# Multica Codex Sync 1.2

[English](README.md) | 简体中文

这个 Codex 插件把当前 Codex Desktop 任务准确绑定到一个 Multica issue，并持续
同步绑定后的可见消息和 token 用量。

## 设置

按照[项目 README](../../README.zh-CN.md)通过公开 marketplace 安装。完整重启
Codex Desktop 后新建任务。从 `/` Skill 选择器使用
**Multica Codex Sync** 无需额外设置。只有旧 `/multica ...` 指令需要
Hook Trust，且 Hook Trust 不能由插件自动完成。

插件需要 Python 3、`curl`，默认使用已登录的 Multica CLI，也兼容
已登录的 Wujie CLI。配置发现优先 Multica、然后回退到 Wujie；聊天命令
命名空间仍为 `/multica`。

## 使用

在 Codex 聊天框输入 `/`，选择 **Multica Codex Sync**，然后输入一个
动作：`4158`、`bind 4158`、`status`、`stop`、`help` 或 `doctor`。issue
编号只是示例。这是推荐用法，不需要 Hook Trust。

如需兼容旧用法，可以先启用插件 Hook，再在第一行开头输入
`/multica 4158`、`/multica status`、`/multica stop`、`/multica help` 或
`/multica doctor`。也支持 `/multica-4158` 等连字符形式。

每个 Codex 任务只能跟踪一个 issue。如需换绑，请先停止当前跟踪，再单独
绑定新 issue。

## 隐私与安全

tracker 从绑定完成后的准确文件偏移开始，不同步更早历史、控制命令、隐藏推理
或工具原始 payload。Codex 提供私有 `$PLUGIN_DATA` 目录保存状态和日志；token
不会进入进程参数或日志。

内部清理代码会核对插件 ownership marker 和 tracker 进程身份。公开插件不提供
cleanup/purge 聊天指令。插件不会替换 Multica 或 Wujie CLI、修改
Hook 配置或 Trust，也不会删除未知数据。详见项目
[安全模型](../../docs/security-model.zh-CN.md)。
