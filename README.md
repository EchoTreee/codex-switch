<p align="center">
  <img src="docs/assets/banner.svg" alt="codex-switch — Switch profiles. Keep your workflow." width="100%">
</p>

# codex-switch

**Save and switch account and provider profiles for OpenAI Codex CLI.**

[![MIT license](https://img.shields.io/badge/license-MIT-60d5b0)](LICENSE)
[![Bash + Python](https://img.shields.io/badge/built_with-Bash_%2B_Python-9bb8ff)](#requirements)
[![Checks](https://github.com/EchoTreee/codex-switch/actions/workflows/checks.yml/badge.svg)](https://github.com/EchoTreee/codex-switch/actions/workflows/checks.yml)

**English** · [简体中文](README.zh-CN.md)

[Install](#install) · [Quick start](#quick-start) · [Commands](#commands) · [Usage guide](docs/usage.md) · [Contribute](CONTRIBUTING.md)

Moving between a personal account, a work account, and a custom provider? Give each setup a name. `codex-switch` saves the local authentication and configuration files together, then restores the pair you choose.

```bash
codex-switch save work       # save your current login + configuration
codex-switch use personal    # restore a previously saved profile
codex-switch resume "parser" # resume a matching local session
```

## Why codex-switch?

| Your workflow | What it helps with |
| --- | --- |
| Several accounts | Switch named profiles without manually copying login files. |
| Several providers | Restore authentication and `config.toml` together. |
| An unfinished task | Search local session titles and resume with the active provider/model. |
| A switch you want to undo | Keep a `previous.*` snapshot of the files that were replaced. |

One Bash script with Python's standard library. No build step, background service, or separate account with this project.

> **Scope:** switching affects the selected `CODEX_HOME`. It does not isolate running Codex processes. Stop sessions using that directory before switching; see [parallel use](docs/usage.md#parallel-use) for separate homes.

## Requirements

- Bash, Python 3, and standard Unix command-line tools.
- [OpenAI Codex CLI](https://github.com/openai/codex), already installed and configured.
- Git for the installation below.
- Both `auth.json` and `config.toml` in your Codex home before the first `save`.

Linux is the primary target. On Windows, use a Linux environment such as WSL; these commands are Bash commands. The included workflow runs smoke tests on Linux and macOS, but mock tests do not establish live Codex compatibility. Terminal messages are currently in Chinese.

`sessions` and `resume` depend on Codex's local `state_5.sqlite` database and `threads` schema. They may need updates when Codex changes its storage format. See [compatibility](docs/usage.md#compatibility).

## Install

```bash
git clone https://github.com/EchoTreee/codex-switch.git
cd codex-switch
bash install.sh
export PATH="$HOME/.local/bin:$PATH"
codex-switch help
```

The installer copies the script to `~/.local/bin`. Keep the `PATH` line in your shell's startup file if that directory is not already on your path. It does not require `sudo`.

<details>
<summary>Custom directory, updates, and uninstall</summary>

```bash
# Install into a directory already on your PATH
bash install.sh /your/bin/directory

# Update from inside this checkout
git pull --ff-only
bash install.sh

# Remove the default installed command
rm "$HOME/.local/bin/codex-switch"
```

Uninstalling the command preserves Codex data and saved profiles. The installer needs the main script beside it; run it from a clone, rather than piping `install.sh` from a URL.

</details>

## Quick start

Start with an existing Codex setup containing both local files. Close Codex sessions that use the same home before changing accounts.

```bash
# Save the account and configuration you already use
codex-switch save work

# Sign in to another account and save it immediately
codex login
codex-switch save personal

# Pick a saved setup before starting Codex
codex-switch use work
codex
```

After an external `codex login` or a manual provider change, run `save <name>` before `use`: switching writes the current files back to the profile recorded as active. Choose the intended account during login and use a distinct name for each setup.

```bash
codex-switch list             # saved profiles; * marks the recorded active one
codex-switch status           # local paths, account ID, and provider
codex-switch sessions         # local CLI / exec sessions
codex-switch resume "parser"  # use a title keyword matching one CLI session
```

See [provider setup, recovery, and troubleshooting](docs/usage.md) for the next steps.

## Commands

| Command | Behavior |
| --- | --- |
| `save <name>` | Save current authentication and configuration; an existing name is overwritten. |
| `use <name>` | Refresh the previously active profile, back up current files, and restore the named profile. |
| `relogin <name>` | Run Codex login, save authentication, and restore that profile's saved configuration if present. |
| `relogin --device-auth <name>` | Use Codex's device-code login flow. The flag comes before the name. |
| `list` | Show saved profiles and the recorded active profile. |
| `status` | Show local file locations and account/provider metadata. |
| `sessions` | List local sessions from the expected SQLite schema. |
| `resume <keyword>` | Resume one matching CLI session with current provider/model overrides. |
| `delete <name>` | Remove the saved profile; leave active Codex files untouched. |
| `help` | Show built-in help. |

Prefix each command with `codex-switch`. Use simple profile names such as `work`, `personal`, or `relay-dev`; names are currently treated as paths, without validation.

## How it works

```text
Saved profiles                         Active Codex home
~/.config/codex-switch/profiles/        ~/.codex/
├── work/                              ├── auth.json
│   ├── auth.json          use work ──► ├── config.toml
│   └── config.toml                     ├── sessions/       (left in place)
└── personal/                          └── state_5.sqlite  (left in place)
    ├── auth.json
    └── config.toml
```

| Variable | Default | Purpose |
| --- | --- | --- |
| `CODEX_HOME` | `~/.codex` | Authentication, configuration, and session location. |
| `CODEX_SWITCH_DIR` | `~/.config/codex-switch` | Saved profiles, active-profile marker, and previous snapshot. |

Saved profiles and backups contain **unencrypted credentials**. Keep them private. Environment-based API keys and OS keychain credentials are not captured by copying these files. The switcher does not add telemetry or cloud synchronization; commands that invoke Codex retain Codex's own behavior. Read the [security notes](SECURITY.md) before sharing logs or screenshots.

## Contribute

Bug reports, compatibility reports, clearer examples, and translations are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md), [open an issue](https://github.com/EchoTreee/codex-switch/issues/new/choose), or review the [roadmap](ROADMAP.md).

If this saves you time, a star helps others discover it. Sharing a reproducible workflow is especially useful.

## License

[MIT](LICENSE) © 2026 EchoTreee. An independent community project, not affiliated with or endorsed by OpenAI.
