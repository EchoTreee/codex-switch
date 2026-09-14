# Roadmap

The next useful milestone is a dependable everyday switching workflow. These are proposed priorities, not implemented features or release dates. Feedback on real usage will help set the order.

## Reliability first

- [ ] Validate profile names and enforce containment inside the profile directory.
- [ ] Restrict credential and backup file permissions explicitly.
- [ ] Make file replacement atomic and prevent concurrent switches.
- [ ] Detect missing dependencies and explain unsupported authentication storage.
- [ ] Document and test a live Codex/platform compatibility matrix with redacted evidence.
- [ ] Handle session schema changes and TOML parsing more robustly.

## Easier daily use

- [ ] Add an English terminal-output option.
- [ ] Add shell completions after the command interface stabilizes.
- [ ] Offer a standalone installer with version-pinned downloads and checksums.
- [ ] Explore explicit per-process profiles without a shared active marker.

Describe the task you are trying to complete in an [issue](https://github.com/EchoTreee/codex-switch/issues/new/choose). Concrete examples help prioritize better than feature counts.
