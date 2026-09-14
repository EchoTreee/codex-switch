# Usage guide

[English README](../README.md) · [中文首页](../README.zh-CN.md)

## Profiles and switching

A profile is a snapshot of `auth.json` and `config.toml`. `save` needs both files and overwrites an existing profile with the same name. Use simple, trusted names without slashes or `..`; the current script does not validate names.

When switching to a different profile, `use`:

1. Copies current authentication and configuration back to the profile recorded in the `current` marker, if that profile exists.
2. Copies current files to `previous.auth.json` and `previous.config.toml` in the profile store when the source files exist.
3. Restores the requested profile and updates the marker.
4. Calls `codex login status` if Codex is available.

That first step preserves updated local credentials, but it also means you must **save immediately after an external login or provider change** before switching away. The marker records a name; it does not detect which account you just logged into. Do not use `codex logout` as a switching step: this tool only needs file snapshots and restore operations.

`previous.*` is a single rolling snapshot, not a history. Missing current files can leave an older matching backup file in place. Inspect the pair before recovery. `delete` removes the saved profile and its active marker when applicable; it does not log out, revoke credentials, or remove the live Codex files.

## Custom providers

Configure and verify your provider in Codex first, then save the working setup:

```bash
codex-switch save relay-dev
codex-switch use work
codex-switch use relay-dev
```

Use the authentication method supported by that provider and your Codex version. This script copies files; it does not convert OAuth credentials into API keys, configure a provider for you, or manage provider billing.

If your provider reads its key from an environment variable, set that variable separately in the terminal where you launch Codex. Environment variables and operating-system keychain entries are not saved with profiles. Do not paste keys into issues, screenshots, or example commands.

## Session search and resume

```bash
codex-switch sessions
codex-switch resume "parser regression"
```

`sessions` reads CLI and exec sessions from the expected local database. `resume` searches CLI session titles using SQLite `LIKE`; `%` and `_` act as wildcards. Zero or multiple matches stop with an error instead of choosing a session automatically. Use a more specific keyword if necessary.

With a single match, the script runs `codex resume <id>` with `-c` overrides from the active configuration. A provider override is always supplied; a model override is supplied if the script finds a model. The database lookup itself is read-only. Once launched, Codex may update session state.

Resuming with a different provider requires that provider to support the selected model and conversation. It is not a universal migration guarantee. Session files stay in the selected Codex home; this project does not synchronize separate homes or machines.

## Parallel use

Changing one shared home is not isolation. Running Codex processes may read or write the same files. Stop them before using `use` or `relogin` against that home.

For separate concurrent setups, launch each terminal with its own home **and its own profile store**. For example, in terminal A:

```bash
export CODEX_HOME="$HOME/.codex-work"
export CODEX_SWITCH_DIR="$HOME/.config/codex-switch-work"
# Configure and log in to Codex in this home first.
codex login
# Once auth.json and config.toml exist:
codex-switch save work
codex
```

In terminal B, use different directories such as `~/.codex-personal` and `~/.config/codex-switch-personal`, configure that home, and sign in to the other account. Keep these exports set for both the switcher and Codex. Isolating only the Codex home while sharing a profile store would still share the active marker and backups.

Each home has its own local session history. This project does not set up these homes or copy session databases for you.

Git worktrees address a separate concern: keeping code edits apart. In your code project's checkout, you can create another worktree with `git worktree add ../project-b -b feature/b`. It does not isolate authentication.

## Re-login and recovery

```bash
codex-switch relogin work
# Or use device-code login:
codex-switch relogin --device-auth work
```

The device flag must precede the name. Pick the intended account in the login flow. If the profile already contains a saved configuration, `relogin` restores it after login; otherwise it saves the current configuration when available.

If a switch selected the wrong existing profile, `use <correct-name>` selects another saved profile. For manual recovery, close running sessions and inspect the `previous.*` snapshot locally before copying it back. It may have already been replaced by another switch; there is no built-in rollback command.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `codex-switch: command not found` | Add the actual install destination to `PATH`, then reopen the shell or export the path. |
| Missing `auth.json` / `config.toml` | Verify `CODEX_HOME`, complete Codex configuration, and confirm file-based credentials are present. |
| Saved profile has the wrong account | After an external login, use `save <name>` before switching; check which account was selected. |
| Expired or rejected credentials | Use `relogin <name>` and verify the intended account. Saved files do not guarantee ongoing login validity. |
| Missing session database / SQL error | Check that this home has sessions and that its schema matches the version the script expects. |
| Several session matches | Use a more specific title keyword. |
| Provider/model error on resume | Verify that the active provider supports the selected model and conversation. |
| macOS shows `?` for file time | `status` uses GNU `stat -c` with a fallback; BSD `stat` may not show the timestamp. |

For a bug report, include OS, Bash/Python/Codex versions, repository commit, the command, and redacted output. Never attach authentication files or session databases.

## Compatibility

The original README reported use with Codex CLI `0.153.4`; that is an author-reported data point, not an independently verified compatibility range. No exhaustive live-version or platform matrix is claimed.

The automated smoke tests use fabricated local files, a small SQLite fixture, and a fake Codex command. They exercise installation, profile switching/backups, device-login argument forwarding, and session selection. They do not contact OpenAI, prove live login behavior, or establish cross-provider compatibility.

Configuration parsing currently expects simple double-quoted assignments at the start of a line. It is not a complete TOML parser. Profile writes are neither atomic nor locked, credential permissions are not explicitly hardened, and profile names are not validated. These are tracked in the [roadmap](../ROADMAP.md).
