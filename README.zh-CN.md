# Multica Agent Sync

[English](README.md) | 简体中文

[![CI](https://github.com/zhongwangquan/multica-agent-sync/actions/workflows/ci.yml/badge.svg)](https://github.com/zhongwangquan/multica-agent-sync/actions/workflows/ci.yml)
[![最新版本](https://img.shields.io/github/v/release/zhongwangquan/multica-agent-sync)](https://github.com/zhongwangquan/multica-agent-sync/releases/latest)
[![GitHub Stars](https://img.shields.io/github/stars/zhongwangquan/multica-agent-sync)](https://github.com/zhongwangquan/multica-agent-sync/stargazers)
[![待处理 Issue](https://img.shields.io/github/issues/zhongwangquan/multica-agent-sync)](https://github.com/zhongwangquan/multica-agent-sync/issues)

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

需要结果可复现时，使用明确的发布 tag 添加公开 marketplace，再安装插件：

```bash
codex plugin marketplace add zhongwangquan/multica-agent-sync --ref v1.0.0
codex plugin add multica-codex-sync@multica-agent-sync
```

Git tag 就是插件的发布边界；Codex 不要求额外构建 ZIP 或二进制包。每个 GitHub
Release 也会自动提供源码压缩包。

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

添加 marketplace 时可以选择发布通道：

| Ref | 用途 | 更新行为 |
| --- | --- | --- |
| `v1.0.0` | 固定稳定版本 | 始终保持在该版本 |
| `main` | 最新稳定通道 | 仅在执行 marketplace upgrade 后变化 |
| `develop` | 测试通道 | 可能包含尚未发布的改动 |

希望方便地持续升级稳定版时，使用 `--ref main` 添加 marketplace。之后刷新 Git
marketplace，再原地安装新版快照：

```bash
codex plugin marketplace upgrade multica-agent-sync
codex plugin add multica-codex-sync@multica-agent-sync
```

指定版本安装或回退时，使用 `--ref vX.Y.Z`。切换命令和分支策略见
[发布通道说明](docs/release-channels.md)。marketplace 快照不会持续自动同步
GitHub，只有执行上述命令后，本地安装代码才会变化。

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
[发布流程](RELEASING.md)。测试 GitHub 上的公开分支或 tag，可以运行
`./scripts/smoke-install.sh zhongwangquan/multica-agent-sync <ref>`。源码注释、
docstring、提交、Issue 与 PR 使用英文；用户文档同时维护英文与中文。

## 项目数据趋势

插件不采集分析数据或遥测。公开的使用与维护趋势只来自 GitHub：

- [Star 趋势](https://www.star-history.com/#zhongwangquan/multica-agent-sync&Date)
- [贡献者趋势](https://github.com/zhongwangquan/multica-agent-sync/graphs/contributors)
- [PR 与 Issue 活跃度](https://github.com/zhongwangquan/multica-agent-sync/pulse)
- [版本发布记录](https://github.com/zhongwangquan/multica-agent-sync/releases)

[![Star History Chart](https://api.star-history.com/svg?repos=zhongwangquan/multica-agent-sync&type=Date)](https://www.star-history.com/#zhongwangquan/multica-agent-sync&Date)

## License

[MIT](LICENSE)
