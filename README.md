<p align="center">
  <img src="docs/assets/banner.svg" alt="codex-switch — Switch profiles. Keep your workflow." width="100%">
</p>

# codex-switch

**Multiple Codex accounts. Shared local conversations. Parallel worktrees.**

[![MIT license](https://img.shields.io/badge/license-MIT-60d5b0)](LICENSE)
[![Bash + Python](https://img.shields.io/badge/built_with-Bash_%2B_Python-9bb8ff)](#requirements)
[![Checks](https://github.com/EchoTreee/codex-switch/actions/workflows/checks.yml/badge.svg)](https://github.com/EchoTreee/codex-switch/actions/workflows/checks.yml)

**English** · [简体中文](README.zh-CN.md)

[Parallel workflow](#parallel-work-launch-finish-recover) · [Official accounts](#multiple-official-accounts) · [Official + relay](#official-accounts-and-relays) · [Install](#install) · [Commands](#commands) · [Contribute](CONTRIBUTING.md)

Moving between a personal account, a work account, and a custom provider? Give each setup a name. `codex-switch` saves the local authentication and configuration files together, then restores the pair you choose.

**Keep working on the same local conversation across accounts or providers.** With the same `CODEX_HOME`, the history is already shared; there is no second copy to synchronize. Choose the [official-account workflow](#multiple-official-accounts) or the [official + relay workflow](#official-accounts-and-relays).

```bash
codex-switch save work       # save your current login + configuration
codex-switch use personal    # restore a previously saved profile
codex-switch resume "parser" # resume a matching local session
```

## Six reasons to use codex-switch

1. **Multiple accounts on one machine.** Launch a Codex CLI in each terminal with a selected ChatGPT account. The author has used this for concurrent tasks; a shared home still has authentication races. Follow the [parallel workflow](#parallel-work-launch-finish-recover).
2. **One local conversation history.** With the same `CODEX_HOME`, accounts and compatible providers can continue the same conversation, including official ↔ relay transitions. No duplicate history store or synchronization step is needed.
3. **Switch files, without logging out.** Restore `auth.json` + `config.toml` instead of manually repeating login. The switcher never calls `codex logout` or a token-revocation endpoint. This does not prevent credentials from expiring or being rotated elsewhere.
4. **Official accounts and custom providers together.** Save working API-key provider configurations, including relay `base_url` settings, alongside official profiles. Keys supplied through environment variables must be managed separately.
5. **Separate worktrees for parallel code changes.** Give each agent its own branch and Git worktree so edits stay in separate working directories. Worktrees isolate code files, not authentication or external services.
6. **One script, minimal setup.** Bash + Python 3's standard library and standard Unix tools; no extra Python packages, build step, or background service. Install to `~/.local/bin` and use it.

## Choose your workflow

| Question | Multiple official accounts | Official account + relay |
| --- | --- | --- |
| What changes? | Login identity; configuration can also differ. | Authentication, provider endpoint, and possibly model. |
| Provider ID | Normally `openai` for both accounts. | For example, `openai` ↔ `zipwuu`. |
| What happens to local history? | Shared when both use the same `CODEX_HOME`. | Shared under that same condition. |
| How do I resume? | Switch profile, then use native `codex resume` for an `openai` session; the wrapper also works. | Find with `codex-switch sessions`, then use `codex-switch resume` to pass the active provider/model. |
| Why the different steps? | Changing the account alone does not cross a provider boundary. | Finding the session and choosing its execution provider are separate concerns. |

One Bash script with Python's standard library. No build step, background service, or separate account with this project.

> **Scope:** ordinary account changes and recovery should happen after stopping other processes using that home. The shared-home parallel pattern below is author-reported experience, with known races; use [separate homes and stores](docs/usage.md#parallel-use) when you need separate authentication files.

## Parallel work: launch, finish, recover

**The author's working pattern is to launch the planned accounts, let each complete its task, then recover credentials after shutdown. Frequent seamless switching during shared-home parallel runs remains unreliable.**

1. **Prepare first.** Save valid profiles while no other process is writing the shared home. Create one Git worktree and branch per agent.
2. **Launch the planned terminals in sequence.** In each worktree, run `codex-switch use <profile>` immediately before `codex`. Complete startup before moving to the next terminal. This reduces unintended startup identities but does not eliminate refresh races.
3. **Let running tasks finish.** Avoid manual `use`, `save`, `relogin`, or edits to shared authentication files during the run. Codex itself may still refresh and write credentials.
4. **Look up history without launching another session.** `codex-switch sessions` only reads the index. `codex-switch resume` starts a new Codex process and still needs the intended account; it is not an authentication-free operation.
5. **Recover after all shared-home processes exit.** Do not assume saved profiles contain the latest usable tokens. If stale or uncertain, run `codex-switch relogin <profile>`, then launch or resume. Elapsed time alone does not determine validity.

Three risks remain: a newly started process can pick up the wrong account; token rotation and another writer can leave a stale or wrong snapshot; `use` can copy that snapshot into the profile named by a stale `current` marker.

See the [full parallel guide](docs/parallel.md) for two-terminal worktree commands, the three failure modes, and recovery. A retained local history and reliable authentication are separate requirements. Avoid resuming the same conversation simultaneously from multiple writers.

## Multiple official accounts

**Use this for two or more official accounts that normally share the `openai` provider.** The main task is switching authentication while keeping your local work available.

### Save each account once

After [installation](#install), start with a working official Codex setup containing both `auth.json` and `config.toml`. Close sessions using that home before changing accounts.

```bash
# Account A is already logged in and configured.
codex-switch save official-work

# Sign in to account B and immediately save its files.
codex login
codex-switch save official-personal
```

Choose the intended account during login. Saving immediately prevents a later switch from copying the new account's files back into the previously active profile.

### Switch accounts and continue

```bash
codex-switch use official-work
codex resume                  # select an existing official-provider session

# Exit the running session before switching accounts.
codex-switch use official-personal
codex resume                  # select that same session
```

For an exact conversation, use `codex resume "your-session-id"` after replacing the ID. Or use `codex-switch sessions` and `codex-switch resume "parser"` to search by title and explicitly apply the active model settings.

### Why native resume is usually enough

The login identity changes, but both accounts normally use `model_provider = "openai"`. An existing `openai` session therefore does not need a different provider just because you changed accounts. The local history remains under the same home; switching accounts does not create a second history store.

If the session was previously resumed through a relay, its saved provider may now be different: use the [mixed-provider workflow](#official-accounts-and-relays). Model access can also differ between official accounts; select an available model when needed. Native picker working-directory filters still apply.

These examples switch accounts sequentially. For the author's shared-home concurrent workflow, see [parallel work](#parallel-work-launch-finish-recover). For separate authentication files, use [separate homes and profile stores](docs/usage.md#parallel-use), which do not automatically share session history.

## Official accounts and relays

**Use this when the provider changes as well as the account.** Keep the same local history, find it without a provider filter, then explicitly choose the provider/model used to continue.

### Save both working configurations

```bash
# Start from a verified official login and configuration.
codex-switch save official

# Configure and verify the relay in Codex, then save it immediately.
codex-switch save relay
```

Before the second `save`, actually configure the relay's provider ID, endpoint, model, and authentication in Codex and verify that it works. The name `relay` does not configure a provider automatically. File snapshots do not switch environment-based API keys; set those separately for the selected provider. See [custom providers](docs/usage.md#custom-providers).

### The history is already shared

When both setups use the same `CODEX_HOME` (default `~/.codex`), they use the same local storage:

- `~/.codex/sessions/` — rollout JSONL conversation records.
- `~/.codex/state_5.sqlite` — the session index used by this script.

The files are not split into separate official-account and relay histories. A session can have provider metadata while its history remains in that same directory. Switching profiles leaves these records in place.

### Why a conversation can seem to disappear

In the author's reported workflow, Codex's `/resume` picker filters by `model_provider`: the `openai` view shows official-provider sessions, while the `zipwuu` view shows that relay's sessions. Without an override, resuming also uses the session's saved provider. A missing picker entry can therefore be a filtered view, rather than lost history. Picker behavior is version-dependent; working-directory filters can also hide sessions.

### Continue in either direction

First save and verify both profiles in the same home. Here, `relay` and `official` are saved profile names; choose a title keyword matching exactly one CLI session.

```bash
codex-switch sessions           # list CLI / exec sessions across providers
codex-switch use relay          # activate the saved relay configuration
codex-switch resume "parser"    # continue with its provider/model

# Exit that Codex session before switching back.
codex-switch use official
codex-switch resume "parser"    # continue the same local conversation
```

The underlying commands look like this; replace the session ID and use models available on each provider. `zipwuu` is an example configured provider ID, not a built-in profile or an endorsement.

```bash
SESSION_ID="your-session-id"

# Via the relay
codex resume "$SESSION_ID" -c 'model_provider="zipwuu"' -c 'model="gpt-5.6-terra"'

# After exiting, via the official provider
codex resume "$SESSION_ID" -c 'model_provider="openai"' -c 'model="gpt-6-astra"'
```

The author reports that successful cross-provider resume writes the selected provider back to the local index, effectively “re-pointing” that session. A later override can point it back while continuing its existing local history. **Codex performs that writeback; `codex-switch` only reads the index and forwards the overrides.** This persistence behavior is not independently verified across Codex versions. See [the detailed mechanism](docs/usage.md#shared-history-and-provider-writeback).

This workflow requires a shared home, a compatible session format, and a provider/model that can resume the conversation. Existing history is retained locally; that does not guarantee every historical token fits the model's context window. Separate homes or machines do not automatically share history.

**Remember: find with `codex-switch sessions`; continue with `codex-switch resume`.**

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
