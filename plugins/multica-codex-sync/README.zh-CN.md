# Multica Codex Sync 1.1

[English](README.md) | 简体中文

这个 Codex 插件把当前 Codex Desktop 任务准确绑定到一个 Multica issue，并持续
同步绑定后的可见消息和 token 用量。

## 设置

按照[项目 README](../../README.zh-CN.md)通过公开 marketplace 安装。完整重启
Codex Desktop，打开 **设置 → Hooks**，核对 `UserPromptSubmit` 命令，点击
**Trust** 并开启，然后新建任务。Hook Trust 不能、也不应该由插件自动完成。

插件需要 Python 3、`curl` 和已登录的 Multica CLI。

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

这些是 Hook 指令，不是 Skill。状态、停止、帮助和诊断会在 prompt 进入模型前完成；
绑定 issue 则会在 Hook 注入准确 issue 上下文后，按设计继续当前模型任务。请直接
输入完整指令，Plugin 不再向 Skill 列表添加 Multica 运行方法。

## 隐私与安全

tracker 从绑定完成后的准确文件偏移开始，不同步更早历史、控制命令、隐藏推理
或工具原始 payload。Codex 提供私有 `$PLUGIN_DATA` 目录保存状态和日志；token
不会进入进程参数或日志。

内部清理代码会核对插件 ownership marker 和 tracker 进程身份。公开插件不提供
cleanup/purge 聊天指令。插件不会替换 Multica CLI、修改
Hook 配置或 Trust，也不会删除未知数据。详见项目
[安全模型](../../docs/security-model.zh-CN.md)。
