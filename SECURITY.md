# Security

## Local credential handling

This tool copies local authentication files. Profiles and `previous.*` backups contain unencrypted credentials and may also contain private provider configuration. Keep both the Codex home and profile store accessible only to your own OS account. Do not put them in a public, shared, or automatically synchronized directory.

The current script does not encrypt credentials, explicitly harden file permissions, validate profile names, or lock simultaneous writes. Use simple trusted profile names, keep directories private, and stop processes using the same home before switching. It is intended for your own local account; it is not a security boundary between users or processes.

Deleting a saved profile or uninstalling the command does not revoke credentials. Switching can retain additional credential copies in backups. Environment-based keys and keychain entries are outside the file snapshot mechanism.

## Reporting a vulnerability

If the repository's Security tab offers **Report a vulnerability**, use that private channel. If it is unavailable, open an issue asking the maintainer for a private reporting channel without including exploit details, credentials, or affected private data. Do not include sensitive findings in a public issue or pull request.

Provide a minimal reproduction using fabricated data, the affected commit, and the impact. Never attach `auth.json`, full `config.toml`, profile directories, session databases, or real tokens. Redact account IDs, private endpoints, paths, and conversation titles from screenshots and logs.

Security changes are developed against `main`. There is no promised response time or maintained backport series at this stage.
