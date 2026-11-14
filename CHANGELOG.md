# Changelog

## 2.0.1 — V2.0.1 补丁（当前）

- 路径安全补丁（不扩展功能）：
  - `project_name` 校验：拒绝绝对路径、路径穿越（`..`）、目录分隔符（`/`、`\`）、
    空白、`.`/`..`，以及 Windows 非法字符（`< > : " / \ | ? *`）与保留设备名（CON/NUL/COM1-9/LPT1-9/AUX/PRN）。
  - `existing_project_path` 只读核验存在性与目录类型；无法确认时输出
    `existence_verified: false` + `existence_verification`（NOT_CHECKED/MISSING/NOT_A_DIRECTORY），
    绝不宣称已验证存在。保持不迁移原则不变。
- 保留 D 盘优先策略（B）与已有项目不迁移（C）行为不变。
- 新增回归测试类 `G_PathSafety`（12 项）；全量 26/26 通过。
- 未修改 goal-driven-delivery，未改动其他 Agent 配置，未覆盖 V1。

## 2.0.0 — V2（基线）

- 收窄职责为：环境审计、路径策略、Agent 兼容、最小风险预检（只读，只报告不修复）。
- 交付 / 调度 / 验收 / Git 收口交还给 doraemon-goal-driven-delivery。
- 新增跨平台核心脚本 `scripts/local_dev_guard.py`（Python 3 标准库，零依赖）。
- 新增验收测试 `tests/test_guard.py`（A–F）。
- 新增 Codex 适配 `agents/openai.yaml`。
- 路径策略：新建项目默认 D 盘；无 D 盘 / 不可写 / 空间不足报 BLOCKED，不自动退回 C 盘；
  已有项目禁止擅自迁移；POSIX 使用实际可写数据目录。
- 发布为 MIT 许可的公开仓库。

## 1.0 — V1（基线，保留于源机）

- V1 原件保留于源机 Codex Skill 目录（`~/.codex/skills/doraemon-local-dev-guard`，非 Git 仓库）。
- V1 职责偏重“干到底”的执行纪律（单假设、修改原则、调用额度、Git 纪律等）。
- V1 文件 SHA-256 基线（用于验收 J：V1 无损）：
  - `SKILL.md`        6131667bfbf0140a9d5057e5d9d51bb2b9fcaf81c51e351c39f19a3ac4d66716
  - `agents/openai.yaml` eb8b9915248c7a7c5ae550115f3213bc1e7aa57f30f1e600df18cc1e475e9d37
- V1 未被删除或改动；V2 在 D 盘独立开发，不覆盖 V1。
