# Multica Codex Sync 1.2

[English](README.md) | 简体中文

这个 Codex 插件把当前 Codex Desktop 任务准确绑定到一个 Multica issue，并持续
同步绑定后的可见消息和 token 用量。

## 设置

按照[项目 README](../../README.zh-CN.md)通过公开 marketplace 安装。完整重启
Codex Desktop，在设置中启用并信任本插件 Hook，然后新建任务。
Hook Trust 不能由插件自动完成。

插件需要 Python 3、`curl` 和已登录的 Multica CLI。聊天命令命名空间为
`/multica`。

## 使用

### 推荐：`/multica` 指令

在第一行开头输入 `/multica 4158`、`/multica status`、
`/multica stop`、`/multica help` 或 `/multica doctor`。issue 编号只是示例。
也支持 `/multica-4158` 等连字符形式。

### 可选：`/multica-sync` Skill

输入 `/multica-sync`，选择 **Multica Sync**，再输入 `4158`、`bind 4158`、
`status`、`stop`、`help` 或 `doctor`。不需要输入内部调用格式。

| 区别 | `/multica` 指令 | `/multica-sync` Skill |
| --- | --- | --- |
| 定位 | 推荐 | 可选 |
| 输入方式 | 在第一行输入完整指令 | 输入 `/multica-sync`，选择 **Multica Sync** 后输入动作 |
| Hook Trust | 需要 | 不需要 |
| 执行效果 | 固定控制直接完成；绑定会携带 issue 上下文继续 | 在 Agent 回合中执行动作 |

每个 Codex 任务只能跟踪一个 issue。如需换绑，请先停止当前跟踪，再单独
绑定新 issue。

## 隐私与安全

tracker 从绑定完成后的准确文件偏移开始，不同步更早历史、控制命令、隐藏推理
或工具原始 payload。Codex 提供私有 `$PLUGIN_DATA` 目录保存状态和日志；token
不会进入进程参数或日志。

内部清理代码会核对插件 ownership marker 和 tracker 进程身份。公开插件不提供
cleanup/purge 聊天指令。插件不会替换 Multica CLI、修改
Hook 配置或 Trust，也不会删除未知数据。详见项目
[安全模型](../../docs/security-model.zh-CN.md)。
