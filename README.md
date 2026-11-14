# Doraemon Local Dev Guard（V2，版本 2.0.1）

本地开发任务的**前置守卫**：轻量环境审计、智能路径发现、多 Agent 适配、最小风险预检。
默认**只读**——零网络、零模型调用、零环境修改，不安装依赖（仅 Python 3 标准库）。

## 定位

回答三个问题，然后立即交棒：

1. 环境是否就绪？（OS / 架构 / 用户 / Shell / 工作目录权限 / 必需工具及版本 / Git 状态 / 缺失依赖）
2. 项目应该放哪里？（路径策略，见下）
3. 有哪些必须知道的风险？（路径冲突、权限不足、环境不匹配、关键依赖缺失、未提交修改）

## 与 doraemon-goal-driven-delivery 的职责区别

| doraemon-local-dev-guard（本仓库） | doraemon-goal-driven-delivery（另一仓库） |
|---|---|
| 环境识别（审计） | 目标拆解 |
| 路径**放置**策略 | 路径**搜索**（path-discovery：未给路径时找到目标） |
| Agent 兼容适配 | 任务调度 / 重试 / 熔断 |
| 风险预检（只报告） | 业务验收 / Git 交付收口 |

两者共用统一核心规则，但**不循环调用、不互相依赖**：Guard 缺失时任务按自身硬规则继续。
本 Skill 绝不实现“干到底”的交付能力；goal-driven-delivery 也不重复环境守卫。

## 使用方式

```bash
# 一行预检（项目名 + 必需工具）
python scripts/local_dev_guard.py --project-name myapp --tools git,node,python

# 指定已有项目路径（只确认不迁移）
python scripts/local_dev_guard.py --existing "C:\Users\me\myproject"

# 或作为库
python -c "import sys; sys.path.insert(0,'scripts'); import json,local_dev_guard as g; \
print(json.dumps(g.run({'project_name':'myapp','required_tools':['git']}),indent=2))"
```

输出为纯 JSON：`env`（审计快照，用户名默认脱敏为 `<user>`）、`path`（建议 / BLOCKED）、
`risks`（风险清单，全部 `auto_fix_allowed: false`）。

## 路径策略

- **已有项目**：以真实路径为准，**禁止擅自迁移**（C 盘项目留在 C 盘）。
- **新建项目（Windows）**：默认建议 `D:\Projects\<项目名>`。
  - 无 D 盘 / D 不可写 / 空间不足 → 报告 `BLOCKED`，**不自动退回 C 盘**，须用户明确授权。
- **新建项目（macOS/Linux）**：使用实际可写数据目录（如 `$HOME`）。
- Agent 系统配置（skills / plugins 等）遵循各 Agent 官方目录要求，本 Skill 不擅改。
- **输入校验（V2.0.1）**：`project_name` 拒绝空白、`.`/`..`、路径穿越、目录分隔符、
  绝对路径及 Windows 非法字符 / 保留设备名；`existing_project_path` 只读核验存在性与
  目录类型，无法确认时输出 `existence_verified: false`，绝不宣称已验证存在。

## 多 Agent 适配与已验证状态

核心规则统一；适配按各 Agent 的**真实加载机制**做最小实现：

| Agent | 适配方式 | 状态 | 证据 |
|---|---|---|---|
| Claude Code | 原生 SKILL.md（YAML frontmatter），部署于 user skills 目录 | **已验证（本机）** | 本机 CC 目录 + 单元测试 A–F |
| Codex CLI | `agents/openai.yaml` 接口声明 + 核心脚本 | **已验证（适配文件存在；行为实测 UNVERIFIED）** | 结构与 `~/.codex/skills/` 下多个现有本地 Skill 的 `agents/openai.yaml` 一致；本机 codex-cli 0.159.3 可用 |
| Agnes Code | 核心脚本语言无关（Python 3 stdlib） | **UNVERIFIED** | 无本机安装 |
| Hermes | 核心脚本语言无关 | **UNVERIFIED** | 无本机安装 |
| WorkBuddy | 核心脚本语言无关 | **UNVERIFIED** | 无本机安装 |
| 其他兼容 Agent | 任何可执行 Python 3 标准库脚本的环境 | **UNVERIFIED** | — |

原则：**安装 ≠ 加载 ≠ 行为验证**；无法实测的 Agent 一律如实标 UNVERIFIED，不伪造。

## 仓库内容

```
SKILL.md                  # 核心 Skill（简短）
scripts/local_dev_guard.py # 唯一必需脚本（stdlib only，跨平台）
tests/test_guard.py       # 验收测试 A–F
agents/openai.yaml        # Codex 适配
README.md / CHANGELOG.md / LICENSE
```

## 安全

- 零网络、零模型调用、零环境修改、零新增依赖。
- 不修改 CC Switch / 模型路由 / 密钥配置；不访问、不提交任何真实凭据。
- 审计输出默认脱敏用户名；仓库不包含本机环境报告或个人信息。

## 许可

MIT（V1 无 LICENSE，V2 首次公开发布采用 MIT；V1 原件在源机保留，见 CHANGELOG）。
