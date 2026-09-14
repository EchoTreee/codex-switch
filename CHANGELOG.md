# Changelog

## Unreleased

### Added

- Optional herdr companion recommendations in both READMEs and parallel guides, including pane setup and the distinction between detaching and restarting an agent.
- Six core benefits at the top of both READMEs, plus bilingual parallel-workflow guides covering worktrees, startup identities, token snapshots, and safe timing for recovery.
- Separate official-account and official + relay workflow guides in both READMEs, with a comparison of authentication versus provider changes, shared history, bidirectional resume examples, and version-dependent provider writeback notes.
- Full Chinese README, shared visual header, and a focused usage guide.
- Contribution and security guidance, roadmap, and issue/PR templates.
- Isolated smoke tests and a Linux/macOS GitHub Actions workflow.
- LF checkout rules for shell scripts and repository text files.

### Corrected

- Braced variables next to Chinese punctuation in CLI messages so macOS Bash does not consume part of a UTF-8 character as a variable name and abort. The existing Linux/macOS smoke suite covers these command paths.
- Distinguished read-only session lookup from authenticated resume; documented shared-home parallel use as author-reported experience rather than guaranteed isolation or a fixed token lifetime.
- Installation instructions now use a clone, as required by the existing installer.
- Device-code examples put `--device-auth` before the profile name.
- Clarified shared-home concurrency, snapshot behavior, credential storage, and session compatibility limits.

Account switching and installer logic are unchanged; the CLI message fix restores command execution on affected macOS Bash versions.
