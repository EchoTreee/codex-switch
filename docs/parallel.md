# Parallel workflow and risks

[Back to README](../README.md) · [简体中文](parallel.zh-CN.md)

## Choose what to share

| Layout | Useful for | Tradeoff |
| --- | --- | --- |
| Shared `CODEX_HOME`, accounts launched in sequence | Multiple terminals on one machine with one local conversation store. | Credential files and profile markers remain shared, with startup, refresh, and save-back races. |
| Separate `CODEX_HOME` and `CODEX_SWITCH_DIR` | Separate authentication files and profile stores for each group of processes. | Local conversation history is no longer automatically shared; see [separate homes](usage.md#parallel-use). |
| One Git worktree and branch per agent | Keeping concurrent code edits in different working directories. | Does not isolate authentication, ports, databases, or other external resources. |

**The author's working pattern is to launch the planned accounts, let each finish its task, then recover credentials after shutdown. Frequent seamless switching and restarting during a shared-home run remains unreliable.** This is author-reported experience, not a stability guarantee across Codex versions or run durations. The repository's mock tests do not validate real long-running multi-account concurrency.

## Why authentication can race

This guide concerns file-based credentials. A running Codex process holds authentication state and may refresh and persist credentials. Changing a file does not establish that every running process immediately changes account, nor is reading the file exactly once at startup guaranteed across versions. The [official authentication guide](https://learn.chatgpt.com/docs/auth#login-caching) describes local caching and automatic token refresh during use; it does not establish a fixed one-hour lifetime.

With a shared home, `auth.json` is a shared file, not a file per process. Refresh may rotate a refresh token, leaving an older profile unusable. Even when new credentials have been written to disk, another account may overwrite that file later. `save` and `use` read the current file; they cannot extract the latest credentials from a particular running Codex process's memory.

The issue is therefore not that fresh credentials always exist only in memory. It is that **without locking and identity checks, the shared file cannot reliably be attributed to the intended account.** API-key providers may not use the same OAuth refresh mechanism, but still require the correct configuration and file-based or environment-based key.

## Three failure modes

### 1. A new or resumed process can use the wrong account

Another process may have updated the shared authentication file. A new terminal, restarted CLI, or `codex-switch resume` needs authentication; terminal names and the `current` marker are not proof of the selected account.

During planned startup, run `use <target>` immediately before launching Codex. This helps select an initial identity but is not atomic: an existing process may write between those operations. Once parallel work is underway, stop competing writers before a new launch or resume that needs a definite identity. Built-in subagent authentication depends on its implementation; not every subagent necessarily rereads this file.

### 2. A profile can contain stale or another account's credentials

Refreshed credentials may exist in a running account while its profile still holds an older copy. The shared file may now belong to another account. `save` cannot select the intended process, and changing the saved profile name does not resolve uncertain credential provenance.

The author has encountered rejected snapshots and needed re-login after long tasks. A duration of “about one hour” is not a reliable expiration timer: access-token lifetime, refresh-token rotation, and snapshot validity are different concerns.

### 3. Automatic save-back can update the wrong profile

`use` copies live files back to the profile named in `current`. During a parallel run, the files may no longer belong to that profile, so account A's credentials can be copied into profile B.

The marker and files may remain inconsistent even after every process exits. When identity is uncertain, re-login to the intended profile instead of repeatedly using or saving profiles in an attempt to recover the right credentials.

## The author's launch-and-finish pattern

Before starting, close old shared-home sessions and prepare valid profiles for both accounts. Do any necessary re-login now. The examples assume saved profiles `official-work` and `official-personal`, with the same `CODEX_HOME` and `CODEX_SWITCH_DIR` in both terminals. Also close other Codex clients that write to the same credential store.

### 1. Prepare separate code worktrees

From the root of the code project you will work on, using new branch and directory names:

```bash
git worktree add ../project-work -b agent/work
git worktree add ../project-personal -b agent/personal
```

Assign different tasks to each agent. Separate directories prevent direct overwrites of the same working files, but merging branches can still require conflict resolution.

### 2. Launch terminals in sequence

Terminal A, replacing the example path with the worktree you created:

```bash
cd /path/to/project-work
codex-switch use official-work
codex
```

Finish starting A and confirm the intended account before starting terminal B:

```bash
cd /path/to/project-personal
codex-switch use official-personal
codex
```

This is the author's startup sequence, not an atomic switch or identity-locking mechanism. Refresh races are possible even during startup. The shared marker and `codex-switch status` describe disk state; they do not establish every running process's identity.

### 3. Let the tasks finish

Avoid manually editing shared authentication files or repeatedly using `use`, `save`, or `relogin`. This reduces manual interference; Codex may still automatically refresh and write credentials.

You can look up local conversation records:

```bash
codex-switch sessions
```

Do not treat `codex-switch resume <keyword>` as a read-only lookup. It starts a new authenticated Codex process. Defer continuation until recovery below, or use a separate authentication home. Also avoid multiple processes resuming and writing the same conversation simultaneously: shared history enables later continuation, not concurrent editing of one session.

### 4. Recover identity before continuing

Wait for every process using the shared home to exit. If a profile is stale, authentication is rejected, or the snapshot's identity is uncertain, re-login rather than repeatedly switching in an attempt to save a fresh token.

```bash
codex-switch relogin official-work
codex-switch resume "parser"
```

Select the correct account during login. `relogin` restores the profile's saved configuration; if that configuration was also saved incorrectly, inspect and correct it. For a relay/API-key provider, recover using its supported authentication method rather than treating official OAuth re-login as a universal repair.

## Using herdr as your terminal interface

[herdr](https://github.com/herdrdev/herdr) is an optional TUI companion for keeping agent terminals together. The division of responsibilities is simple: herdr manages panes, codex-switch selects profiles, and Git worktrees separate code directories. This is a documented workflow suggestion, not a bundled integration or an end-to-end compatibility test.

1. Install herdr using its [official quick start](https://herdr.dev/docs/quick-start/), then run `herdr` in your code project.
2. Create one pane per worktree using herdr's split controls. In each pane, change into the intended worktree and use the account-specific startup commands above, completing one startup before the next.
3. Keep the agents running on their assigned tasks. herdr's pane status helps you see which agent needs attention; it does not verify that agent's ChatGPT account.

**Detaching is different from restarting.** With herdr's server still running, `Ctrl+B`, then `Q`, detaches the client; running `herdr` reattaches. Restarting the server or machine ends the old processes. Restored agents are new processes, so the shared-home authentication rules still apply.

According to [herdr's session-state documentation](https://herdr.dev/docs/session-state/), native agent resume on server restore is enabled by default. For a workflow that requires manual account selection before restarting Codex, consider disabling that automatic resume in your herdr configuration. Merge this key into the existing `[session]` section if one exists:

```toml
[session]
resume_agents_on_restore = false
```

This leaves account recovery and agent startup under your control; it does not prevent credential refresh races between agents that are already running. Before manually restarting or resuming, follow the recovery steps above. No herdr configuration is changed by codex-switch.

## What this pattern establishes

It reduces manual switching during work and moves identity maintenance to preparation and post-shutdown recovery. Existing local history remains available for later cross-account or compatible cross-provider continuation. It does not guarantee isolated authentication, permanently valid tokens, or that every historical token fits in the next model request.

The switcher never invokes `codex logout` or a revocation endpoint, so logging out is not a switching step. Other clients logging out, server-side policies, and token refresh or rotation can still affect saved credentials. If you need separate authentication files, use [separate homes and profile stores](usage.md#parallel-use), accepting that their conversation histories are not automatically shared.
