# Changelog

## Unreleased

### Added

- `run <name> [codex args...]` launches Codex in an isolated per-account `CODEX_HOME` (own `auth.json`/`config.toml`, symlinked sessions) so multiple accounts can run concurrently without clobbering each other's tokens.
- `sync <name>` writes the latest authentication from a `run`-created isolated home back into its profile, so tokens rotated by a long-running agent can be reused later without another login.
- `daemon-restart <name>` stops the isolated home's app-server daemon processes (including orphaned `pid-update-loop` holders), so the next `run` starts a fresh daemon that reads the latest `auth.json`. `relogin` and `run` now warn when a daemon for that home is still running with older credentials: a daemon reads `auth.json` only once at startup and keeps the token chain in memory, so a fresh login on disk does not take effect for a running daemon (a `run` right after `relogin` then shows the login page).
- `run` now keeps the isolated home's `auth.json` when it is newer than the profile copy (tokens rotated during the previous run) and writes it back to the profile, so reopening a concurrent slot does not require another login.
- `sessions` and `resume` now include VS Code (`source = 'vscode'`) sessions alongside CLI sessions, so sessions created from the VS Code Codex extension are no longer invisible.
- `resume` accepts a session ID or ID prefix (hex/hyphen, 8+ characters) in addition to a title keyword.
- Optional herdr companion recommendations in both READMEs and parallel guides, including pane setup and the distinction between detaching and restarting an agent.
- Six core benefits at the top of both READMEs, plus bilingual parallel-workflow guides covering worktrees, startup identities, token snapshots, and safe timing for recovery.
- Separate official-account and official + relay workflow guides in both READMEs, with a comparison of authentication versus provider changes, shared history, bidirectional resume examples, and version-dependent provider writeback notes.
- Full Chinese README, shared visual header, and a focused usage guide.
- Contribution and security guidance, roadmap, and issue/PR templates.
- Isolated smoke tests and a Linux/macOS GitHub Actions workflow.
- LF checkout rules for shell scripts and repository text files.

### Corrected

- `relogin` now runs `codex login` inside a scratch `CODEX_HOME` instead of the shared home. `codex login` revokes the current home's refresh token first, so logging in through the shared home invalidated the previous login's session — including a session a concurrent `run` slot was actively using (the slot then fails with `token_revoked` 401s at its next refresh). The shared home's `auth.json`/`config.toml` are now left untouched, and the scratch home is removed afterwards.
- `run` now removes stray `app-server-*` and `.tmp` symlinks left in an isolated home by earlier versions, so homes created before the exclusion fix self-heal instead of failing to start Codex.
- `resume` and `sessions` now flatten newlines/tabs in session titles before printing, so a single session whose title spans multiple lines is no longer miscounted as multiple matches.
- Braced variables next to Chinese punctuation in CLI messages so macOS Bash does not consume part of a UTF-8 character as a variable name and abort. The existing Linux/macOS smoke suite covers these command paths.
- Braced the remaining unbraced variables that sat directly against Chinese punctuation in `sync`/`run`/`daemon-restart` messages (`$src（`, `$home（`, `$dp）`), which still produced invalid UTF-8 on macOS Bash 3.2.
- Distinguished read-only session lookup from authenticated resume; documented shared-home parallel use as author-reported experience rather than guaranteed isolation or a fixed token lifetime.
- Installation instructions now use a clone, as required by the existing installer.
- Device-code examples put `--device-auth` before the profile name.
- Clarified shared-home concurrency, snapshot behavior, credential storage, and session compatibility limits.

Account switching and installer logic are unchanged; the CLI message fix restores command execution on affected macOS Bash versions.
