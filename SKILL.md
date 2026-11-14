---
name: doraemon-local-dev-guard
description: 本地开发环境守卫：轻量环境审计、智能路径发现、多 Agent 适配与最小风险预检。只读、零网络、不修改环境。不负责任务执行、调度与业务验收（归 doraemon-goal-driven-delivery）。
version: 2.0.1
---

# Doraemon Local Dev Guard (V2)

本地开发任务的**前置守卫**。回答三个问题：环境是否就绪、项目放哪里、有哪些最低限度需要知道的风险。除此之外不做任何事。

## 职责边界（硬性）

| 本 Skill 负责 | 不负责（→ goal-driven-delivery） |
|---|---|
| 环境识别 | 目标拆解 / 任务调度 |
| 路径策略 | 自主执行 / 重试熔断 |
| Agent 兼容 | 业务验收 |
| 风险预检（只报告） | Git 交付收口 |

- 默认**只读**。发现风险只报告，不自动修复。
- 缺失本 Skill 时，任务按其自身硬规则继续，不阻塞。
- 禁止循环调用、禁止与其他 Skill 互相依赖。

## 1. 轻量环境审计

普通任务只确认（不写长报告）：

- OS / 架构 / 当前用户 / Shell
- 当前工作目录及其可写性
- 本任务必需工具的可用性与版本
- 涉及仓库时：Git 状态（clean / dirty）
- 必需依赖是否缺失

异常或高风险场景（系统级修改、权限、迁移、生产）→ 完整审计。

## 2. 智能路径策略

1. **已有项目**：以真实路径为准，**禁止擅自迁移**（C 盘项目留在 C 盘）。
2. **新建项目（Windows）**：优先 `D:\Projects\<项目名>`。
   - 无 D 盘 / D 不可写 / 空间不足 → 报告 `BLOCKED`，**不自动退回 C 盘**，等用户授权。
3. **新建项目（macOS/Linux）**：使用实际可写数据目录（如 `~/` 或用户数据目录）。
4. Agent 系统配置（skills/plugins 等）遵循各 Agent 官方目录，不擅改。
5. **输入校验**：`project_name` 拒绝空白、`.`/`..`、路径穿越、目录分隔符、绝对路径及
   Windows 非法字符/保留设备名；`existing_project_path` 只读核验存在性与目录类型，
   无法确认时输出 `existence_verified: false`，绝不宣称已验证存在。

> 边界澄清：本节“路径策略”指**放置决策**（新项目放哪、旧项目动不动、阻断条件）。
> “搜索实际路径”（未提供精确路径时如何找到目标文件）属于
> doraemon-goal-driven-delivery 的 path-discovery 职责，本 Skill 不实现、不重复。

## 3. 多 Agent 适配

统一核心规则（上文 1–2–风险清单）。按 Agent 真实加载机制做最小适配：

- **Claude Code**：本 SKILL.md 原生加载于 user skills 目录。
- **Codex CLI**：`agents/openai.yaml` 提供接口声明（display_name / short_description / default_prompt）。
- 其他 Agent（Agnes Code / Hermes / WorkBuddy 等）：核心脚本 `scripts/local_dev_guard.py` 语言无关，任何能执行 Python 3 标准库脚本的 Agent 均可调用；无法实测的 Agent 标记 **UNVERIFIED**。

验证状态以 `README.md` 中“已验证状态”表为准；**加载≠行为验证**，未实测不写成已支持。

## 4. 最小风险清单（只报告）

- 路径冲突（目标路径已有内容）
- 权限不足（目录不可写）
- 环境不匹配（版本 / OS 与任务要求不符）
- 关键依赖缺失
- 现有工作区有未提交修改（**不覆盖**）

## 用法

```bash
python scripts/local_dev_guard.py --project-name myapp --tools git,node
python -c '...'  # 或直接 import: from local_dev_guard import run
```

`run(payload)` 输出纯 JSON：`env`（审计快照，用户名默认脱敏）、`path`（建议或 BLOCKED）、`risks`（清单，全部 `auto_fix_allowed: false`）。

## 停止条件

- 环境就绪、路径已建议、风险已列 → 立即停止，交棒给 goal-driven-delivery。
- 发现 `BLOCKED` 路径阻断 → 报告并停止，等授权。

## 验收字段（最终回报）

VERSION / SOURCE_PATH / CC_INSTALL_PATH / GITHUB_URL / PUBLIC_VERIFIED /
TESTS / AGENT_COMPATIBILITY / V1_PRESERVED / GIT_COMMIT / GIT_CLEAN / FINAL_STATUS
