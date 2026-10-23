# Changelog

## Unreleased

### Added

- `run <name> [codex args...]` launches Codex in an isolated per-account `CODEX_HOME` (own `auth.json`/`config.toml`, symlinked sessions) so multiple accounts can run concurrently without clobbering each other's tokens.
- `sessions` and `resume` now include VS Code (`source = 'vscode'`) sessions alongside CLI sessions, so sessions created from the VS Code Codex extension are no longer invisible.
- `resume` accepts a session ID or ID prefix (hex/hyphen, 8+ characters) in addition to a title keyword.
- Optional herdr companion recommendations in both READMEs and parallel guides, including pane setup and the distinction between detaching and restarting an agent.
- Six core benefits at the top of both READMEs, plus bilingual parallel-workflow guides covering worktrees, startup identities, token snapshots, and safe timing for recovery.
- Separate official-account and official + relay workflow guides in both READMEs, with a comparison of authentication versus provider changes, shared history, bidirectional resume examples, and version-dependent provider writeback notes.
- Full Chinese README, shared visual header, and a focused usage guide.
- Contribution and security guidance, roadmap, and issue/PR templates.
- Isolated smoke tests and a Linux/macOS GitHub Actions workflow.
- LF checkout rules for shell scripts and repository text files.
- macOS credential-store detection: `save`, `use`, `relogin`, and `status` warn when the login may live in the system Keychain (switching `auth.json` would not change the account), and `status` prints the detected `cli_auth_credentials_store`.

### Corrected

- `status` file time now uses a portable `stat` (GNU `-c` / BSD `-f`), so macOS shows a real timestamp instead of `?`.
- `run` no longer symlinks `app-server-daemon` into the isolated per-account home and clears a stale symlink left by a failed run, so the Codex daemon can create its own state directory instead of failing with `socket directory path exists and is not a directory`.
- Smoke tests no longer require Python 3.10 (`Path.write_text(newline=...)` replaced with `open(newline="\n")`), so they run on macOS's system Python 3.9.
- `resume` and `sessions` now flatten newlines/tabs in session titles before printing, so a single session whose title spans multiple lines is no longer miscounted as multiple matches.
- Braced variables next to Chinese punctuation in CLI messages so macOS Bash does not consume part of a UTF-8 character as a variable name and abort. The existing Linux/macOS smoke suite covers these command paths.
- Distinguished read-only session lookup from authenticated resume; documented shared-home parallel use as author-reported experience rather than guaranteed isolation or a fixed token lifetime.
- Installation instructions now use a clone, as required by the existing installer.
- Device-code examples put `--device-auth` before the profile name.
- Clarified shared-home concurrency, snapshot behavior, credential storage, and session compatibility limits.

Account switching and installer logic are unchanged; the CLI message fix restores command execution on affected macOS Bash versions.
