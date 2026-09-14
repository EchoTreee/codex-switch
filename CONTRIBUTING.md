# Contributing

Thanks for helping make account switching easier to understand and more reliable. Issues and pull requests in English or Chinese are welcome.

## Useful first contributions

- Report an installation problem with your OS and shell versions.
- Improve an example that was confusing on your first run.
- Keep the English and Chinese READMEs aligned.
- Add a regression test for a reproducible profile or session bug.

For larger changes, open an issue describing the workflow and proposed behavior first. The [roadmap](ROADMAP.md) lists candidate areas, not assigned work or release promises.

## Report a bug

Use the [issue templates](https://github.com/EchoTreee/codex-switch/issues/new/choose). Include the repository commit, Codex version, OS, command, expected result, and actual result. Use fabricated account IDs and redacted output. For credential exposure or other sensitive findings, follow [SECURITY.md](SECURITY.md).

## Run checks

From a clone in a Unix-like Bash environment with Python 3:

```bash
bash -n codex-switch
bash -n install.sh
python3 -m unittest discover -s tests -v
```

The tests use temporary Codex/profile directories and a fake Codex command. They never require real login credentials or a live API. Do not run exploratory account tests against your real default profile store. For manual tests, set `CODEX_HOME` and `CODEX_SWITCH_DIR` to dedicated test directories and use fabricated data.

## Pull requests

Keep each pull request focused on a specific problem. Describe the behavior before and after, include relevant checks, and update both READMEs when the user-facing workflow changes. Keep shell files in LF format and preserve executable permissions on `codex-switch` and `install.sh`.

Avoid new runtime dependencies unless the benefit is clear. Never add real authentication files, API keys, configuration dumps, account IDs, or session exports. Contributions are distributed under the repository's [MIT license](LICENSE).
