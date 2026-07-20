# 安全模型

## 信任边界

Codex 提供 `PLUGIN_ROOT`、`PLUGIN_DATA`、可信 Hook 定义和当前任务的准确 ID；
用户必须在设置页人工 Trust Hook。聊天文本、Hook payload、Multica API 返回、
issue/run ID、本地状态文件和 PID 都按不可信输入处理。

## 会同步什么

绑定后，tracker 会同步当前 Codex 任务中新增的可见用户/助手消息和 token 用量。
绑定前历史、控制命令、隐藏推理和工具原始 payload 不上传。

## 本地保护

- 目录权限为 `0700`，文件和日志为 `0600`。
- token 不进入进程参数；临时 curl 配置仅当前用户可读，并在请求后删除。
- 外部 run ID 先哈希再用作文件名。
- 遇到符号链接形式的私有状态目录会拒绝继续。
- 停止 tracker 时必须同时匹配 PID、命令、运行模式、状态路径和进程启动身份。
- 拿不到准确任务 ID 就拒绝绑定，不猜测最近任务。

## 安全移除

普通 cleanup 只停止身份匹配的 tracker，保留状态和日志。只有用户明确要求 purge
时，程序才会核对插件专属 ownership marker，并删除已知的状态、日志、锁和临时
文件；符号链接和未知文件会保留并报告。插件不会删除 Multica 配置、Codex 任务、
共享 Hook 配置或上层用户目录。

## 仍需用户信任的部分

被 Trust 的 Hook 可以在 Codex sandbox 外运行。因此应核对 Hook 命令，并只从
可信 Git ref 安装。网络加密和服务器授权取决于用户配置的 Multica 服务。安全
问题请通过 GitHub private vulnerability reporting 提交。
