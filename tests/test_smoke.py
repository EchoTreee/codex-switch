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
import time
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
        self.login_homes = self.base / "codex-login-homes.txt"
        self.env = os.environ.copy()
        self.env.update(
            CODEX_HOME=self.home.as_posix(),
            CODEX_SWITCH_DIR=self.store.as_posix(),
            CODEX_SWITCH_HOMES_DIR=(self.base / "homes").as_posix(),
            CODEX_TEST_CALLS=self.calls.as_posix(),
            CODEX_TEST_HOMES=self.login_homes.as_posix(),
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
            "    p.write_text(json.dumps({'auth_mode': 'chatgpt', 'tokens': {'account_id': 'fixture-relogin'}}))\n"
            "    if 'CODEX_TEST_HOMES' in os.environ:\n"
            "        with open(os.environ['CODEX_TEST_HOMES'], 'a', encoding='utf-8') as f:\n"
            "            f.write(os.environ.get('CODEX_HOME', '') + '\\n')\n",
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
        current_auth, current_config = self.seed(provider="temporary-provider", account="fixture-current")
        self.run_cli("relogin", "--device-auth", "work")
        self.assertEqual(json.loads(self.calls.read_text()), ["login", "--device-auth"])
        # 共享 home 的 auth/config 原样保留：登录发生在临时 home 里，不碰共享 home
        self.assertEqual((self.home / "auth.json").read_bytes(), current_auth)
        self.assertEqual((self.home / "config.toml").read_bytes(), current_config)
        # profile 保存登录结果，并保留原 provider 配置
        auth = json.loads((self.store / "profiles/work/auth.json").read_text())
        self.assertEqual(auth["tokens"]["account_id"], "fixture-relogin")
        self.assertEqual((self.store / "profiles/work/config.toml").read_bytes(), config)

    def test_relogin_runs_login_outside_shared_home(self):
        # 回归：codex login 会先吊销当前 CODEX_HOME 里的 refresh_token。
        # 若在共享 home 里登录，上一次 relogin 留下的会话（可能正被 run 的
        # 并发槽位使用）会被当作旧会话吊销，导致正在运行的槽位全部 401。
        self.seed()
        self.run_cli("relogin", "--device-auth", "work")
        lines = self.login_homes.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        self.assertNotIn(self.home.as_posix(), lines[0])
        self.assertIn("/codex-switch-login.", lines[0])
        # 临时 home 用后即焚，不留残余
        self.assertFalse(os.path.exists(lines[0]))

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

    def test_run_isolates_auth_and_shares_sessions(self):
        self.seed()
        self.run_cli("save", "work")
        # 共享 CODEX_HOME 里放一个 sessions 目录，验证 run 会软链共享它
        sessions = self.home / "sessions"
        sessions.mkdir()
        (sessions / "shared.txt").write_text("shared", encoding="utf-8")
        # 放一个 app-server-control（含 socket），验证 run 不会软链它（避免 TUI 连全局 app-server 串号）
        app_ctl = self.home / "app-server-control"
        app_ctl.mkdir()
        (app_ctl / "app-server-control.sock").write_text("", encoding="utf-8")

        self.run_cli("run", "work")

        homes = self.base / "homes" / "work"
        # auth.json / config.toml 是真实文件（每账号独立，不软链）
        self.assertTrue((homes / "auth.json").is_file() and not (homes / "auth.json").is_symlink())
        self.assertTrue((homes / "config.toml").is_file() and not (homes / "config.toml").is_symlink())
        # sessions 是软链，指向共享 CODEX_HOME，历史互通
        self.assertTrue((homes / "sessions").is_symlink())
        self.assertEqual((homes / "sessions" / "shared.txt").read_text(encoding="utf-8"), "shared")
        # app-server-control 不软链（避免串号）
        self.assertFalse((homes / "app-server-control").exists())
        # codex 被调用
        self.assertEqual(json.loads(self.calls.read_text()), [])

    def test_sync_writes_live_auth_back_into_profile(self):
        self.seed()
        self.run_cli("save", "work")
        homes = self.base / "homes" / "work"
        homes.mkdir(parents=True)
        live_auth = '{"auth_mode": "chatgpt", "tokens": {"account_id": "fixture-rotated"}}'
        (homes / "auth.json").write_text(live_auth, encoding="utf-8")
        self.run_cli("sync", "work")
        self.assertEqual(
            (self.store / "profiles/work/auth.json").read_text(encoding="utf-8"),
            live_auth,
        )
        self.run_cli("sync", "missing", success=False)

    def test_run_reuses_newer_auth_from_isolated_home(self):
        self.seed()
        self.run_cli("save", "work")
        homes = self.base / "homes" / "work"
        homes.mkdir(parents=True)
        live_auth = '{"auth_mode": "chatgpt", "tokens": {"account_id": "fixture-rotated"}}'
        (homes / "auth.json").write_text(live_auth, encoding="utf-8")
        future = time.time() + 60
        os.utime(homes / "auth.json", (future, future))
        self.run_cli("run", "work")
        # 独立 home 里较新的登录态被沿用，并回写 profile
        self.assertEqual((homes / "auth.json").read_text(encoding="utf-8"), live_auth)
        self.assertEqual(
            (self.store / "profiles/work/auth.json").read_text(encoding="utf-8"),
            live_auth,
        )

    def test_run_removes_stray_app_server_symlinks_from_home(self):
        self.seed()
        self.run_cli("save", "work")
        homes = self.base / "homes" / "work"
        homes.mkdir(parents=True)
        stray_daemon = homes / "app-server-daemon"
        stray_daemon.symlink_to(self.home / "app-server-daemon")
        stray_tmp = homes / ".tmp"
        stray_tmp.symlink_to(self.home / ".tmp")
        self.run_cli("run", "work")
        # 旧版本遗留的软链被清掉（悬空软链也算软链，用 is_symlink 判断）
        self.assertFalse(stray_daemon.is_symlink())
        self.assertFalse(stray_tmp.is_symlink())

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


    def _spawn_fake_daemon(self, homes_dir, name, label="pid-update-loop"):
        """Spawn a live process whose /proc cmdline matches the daemon patterns."""
        sleep_bin = shutil.which("sleep")
        self.assertIsNotNone(sleep_bin)
        link = self.base / label
        if not link.exists():
            link.symlink_to(sleep_bin)
        home = homes_dir / name
        home.mkdir(parents=True, exist_ok=True)
        proc = subprocess.Popen(
            [str(link), "60"],
            env={**self.env, "CODEX_HOME": home.as_posix()},
            cwd=self.base,
        )
        self.addCleanup(self._kill_proc, proc)
        return proc, home

    @staticmethod
    def _kill_proc(proc):
        if proc.poll() is None:
            proc.kill()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass

    @unittest.skipUnless(os.path.isdir("/proc/self"), "requires /proc to inspect daemon processes")
    def test_daemon_restart_noop_without_daemon(self):
        homes = self.base / "homes" / "work"
        homes.mkdir(parents=True)
        (homes / "auth.json").write_text("{}", encoding="utf-8")
        out = self.run_cli("daemon-restart", "work")
        self.assertIn("无需重启", out)

    @unittest.skipUnless(os.path.isdir("/proc/self"), "requires /proc to inspect daemon processes")
    def test_daemon_restart_stops_only_its_own_home_daemons(self):
        self.seed()
        self.run_cli("save", "work")
        homes = self.base / "homes"
        work_proc, _ = self._spawn_fake_daemon(homes, "work")
        other_proc, _ = self._spawn_fake_daemon(homes, "other", label="pid-update-loop-other")
        out = self.run_cli("daemon-restart", "work")
        self.assertIn("已全部停掉", out)
        work_proc.wait(timeout=10)  # 目标 home 的进程被停掉
        self.assertIsNone(other_proc.poll())  # 其它 home 的进程不受影响

    @unittest.skipUnless(os.path.isdir("/proc/self"), "requires /proc to inspect daemon processes")
    def test_relogin_warns_about_running_home_daemon(self):
        # 回归：relogin 只更新磁盘文件；独立 home 里的旧 daemon 缓存旧 token 链，
        # 不提醒的话用户 relogin 成功后 run 仍会弹登录页。
        self.seed()
        self.run_cli("save", "work")
        proc, _ = self._spawn_fake_daemon(self.base / "homes", "work")
        out = self.run_cli("relogin", "--device-auth", "work")
        self.assertIn("daemon-restart work", out)
        self.assertIsNone(proc.poll())  # relogin 只提醒，不动正在跑的进程

    @unittest.skipUnless(os.path.isdir("/proc/self"), "requires /proc to inspect daemon processes")
    def test_run_warns_when_daemon_predates_fresh_auth(self):
        self.seed()
        self.run_cli("save", "work")
        self._spawn_fake_daemon(self.base / "homes", "work")
        time.sleep(1.2)  # run 复制进去的 auth.json 比 daemon 启动时间新 → 旧 daemon 读不到
        out = self.run_cli("run", "work")
        self.assertIn("daemon-restart work", out)

    @unittest.skipUnless(os.path.isdir("/proc/self"), "requires /proc to inspect daemon processes")
    def test_run_stays_silent_when_daemon_started_after_auth(self):
        # 反例：daemon 在 auth.json 之后启动，读到的就是最新登录态，不应警告
        self.seed()
        self.run_cli("save", "work")
        homes = self.base / "homes" / "work"
        homes.mkdir(parents=True)
        now = time.time()
        kept = '{"auth_mode": "chatgpt", "tokens": {"account_id": "fixture-kept"}}'
        (homes / "auth.json").write_text(kept, encoding="utf-8")
        os.utime(homes / "auth.json", (now, now))
        os.utime(self.store / "profiles/work/auth.json", (now - 100, now - 100))
        time.sleep(1.2)
        self._spawn_fake_daemon(self.base / "homes", "work")
        out = self.run_cli("run", "work")
        self.assertNotIn("daemon-restart", out)
        self.assertEqual((homes / "auth.json").read_text(encoding="utf-8"), kept)


if __name__ == "__main__":
    unittest.main()
