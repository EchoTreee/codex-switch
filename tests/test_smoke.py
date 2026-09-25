"""Exercise the public CLI with disposable files, never real Codex credentials."""

import json
from contextlib import closing
import os
from pathlib import Path
import shlex
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASH = os.environ.get("CODEX_SWITCH_TEST_BASH") or shutil.which("bash")


@unittest.skipUnless(BASH, "Bash is required")
class CliSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(
            prefix="codex-switch-test-", dir=os.environ.get("CODEX_SWITCH_TEST_TMPDIR")
        )
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / "codex home"
        self.store = self.base / "profile store"
        self.bin = self.base / "bin"
        self.home.mkdir()
        self.bin.mkdir()
        self.calls = self.base / "codex-calls.txt"
        self.env = os.environ.copy()
        self.env.update(
            CODEX_HOME=self.home.as_posix(),
            CODEX_SWITCH_DIR=self.store.as_posix(),
            CODEX_TEST_CALLS=self.calls.as_posix(),
            PYTHONIOENCODING="utf-8",
            PATH=str(self.bin) + os.pathsep + self.env.get("PATH", ""),
        )
        # Make python3 resolve to this interpreter, including on Git Bash hosts.
        python = shlex.quote(Path(sys.executable).as_posix())
        self.wrapper("python3", f'exec {python} "$@"\n')
        stub = self.base / "fake_codex.py"
        stub.write_text(
            "import json, os, pathlib, sys\n"
            "pathlib.Path(os.environ['CODEX_TEST_CALLS']).write_text(json.dumps(sys.argv[1:]))\n"
            "if sys.argv[1:] in (['login'], ['login', '--device-auth']):\n"
            "    p = pathlib.Path(os.environ['CODEX_HOME']) / 'auth.json'\n"
            "    p.write_text(json.dumps({'auth_mode': 'chatgpt', 'tokens': {'account_id': 'fixture-relogin'}}))\n",
            encoding="utf-8",
        )
        self.wrapper("codex", f'exec {python} {shlex.quote(stub.as_posix())} "$@"\n')

    def wrapper(self, name, body):
        path = self.bin / name
        path.write_text("#!/usr/bin/env bash\n" + body, encoding="utf-8", newline="\n")
        path.chmod(0o755)

    def run_cli(self, *args, success=True):
        result = subprocess.run(
            [BASH, str(ROOT / "codex-switch"), *args],
            env=self.env, cwd=self.base, capture_output=True,
            text=True, encoding="utf-8", timeout=30,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def seed(self, account="fixture-work", provider="openai", model="fixture-model"):
        auth = json.dumps({"auth_mode": "chatgpt", "tokens": {"account_id": account}})
        config = f'model_provider = "{provider}"\nmodel = "{model}"\n'
        (self.home / "auth.json").write_text(auth, encoding="utf-8")
        (self.home / "config.toml").write_text(config, encoding="utf-8", newline="\n")
        return auth.encode(), config.encode()

    def seed_sessions(self):
        with closing(sqlite3.connect(self.home / "state_5.sqlite")) as db:
            db.execute("CREATE TABLE threads (id TEXT, title TEXT, model_provider TEXT, updated_at INTEGER, source TEXT)")
            db.executemany("INSERT INTO threads VALUES (?, ?, ?, ?, ?)", [
                ("fixture-cli-1", "Parser regression", "old-provider", 1700000000, "cli"),
                ("fixture-cli-2", "Parser cleanup", "openai", 1700000001, "cli"),
                ("fixture-exec", "Only exec task", "openai", 1700000002, "exec"),
            ])
            db.commit()

    def test_help_and_invalid_command(self):
        self.assertIn("codex-switch", self.run_cli("help"))
        self.run_cli("not-a-command", success=False)
        self.assertFalse(self.store.exists())

    def test_save_requires_both_files(self):
        self.run_cli("save", "work", success=False)
        self.seed()
        (self.home / "config.toml").unlink()
        self.run_cli("save", "work", success=False)
        self.assertFalse((self.store / "profiles" / "work").exists())

    def test_switch_restores_pair_refreshes_previous_profile_and_preserves_sessions(self):
        work_auth, work_config = self.seed()
        self.run_cli("save", "work")
        self.seed("fixture-personal")
        self.run_cli("save", "personal")
        personal_auth, personal_config = self.seed("fixture-personal-refreshed", "other-provider")
        self.seed_sessions()
        database_before = (self.home / "state_5.sqlite").read_bytes()
        sessions = self.home / "sessions"
        sessions.mkdir()
        sentinel = sessions / "fixture.txt"
        sentinel.write_text("keep this local session", encoding="utf-8")

        self.run_cli("use", "work")
        self.assertEqual((self.home / "auth.json").read_bytes(), work_auth)
        self.assertEqual((self.home / "config.toml").read_bytes(), work_config)
        self.assertEqual((self.store / "previous.auth.json").read_bytes(), personal_auth)
        self.assertEqual((self.store / "previous.config.toml").read_bytes(), personal_config)
        self.assertEqual((self.store / "profiles/personal/auth.json").read_bytes(), personal_auth)
        self.assertEqual((self.store / "profiles/personal/config.toml").read_bytes(), personal_config)
        self.assertEqual((self.home / "state_5.sqlite").read_bytes(), database_before)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep this local session")
        self.assertEqual((self.store / "current").read_text().strip(), "work")
        self.assertRegex(self.run_cli("list"), r"\*\s+work\s+provider=openai")
        self.assertIn("fixture-work", self.run_cli("status"))

    def test_unknown_profile_does_not_change_active_files(self):
        auth, config = self.seed()
        self.run_cli("use", "missing", success=False)
        self.assertEqual((self.home / "auth.json").read_bytes(), auth)
        self.assertEqual((self.home / "config.toml").read_bytes(), config)

    def test_delete_keeps_live_authentication(self):
        auth, config = self.seed()
        self.run_cli("save", "work")
        self.run_cli("delete", "work")
        self.assertFalse((self.store / "profiles/work").exists())
        self.assertFalse((self.store / "current").exists())
        self.assertEqual((self.home / "auth.json").read_bytes(), auth)
        self.assertEqual((self.home / "config.toml").read_bytes(), config)

    def test_device_login_preserves_saved_provider_config(self):
        _, config = self.seed(provider="saved-provider")
        self.run_cli("save", "work")
        self.seed(provider="temporary-provider")
        self.run_cli("relogin", "--device-auth", "work")
        self.assertEqual(json.loads(self.calls.read_text()), ["login", "--device-auth"])
        self.assertEqual((self.home / "config.toml").read_bytes(), config)
        auth = json.loads((self.store / "profiles/work/auth.json").read_text())
        self.assertEqual(auth["tokens"]["account_id"], "fixture-relogin")

    def test_session_selection_and_provider_model_forwarding(self):
        self.seed(provider="new-provider", model="new-model")
        self.seed_sessions()
        listing = self.run_cli("sessions")
        self.assertIn("fixture-cli-1", listing)
        self.assertIn("fixture-exec", listing)
        self.run_cli("resume", "Parser", success=False)
        self.run_cli("resume", "missing title", success=False)
        self.run_cli("resume", "Only exec", success=False)
        self.assertFalse(self.calls.exists())
        self.run_cli("resume", "regression")
        self.assertEqual(json.loads(self.calls.read_text()), [
            "resume", "fixture-cli-1", "-c", 'model_provider="new-provider"', "-c", 'model="new-model"',
        ])

    def test_resume_by_session_id(self):
        self.seed(provider="new-provider", model="new-model")
        with closing(sqlite3.connect(self.home / "state_5.sqlite")) as db:
            db.execute(
                "CREATE TABLE threads "
                "(id TEXT, title TEXT, model_provider TEXT, updated_at INTEGER, source TEXT)"
            )
            db.executemany("INSERT INTO threads VALUES (?, ?, ?, ?, ?)", [
                ("01a07ed8-18ce-7a02-9f06-e00bf007b95d", "Main experiment", "openai", 1700000000, "cli"),
                ("01a0aaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "Other experiment", "openai", 1700000001, "cli"),
            ])
            db.commit()
        # 完整 ID 唯一命中
        self.run_cli("resume", "01a07ed8-18ce-7a02-9f06-e00bf007b95d")
        self.assertEqual(json.loads(self.calls.read_text()), [
            "resume", "01a07ed8-18ce-7a02-9f06-e00bf007b95d",
            "-c", 'model_provider="new-provider"', "-c", 'model="new-model"',
        ])
        # ID 前缀唯一命中
        self.run_cli("resume", "01a0aaaa")
        self.assertEqual(json.loads(self.calls.read_text()), [
            "resume", "01a0aaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "-c", 'model_provider="new-provider"', "-c", 'model="new-model"',
        ])

    def test_resume_multiline_title_counts_once(self):
        self.seed(provider="new-provider", model="new-model")
        with closing(sqlite3.connect(self.home / "state_5.sqlite")) as db:
            db.execute(
                "CREATE TABLE threads "
                "(id TEXT, title TEXT, model_provider TEXT, updated_at INTEGER, source TEXT)"
            )
            db.executemany("INSERT INTO threads VALUES (?, ?, ?, ?, ?)", [
                ("fixture-multi", "install codex\nstep two\nstep three", "openai", 1700000000, "cli"),
            ])
            db.commit()
        # 标题含换行时，仍应作为「一条」会话命中，而不是被数成多行
        self.run_cli("resume", "install codex")
        self.assertEqual(json.loads(self.calls.read_text()), [
            "resume", "fixture-multi",
            "-c", 'model_provider="new-provider"', "-c", 'model="new-model"',
        ])

    def test_sessions_and_resume_include_vscode(self):
        self.seed(provider="new-provider", model="new-model")
        with closing(sqlite3.connect(self.home / "state_5.sqlite")) as db:
            db.execute(
                "CREATE TABLE threads "
                "(id TEXT, title TEXT, model_provider TEXT, updated_at INTEGER, source TEXT)"
            )
            db.executemany("INSERT INTO threads VALUES (?, ?, ?, ?, ?)", [
                ("fixture-vscode", "Editor session", "openai", 1700000000, "vscode"),
            ])
            db.commit()
        # vscode 会话应出现在 sessions 列表里
        self.assertIn("fixture-vscode", self.run_cli("sessions"))
        # 也能按标题关键词恢复
        self.run_cli("resume", "Editor")
        self.assertEqual(json.loads(self.calls.read_text()), [
            "resume", "fixture-vscode",
            "-c", 'model_provider="new-provider"', "-c", 'model="new-model"',
        ])

    def test_installer_from_another_directory_and_destination_with_spaces(self):
        destination = self.base / "custom bin"
        result = subprocess.run(
            [BASH, str(ROOT / "install.sh"), destination.as_posix()],
            env=self.env, cwd=self.base, capture_output=True,
            text=True, encoding="utf-8", timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        installed = destination / "codex-switch"
        self.assertEqual(installed.read_bytes(), (ROOT / "codex-switch").read_bytes())
        help_result = subprocess.run(
            [BASH, installed.as_posix(), "help"], env=self.env,
            capture_output=True, timeout=30,
        )
        self.assertEqual(help_result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
