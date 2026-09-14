# 并行工作流与风险

[返回中文首页](../README.zh-CN.md) · [English](parallel.md)

## 先明确你要的是什么

| 方式 | 适用需求 | 代价与边界 |
| --- | --- | --- |
| 共享 `CODEX_HOME`，集中启动各账号 | 一机多终端处理任务，同时保留一份本地对话历史。 | 认证文件和 profile 标记仍然共享，存在刷新、启动和回存竞态。 |
| 独立 `CODEX_HOME` + `CODEX_SWITCH_DIR` | 分开各组进程的认证文件和 profile 存储。 | 不再自动共享本地会话历史；详见[独立目录方式](usage.md#parallel-use)。 |
| 每个 agent 一个 Git worktree | 不同 agent 在不同工作目录和分支修改代码。 | 只分开代码文件，不隔离认证、端口、数据库或其他外部资源。 |

**作者在自己的环境中验证过的模式是：集中启动，各自完成任务，结束后再恢复凭据。共享 home 下频繁切换账号、重启并无缝续跑仍不可靠。** 这是使用经验，不是所有 Codex 版本或运行时长下的稳定性保证；本项目的模拟测试没有验证真实多账号长时间并发。

## 认证状态为什么会产生竞态

本指南针对文件凭据模式。Codex 运行时会持有认证状态，并可能刷新、持久化凭据；不能把“修改了磁盘文件”等同于“所有已启动进程立即切换账号”，也不能保证所有版本都只在启动时读取一次文件。官方文档说明了本地凭据缓存和使用期间的自动刷新，但没有保证固定的一小时有效期。参见 [Codex 身份验证](https://learn.chatgpt.com/docs/auth#login-caching)。

同一 home 下的 `auth.json` 是共享文件，不是每个进程各自的一份。刷新可能伴随 refresh token 轮换，旧 profile 因而可能变得不可用；新凭据即使已写入文件，也可能被另一账号后续写入覆盖。`save` 和 `use` 只能读取当时的文件，不能从指定 Codex 进程的内存里取回它自己的最新 token。

因此，“最新 token 只在内存里”并非始终成立；真正的问题是：**没有锁和身份核对时，无法可靠地把共享文件的某一次内容归属于目标账号。** API-key provider 不一定存在同样的 OAuth 刷新机制，但仍需要正确选择配置、文件凭据或环境变量。

## 三个具体风险

### 1. 新启动或恢复会话可能用错账号

共享 `auth.json` 可能已经被另一个账号的进程更新。新开终端、重启 CLI、执行 `codex-switch resume` 时，新进程需要取得认证状态，不能只凭终端名字或 `current` 标记推断账号。

在计划内集中启动时，每次先 `use <目标账号>` 再立即启动 Codex，有助于选择启动身份，但另一进程仍可能在这两步之间写文件。已经进入并行运行阶段后，需要确定身份的新启动或恢复，应先停止其他写入者再处理。内置子代理如何取得认证依实现而定，不能一概断言每个子代理都会重读该文件。

### 2. profile 可能陈旧，也可能保存到别人的凭据

一个账号的刷新凭据可能已更新，profile 中却仍保留旧副本；共享文件又可能刚好是另一账号的状态。这时 `save` 不会自动定位目标进程，重新命名保存也不能解决来源不确定的问题。

作者观察到长任务后旧快照被拒绝、需要 `relogin` 的情况，但“约一小时”不是可靠失效计时器。不要把 access token 的有效期、refresh token 轮换和 profile 可用性当成同一个固定时限。

### 3. `use` 自动回存可能写错 profile

脚本按 `current` 文件记录的名字，把当前磁盘凭据刷新回之前的 profile。共享 home 并行时，“当前文件就是这个 profile 的账号”可能已不成立，于是 A 的凭据可能被写进 B 的 profile。

即使稍后所有进程都退出，文件和标记也可能已经不一致。身份不确定时，先针对目标 profile 重新登录，而不要靠反复 `use` 或 `save` 猜测恢复。

## 作者采用的集中启动方式

开始前，关闭旧的共享 home 会话，准备好并确认两个账号的 profile。需要重新登录时在这个阶段完成；运行中不再维护 profile。下面假定已有 `official-work` 和 `official-personal`，且两终端使用同一 `CODEX_HOME` 和 `CODEX_SWITCH_DIR`。也应关闭会写入同一凭据存储的其他 Codex 客户端。

### 1. 为代码任务准备独立 worktree

在你要开发的代码项目根目录执行，分支名和目录名须尚未存在：

```bash
git worktree add ../project-work -b agent/work
git worktree add ../project-personal -b agent/personal
```

分配不同任务给两个 agent。独立工作目录可以避免直接互相覆盖文件，后续合并分支仍可能需要解决冲突。

### 2. 依次启动两个终端

终端 A：将示例路径替换为刚创建的 worktree。

```bash
cd /path/to/project-work
codex-switch use official-work
codex
```

完成 A 的启动并确认预期账号后，再启动终端 B：

```bash
cd /path/to/project-personal
codex-switch use official-personal
codex
```

这是作者使用过的启动顺序，不是原子切换或进程锁定机制；初始化期间也不能排除认证刷新竞态。共享标记或 `codex-switch status` 描述的是磁盘状态，不能证明所有运行中进程的身份。

### 3. 运行中各做各的任务

避免手动修改共享 `auth.json`，避免在 profile 之间频繁 `use`、`save` 或 `relogin`。这些限制只约束手动操作，无法阻止 Codex 自动刷新并写文件。

可以查看本地会话索引：

```bash
codex-switch sessions
```

但不要将 `codex-switch resume <关键词>` 视为只读查询：它会启动新的、需要认证的 Codex 进程。应在下面的收尾阶段处理续聊，或改用独立认证目录。也不要让两个进程同时恢复并写入同一条会话；共享历史用于后续接续，不等于同一会话支持并发编辑。

### 4. 收尾后恢复身份，再续聊

等所有共享 home 的进程退出，再使用目标账号。长任务后如果 profile 已陈旧、认证被拒绝或来源不确定，采用重新登录恢复，尤其不要反复切换来尝试“保存最新 token”。

```bash
codex-switch relogin official-work
codex-switch resume "parser"
```

登录时选对账号；`relogin` 会恢复该 profile 已保存的配置。如果当前配置本身已经被误存，还需检查并修正它。对中转站/API-key provider，应按其支持的认证方式恢复，不能把官方 OAuth 重新登录当成通用修复。

## 这套方式解决什么、不保证什么

它减少运行中人为切换，并把身份维护集中在任务开始前和所有进程退出后。本地历史仍可在之后跨账号、跨兼容 provider 接续；它不提供认证强隔离、不保证旧 token 永远有效，也不保证所有历史 token 都原样进入下一次模型请求。

切换器不调用 `codex logout` 或吊销接口，因而无需通过退出登录切换账号。但其他客户端退出、服务端策略、token 刷新或轮换仍可能影响已保存凭据。需要分开认证状态时，使用[独立 home 与 profile 存储目录](usage.md#parallel-use)，接受会话历史不自动共享的取舍。
