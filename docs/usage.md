# Usage guide

[English README](../README.md) · [中文首页](../README.zh-CN.md)

## Choose a workflow

| Scenario | Method | Why |
| --- | --- | --- |
| Multiple official accounts, same `openai` provider | Save each login/config pair, `use` the desired profile, then resume the existing `openai` session. | Authentication changes, but the execution provider need not change. |
| Official account and relay, different provider IDs | Save both working configurations, switch profile, list across providers, and resume with explicit provider/model overrides. | The session's saved provider or picker filter may differ from the provider you want to use now. |

Both workflows share local history only when they use the same Codex home. Account identity, profile name, and provider ID are distinct: a profile called `official-work` may still use provider `openai`, while a profile called `relay` might use provider `zipwuu`.

See the complete [official-account example](../README.md#multiple-official-accounts) / [官方多账号示例](../README.zh-CN.md#官方多账号使用), or the [official + relay example](../README.md#official-accounts-and-relays) / [混合使用示例](../README.zh-CN.md#官方与中转站混合使用). If an otherwise official-account session was last resumed through a relay, use the mixed-provider method to explicitly choose `openai` again.

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

`sessions` reads CLI and exec sessions from the expected local database **without a provider or working-directory filter**. The `*` marker identifies the current provider; it does not exclude other providers. `resume` also searches across providers, but only searches CLI session titles, using SQLite `LIKE`; `%` and `_` act as wildcards. Zero or multiple matches stop with an error instead of choosing a session automatically. Use a more specific keyword if necessary.

With a single match, the script runs `codex resume <id>` with `-c` overrides from the active configuration. A provider override is always supplied; a model override is supplied if the script finds a model. The database lookup itself is read-only. Once launched, Codex may update session state.

`sessions` is only a lookup; `resume` launches a new Codex process that still needs valid authentication for the selected provider. During a shared-home parallel run, a matching conversation ID does not guarantee that process will use the intended account. See [parallel operation and recovery](parallel.md).

Resuming with a different provider requires that provider to support the selected model and conversation. It is not a universal migration guarantee. Session files stay in the selected Codex home; this project does not synchronize separate homes or machines.

## Shared history and provider writeback

Official OpenAI and relay configurations that use the same `CODEX_HOME` already share the same local rollout history (`sessions/`) and session index (`state_5.sqlite` in the format this script expects). Provider metadata is attached to sessions; it does not imply separate directories of history to synchronize. `use` copies authentication and configuration, leaving the session store in place.

In the author's reported workflow, the built-in `/resume` picker filters by provider and resumes with the session's saved provider unless overridden. This can make a conversation appear absent after switching configurations. Picker filters can vary with Codex versions and working directories. `codex-switch sessions` reads the index across providers, and `codex-switch resume` supplies the chosen session ID directly, along with the current provider/model overrides.

The author reports a second effect after successful cross-provider resume: Codex updates the session's provider in the local index. The same session ID can then be resumed in the opposite direction by supplying another override. This is the “re-pointing” behavior described in the [English README](../README.md#official-accounts-and-relays) and [Chinese README](../README.zh-CN.md#官方与中转站混合使用).

Distinguish the verified script behavior from Codex's persistence behavior:

| Layer | Behavior and evidence |
| --- | --- |
| `codex-switch sessions` | Its SQL has a source filter (`cli` / `exec`), but no provider or working-directory filter. |
| `codex-switch resume` | Its SQL searches CLI titles without a provider filter. It opens SQLite in read-only mode, then invokes `codex resume` with configuration overrides. |
| Codex CLI | The [official command reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli#codex-resume) documents resume by ID and global overrides. Local `codex-cli 0.153.4` help also confirms `-c key=value`. |
| Provider writeback and picker filtering | Reported by the author for their workflow; the official reference does not promise these database details across versions. No live cross-provider validation was performed for this documentation update. |

The switcher does not edit the provider column directly or copy a conversation to the relay. When you continue through a provider, Codex sends the conversation context needed for that request to the selected service. Choose a provider appropriate for the conversation's contents. Continuing an existing history also does not bypass model context limits or compaction behavior.

To verify provider writeback on your Codex version, use a disposable conversation in a dedicated test home: record its ID in `codex-switch sessions`, resume that ID with the other provider, exit, and check the provider shown for the same ID. Then repeat in the opposite direction. Both providers must already be configured, and any live requests use their normal account access and billing. The existing mock tests establish argument forwarding, not a live provider round trip or database writeback by Codex.

## Parallel use

There are two distinct options. The author reports using a shared home by launching each selected account in sequence, letting the tasks finish, and recovering credentials afterward; this retains shared local history but has authentication races. See the [parallel guide](parallel.md) / [中文指南](parallel.zh-CN.md) for the workflow and risks. Routine switching, re-login, and recovery should happen after stopping other processes using that home.

The alternative below uses separate homes and stores to separate authentication files. It does not automatically share conversation history. Neither option makes worktrees an authentication boundary.

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
