# Multica Codex Sync 1.2

[English](README.md) | 简体中文

这个 Codex 插件把当前 Codex Desktop 任务准确绑定到一个 Multica issue，并持续
同步绑定后的可见消息和 token 用量。

## 设置

按照[项目 README](../../README.zh-CN.md)通过公开 marketplace 安装。完整重启
Codex Desktop 后新建任务。只有旧 `/multica ...` 指令需要 Hook Trust；
Skill 动作会直接调用 tracker CLI。Hook Trust 不能、也不应该由插件自动完成。

插件需要 Python 3、`curl`，默认使用已登录的 Multica CLI，也兼容
已登录的 Wujie CLI。配置发现优先 Multica、然后回退到 Wujie；聊天命令
命名空间仍为 `/multica`。

## 聊天框命令

命令必须位于第一行开头：

```text
/multica 4158
/multica status
/multica stop
/multica help
/multica doctor
```

对应的连字符形式为 `/multica-4158`、`/multica-status`、`/multica-stop`、
`/multica-help` 和 `/multica-doctor`。插件不识别其他命令命名空间。

从 `/` Skill 选择器中选择 **Multica Codex Sync**，然后提交 `4158`、
`bind 4158`、`status`、`stop`、`help` 或 `doctor`。显式调用方式为：

```text
$multica-codex-sync:control 4158
$multica-codex-sync:control bind 4158
$multica-codex-sync:control status
$multica-codex-sync:control stop
$multica-codex-sync:control help
$multica-codex-sync:control doctor
```

| 行为 | Skill 动作 | 旧 `/multica` 指令 |
| --- | --- | --- |
| 执行方式 | Agent 直接调用 tracker CLI | Hook 拦截 prompt 第一行 |
| Hook Trust | 不需要 | 需要 |
| 模型回合 | 在当前 Agent 回合执行 | 信息类动作在模型回合前完成；绑定会携带 issue 上下文继续 |
| 定位 | 推荐入口 | 兼容入口 |

Skill 动作会直接调用已安装的 tracker CLI，并使用 `CODEX_THREAD_ID`
精确定位当前任务，不经过 Hook。Hook 仅作为 `/multica ...` 指令的兼容入口。

每个 Codex 任务只能跟踪一个 issue。若当前任务已经跟踪其他 issue，插件不会自动
换绑。请使用同一入口，分两次动作先停止、再绑定。

## 隐私与安全

tracker 从绑定完成后的准确文件偏移开始，不同步更早历史、控制命令、隐藏推理
或工具原始 payload。Codex 提供私有 `$PLUGIN_DATA` 目录保存状态和日志；token
不会进入进程参数或日志。

内部清理代码会核对插件 ownership marker 和 tracker 进程身份。公开插件不提供
cleanup/purge 聊天指令。插件不会替换 Multica 或 Wujie CLI、修改
Hook 配置或 Trust，也不会删除未知数据。详见项目
[安全模型](../../docs/security-model.zh-CN.md)。
