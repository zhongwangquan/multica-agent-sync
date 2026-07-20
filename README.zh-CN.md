# Multica Agent Sync

[English](README.md) | 简体中文

Multica Agent Sync 是一个开源 Codex 插件：它把一个 Codex Desktop 任务绑定
到一个 Multica issue，并持续把绑定后的可见对话和 token 用量同步到对应的
local run。

当前仓库**只实现 Codex**。运行时已经把 Codex 适配层与 Multica 传输层分开，
便于未来评估其他 Agent，但这个版本不包含、也不宣称支持 Claude。

## 为什么使用插件方案

- 通过 Codex 插件管理器安装、升级和移除。
- Hook 跟随插件加载，安装器不修改用户 Hook 文件。
- 不替换、不包裹 `multica` 命令。
- 运行状态保存在 Codex 提供的 `$PLUGIN_DATA`，并使用当前用户私有权限。
- 清理前会核对归属、进程身份和已知文件名；未知文件一律保留。
- 源码、版本、Issue 和 PR 都可以在 GitHub 审查与追踪。

## 环境要求

- macOS，以及支持插件的 Codex Desktop。
- Python 3、`curl`。
- 已安装并登录 Multica CLI。插件复用现有登录配置，不输出 access token。

## 安装

只需添加一次公开 marketplace，然后安装插件：

```bash
codex plugin marketplace add zhongwangquan/multica-agent-sync --ref main
codex plugin add multica-codex-sync@multica-agent-sync
```

安装后：

1. 完整退出并重新打开 Codex Desktop。
2. 打开 **设置 → Hooks**。
3. 核对本插件的 `UserPromptSubmit` 命令，点击 **Trust** 并打开开关。这是
   Codex 要求保留的人工安全确认。
4. 新建一个 Codex 任务。

不要在聊天框输入 `/hooks`；Hook 的 Trust 操作在设置页完成。

## 使用

把命令放在第一行开头：

```text
/multica 4158
/multica status
/multica stop
```

也支持连字符形式：

```text
/multica-4158
/multica-status
/multica-stop
```

插件只识别 `/multica` 命名空间，不占用容易和 Codex 功能、模板或其他插件
冲突的通用 issue、stop 命令。

插件还提供 `help`、`doctor`、`status`、`cleanup` 四个 Skill。

## 升级

刷新 Git marketplace，再原地安装新版快照：

```bash
codex plugin marketplace upgrade multica-agent-sync
codex plugin add multica-codex-sync@multica-agent-sync
```

该过程不会删除插件数据或 Multica 配置。如果 Codex 把 Hook 标记为 modified，
请重新核对并 Trust，然后新建任务。

## 安全卸载

移除前，先让 Codex 执行本插件的 `cleanup` Skill。普通 cleanup 只停止进程身份
与插件状态完全匹配的 tracker，并保留历史。

然后移除插件；如果没有其他插件依赖这个 marketplace，也可以一并移除：

```bash
codex plugin remove multica-codex-sync@multica-agent-sync
codex plugin marketplace remove multica-agent-sync
```

普通清理和移除不会删除 Multica 登录、Codex 任务或无关文件。只有用户明确要求
删除插件自有历史和日志时，`cleanup` Skill 才会执行彻底清理。精确边界见
[安全模型](docs/security-model.zh-CN.md)。

## 开发

```bash
./scripts/test.sh
./scripts/smoke-install.sh .
```

参阅 [贡献指南](CONTRIBUTING.md)、[架构说明](docs/architecture.md) 和
[发布流程](RELEASING.md)。源码注释、docstring、提交、Issue 与 PR 使用英文；
用户文档同时维护英文与中文。

## License

[MIT](LICENSE)
