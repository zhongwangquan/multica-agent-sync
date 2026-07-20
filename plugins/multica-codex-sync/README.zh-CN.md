# Multica Codex Sync 1.0

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
```

对应的连字符形式为 `/multica-4158`、`/multica-status`、`/multica-stop`。
插件不识别其他命令命名空间。

## 隐私与安全

tracker 从绑定完成后的准确文件偏移开始，不同步更早历史、控制命令、隐藏推理
或工具原始 payload。Codex 提供私有 `$PLUGIN_DATA` 目录保存状态和日志；token
不会进入进程参数或日志。

cleanup 会核对插件 ownership marker 和 tracker 进程身份。插件不会替换
Multica CLI、修改 Hook 配置或 Trust，也不会删除未知数据。详见项目
[安全模型](../../docs/security-model.zh-CN.md)。

## Skills

- `help`：说明命令和设置。
- `doctor`：检查本地状态，不暴露凭据。
- `status`：检查 tracker，不输出对话正文。
- `cleanup`：停止插件自有 tracker；只有用户明确要求时，才彻底清除插件自有
  历史和日志。
