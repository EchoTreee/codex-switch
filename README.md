# codex-switch

Run multiple [OpenAI Codex CLI](https://github.com/openai/codex) sessions on a single machine — each with a different ChatGPT account — in parallel, while sharing conversation history across them.

> 在同一台服务器上开多个终端，让每个 Codex CLI 使用不同的 ChatGPT 账号同时运行；账号之间共享对话记录，并用独立的 Git worktree 并行开发。

## Why this exists

Codex CLI stores your login in a single `~/.codex/auth.json` and your provider config in `~/.codex/config.toml` — which normally means **one account per machine**. `codex-switch` turns `~/.codex` into a **profile manager**, so you can:

- **Run several accounts at once.** Open multiple terminals; each one runs `codex` against a different account (or a relay / 中转站), all on the same box.
- **Share conversation history between accounts.** Sessions are stored locally in `~/.codex/sessions/` and `~/.codex/state_5.sqlite`, not tied to any account, so any account can list and resume any conversation.
- **Switch instantly without logging out.** `codex logout` revokes your refresh token server-side and bricks your saved profiles. `codex-switch use` only swaps local files.
- **Give each account its own Git worktree** so parallel agents never fight over the same working tree.

## Requirements

- OpenAI [Codex CLI](https://github.com/openai/codex) — tested on `0.153.4`
- `python3` (for reading session metadata)
- `bash`

## Install

```bash
git clone https://github.com/EchoTreee/codex-switch.git
cd codex-switch
./install.sh            # copies codex-switch into ~/.local/bin
```

Or one-shot:

```bash
curl -fsSL https://raw.githubusercontent.com/EchoTreee/codex-switch/main/install.sh | bash
```

## Quick start

```bash
# 1. Log in to Codex as usual, then save the account as a profile
codex login
codex-switch save work

# 2. Log in to a second account (or a relay), save it too
codex login              # log into a different account
codex-switch save home

# 3. Switch freely
codex-switch use work
codex-switch use home
codex-switch list        # list profiles; * marks the active one
```

That's the whole idea: **`save` once per account, then `use` to switch.**

## Commands

| Command | What it does |
|---|---|
| `codex-switch save <name>` | Save the current `auth.json` + `config.toml` as a profile |
| `codex-switch use <name>` | Switch to a profile (backs up the current one first) |
| `codex-switch relogin <name> [--device-auth]` | Re-login and refresh a profile whose token expired |
| `codex-switch list` | List all profiles |
| `codex-switch sessions` | List all sessions (id + provider + title) |
| `codex-switch resume <keyword>` | Resume a session by title keyword, using the current account/provider |
| `codex-switch status` | Show the current account and provider |
| `codex-switch delete <name>` | Delete a profile |

## Key concepts & gotchas

### 1. Never use `codex logout` to switch

`codex logout` revokes the refresh token on OpenAI's servers, which permanently invalidates any profile you saved for that account. Switch with `codex-switch use` instead — it only swaps local files.

### 2. Relays (中转站) need API-key auth

A relay is a custom provider with its own `base_url` (e.g. `https://api.example.com/v1`). Its profile must use `auth_mode = "apikey"`, not a ChatGPT OAuth token:

```bash
printf '%s' "$RELAY_API_KEY" | codex login --with-api-key
codex-switch save relay
```

If a relay profile accidentally holds a ChatGPT token, Codex will keep trying to refresh it and fail with `refresh token revoked`.

### 3. Cross-provider resume

Codex's own `/resume` picker only shows sessions from the *current* provider, and resuming a session uses the provider it was created under. To resume a session under a different account/provider:

```bash
codex-switch sessions            # find a keyword from the session's title
codex-switch resume <keyword>    # resume it with the current profile's provider/model
```

`codex-switch resume` runs `codex resume <id> -c model_provider=... -c model=...`, which re-points the session to the current provider. It is reversible — resume the same session again under another profile to point it back.

### 4. Multiple accounts, one machine

Each terminal runs its own `codex` process, which reads `~/.codex` **at startup** and keeps it in memory. So the practical pattern is:

```bash
# terminal 1
codex-switch use account-a
codex

# terminal 2
codex-switch use account-b
codex
```

Both processes now hold different accounts and run side by side, sharing the local session store — either one can `codex-switch resume` a conversation the other started.

> **Caveat:** the *active* profile is machine-wide (it's just whichever files are currently in `~/.codex`). A running Codex process may also write back to `~/.codex/auth.json` when it refreshes its token. For strict isolation of two always-on accounts, run each in its own `CODEX_HOME` (or container). For the common "two agents, each on its own account, working in parallel" workflow, one `~/.codex` plus `codex-switch use` per terminal is enough.

### 5. Independent Git worktrees

Pair each account with a separate checkout so two agents never clobber each other's files:

```bash
git worktree add ../project-b feature/b
cd ../project-b
codex-switch use account-b
codex
```

## Environment variables

- `CODEX_HOME` — Codex config dir (default `~/.codex`)
- `CODEX_SWITCH_DIR` — where profiles are stored (default `~/.config/codex-switch`)

## License

MIT — see [LICENSE](LICENSE).

---

## 中文说明

`codex-switch` 是 OpenAI Codex CLI 的多账号/多 provider 切换器。核心用法：每个账号 `codex-switch save <名字>` 存一次，之后 `codex-switch use <名字>` 切换；会话记录存在本地 `~/.codex/`，跨账号不丢；配合 `git worktree` 可让多个账号的 agent 并行开发、互不干扰。

三条铁律：**切换永远用 `use`，不要 `codex logout`**（会吊销 token）；**中转站要用 API key 登录**；**跨账号续对话用 `codex-switch resume`**。
