# Doraemon Local Dev Guard（哆啦A梦·本地开发守卫）

**一个给 AI 编程助手用的轻量 Skill：开工前的检查员。**
在你让 AI 开始开发之前，帮你确认电脑环境、选对项目位置、找出可能导致失败的风险。
版本 2.0.1 · MIT 许可。

> 它**不是**自动修电脑的软件：默认**只读**，只报告、不修复，不擅自安装、迁移或修改你的环境。

---

## 目录

- [为什么需要它？](#为什么需要它)
- [它能做什么？](#它能做什么)
- [工作原理](#工作原理)
- [支持哪些 AI 编程工具？](#支持哪些-ai-编程工具)
- [新手安装教程（Windows）](#新手安装教程windows)
- [最简单的使用方法](#最简单的使用方法)
- [实际输出示例](#实际输出示例)
- [与 Goal-Driven Delivery 的关系](#与-goal-driven-delivery-的关系)
- [常见问题](#常见问题)
- [技术说明与许可证](#技术说明与许可证)

---

## 为什么需要它？

让 AI 助手写代码时，失败往往不是因为代码本身，而是**开工前没检查**。真实场景：

| 场景 | 没有它时 | 有了它之后 |
|---|---|---|
| 项目路径是否真实存在不确定 | AI 反复试错、猜路径，甚至改错地方 | 预检对**你给出的**路径如实标注 `existence_verified: true/false`，不猜、不迁移 |
| 依赖或工具版本不对 | 写到一半才报错，来回折腾 | 预检直接列出缺什么 |
| 新项目建错位置 | 建进 C 盘深处、权限不够的目录 | 建议明确的落点（如 `D:\Projects\<项目名>`） |
| 原项目有未提交代码 | AI 不知道，可能覆盖你的工作 | 报告 `UNCOMMITTED_CHANGES` 风险，提醒先处理 |
| AI 未检查环境就开始开发 | 环境不匹配时浪费大量来回 | 开工前拿到一份审计报告 + 风险清单，再开始写代码 |

它回答的只有三个问题，然后**立即交棒**给 AI 继续开发：

1. 环境是否就绪？（系统、工具、Git 状态）
2. 项目应该放哪里？
3. 有哪些必须知道的风险？

## 它能做什么？

1. **看一眼你的电脑环境**：什么系统、什么架构、当前目录可不可写、你指定的必需工具（git、node、python…）装没装。
2. **判断项目该放哪**：已有项目原地不动（你给什么路径就用什么路径，只核验、不迁移）；Windows 上新项目建议 D 盘；D 盘不可用就明确阻断，不偷偷退回 C 盘。
3. **挑出开工前的风险**：路径冲突、目录不可写、工具/版本不符、依赖缺失、有未提交的代码——只报告，不擅自修。
4. **守住输入底线**：拒绝非法项目名（路径穿越、Windows 保留名如 `CON`/`NUL` 等），不存在的已有路径**绝不谎称已验证**。
5. **输出一份纯 JSON 报告**：机器可读、可复核。**默认只脱敏用户名**（显示为 `<user>`）；报告中的本地路径（如当前工作目录、建议路径）会如实出现，保存或分享前请自行留意。

## 工作原理

```
用户提出开发任务
        ↓
检查电脑环境（系统 / 工具 / 目录权限 / Git 状态，全部只读）
        ↓
确认项目位置（已有项目不动；新项目给建议；不行就 BLOCKED）
        ↓
提示风险（只报告，不自动修复）
        ↓
交给 AI 继续开发（交棒给 doraemon-goal-driven-delivery）
```

零网络、零模型调用、零环境修改。查完即止，不循环、不重试、不执行交付。

## 支持哪些 AI 编程工具？

先分清三个概念（本仓库的诚实原则）：

- **已安装**：Skill 文件完整放在该工具约定的目录里；
- **已加载**：宿主工具在实际会话中读取并识别了它（有会话证据，不是目录里有文件就够）；
- **行为已验证**：真实执行过、输出符合预期。

**仓库自带的单元测试不能充当宿主"已加载"或"行为已验证"的证明**——它只验证脚本逻辑本身。
无法实际验证的一律标 **UNVERIFIED**，不编造兼容性。

| 工具 | 适配方式 | 已安装 | 已加载 | 行为 | 证据 |
|---|---|---|---|---|---|
| Claude Code | 原生 `SKILL.md`，部署于 user skills 目录 | ✅ 本机 `~/.claude/skills/doraemon-local-dev-guard/` 文件完整 | ✅ 该 Skill 出现在 Claude Code 会话的可用技能列表中（宿主实际读取了 SKILL.md） | 核心脚本 CLI 行为已实测；**宿主按 Skill 自动调度的端到端行为 UNVERIFIED** | 本机目录 + 会话技能列表 + 真实 CLI 运行输出 |
| Codex CLI | `agents/openai.yaml` 接口声明 + 核心脚本 | ✅ 本机 `~/.codex/skills/doraemon-local-dev-guard/` 文件完整 | **UNVERIFIED**（未观察到 Codex 会话实际加载它） | **UNVERIFIED**（本机 codex-cli 0.159.3 可用、脚本可独立执行，但未经 Codex 宿主实测） | 本机目录 + codex --version |
| Agnes Code | 核心脚本语言无关（Python 3 标准库） | ❌ 未安装 | UNVERIFIED | UNVERIFIED | 无本机安装，无法实测 |
| Hermes | 同上 | ❌ 未安装 | UNVERIFIED | UNVERIFIED | 无本机安装，无法实测 |
| WorkBuddy | 同上 | ❌ 未安装 | UNVERIFIED | UNVERIFIED | 无本机安装，无法实测 |

> 原则：**安装 ≠ 加载 ≠ 行为验证**，三件事各自需要各自的证据。上表只写有证据的内容，没有证据的明确写 UNVERIFIED。
> 上表不成立也不影响使用：任何能运行 Python 3 标准库脚本的环境，都可以直接执行 `scripts/local_dev_guard.py`（见下文命令），这条路径不依赖任何宿主加载机制。

## 新手安装教程（Windows）

**先决条件**：Python 3（只需标准库，不装任何第三方包）。

**检查是否已装 Python**（PowerShell）：

```powershell
python --version
```

**安装步骤**（在 PowerShell 中复制即用，已实测通过）：

```powershell
# 1. 把仓库克隆到一个稳定位置（在你喜欢的位置运行，例如 D:\）
git clone https://github.com/hcxhcx1981-hash/doraemon-local-dev-guard

# 2. 进入仓库目录
cd doraemon-local-dev-guard

# 3. 跑一次测试，确认环境没问题（26 项全部通过即 OK）
python -m unittest discover -s tests
```

**装给 Claude Code**（复制进 Claude Code 的 user skills 目录；仍在仓库目录内执行，`.` 就是仓库根目录）：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills"
xcopy /E /Y /I . "$env:USERPROFILE\.claude\skills\doraemon-local-dev-guard\"
```

**装给 Codex CLI**（同样仍在仓库目录内执行）：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills"
xcopy /E /Y /I . "$env:USERPROFILE\.codex\skills\doraemon-local-dev-guard\"
```

**安装后检查**（以 Claude Code 目标为例，另一套把路径换成 `\.codex\`）：

```powershell
# 关键文件是否都在（两项都应输出 True）
Test-Path "$env:USERPROFILE\.claude\skills\doraemon-local-dev-guard\SKILL.md"
Test-Path "$env:USERPROFILE\.claude\skills\doraemon-local-dev-guard\scripts\local_dev_guard.py"

# 从安装位置直接跑一次，能输出 JSON 即安装成功
python "$env:USERPROFILE\.claude\skills\doraemon-local-dev-guard\scripts\local_dev_guard.py" --project-name demo
```

> 不想装进 Skill 目录也可以——`git clone` 后在仓库里运行下一节的命令即可使用。
> 如果目标目录里已有旧版本，先手动删除旧的 `doraemon-local-dev-guard` 文件夹再执行 `xcopy`，避免新旧文件混杂。

**macOS / Linux**（bash 或 zsh）：

```bash
git clone https://github.com/hcxhcx1981-hash/doraemon-local-dev-guard
cd doraemon-local-dev-guard
python3 -m unittest discover -s tests
# Claude Code:
mkdir -p ~/.claude/skills && cp -r . ~/.claude/skills/doraemon-local-dev-guard
# Codex CLI:
mkdir -p ~/.codex/skills && cp -r . ~/.codex/skills/doraemon-local-dev-guard
```

脚本本身跨平台；macOS/Linux 上"新建项目"策略使用实际可写的数据目录（如 `$HOME`），而非 D 盘。

## 最简单的使用方法

先 `cd` 到仓库目录。

**创建新项目之前**（给 AI 做开工预检：项目名 + 这个任务需要哪些工具）：

```bash
python scripts/local_dev_guard.py --project-name myapp --tools git,node,python
```

**检查已有项目**（只确认位置，绝不迁移）：

```bash
python scripts/local_dev_guard.py --existing "C:\Users\me\myproject"
```

常用参数一览（`--help` 可见完整列表）：

| 参数 | 说明 |
|---|---|
| `--project-name NAME` | 新项目名；拒绝 `..`、路径穿越、Windows 非法字符与保留名 |
| `--existing PATH` | 已有项目路径；只读核验存在性，结果里如实标注是否验证成功 |
| `--tools a,b,c` | 需要检查哪些工具可用（逗号分隔） |
| `--from-stdin` | 从标准输入读取完整 JSON payload |
| `--no-anonymize` | 保留真实用户名（默认脱敏为 `<user>`） |

## 实际输出示例

> 以下 JSON 来自真实运行（用户名与路径已脱敏），格式与 `--help` 参数一致。

**示例 1：检查已有项目，但路径实际不存在**（真实运行输出，节选自 `path` 块）

```bash
python scripts/local_dev_guard.py --existing "C:\Users\me\myproject"
```

```json
{
  "path": {
    "status": "USE_EXISTING",
    "path": "C:\\Users\\me\\myproject",
    "reason": "existing project kept in place; existence NOT verified (missing)",
    "auto_fallback": false,
    "existence_verified": false,
    "existence_verification": "MISSING"
  }
}
```

读法：`status: USE_EXISTING` 表示"不迁移、原地使用"；但 `existence_verified: false` + `MISSING` 提醒你——**这个路径在这台机器上不存在**，需要核对真实路径后再开工。

**示例 2：新建项目 + 工作区有未提交代码（高风险）**（真实 CLI 输出，`cwd` 指向一个有未提交修改的 Git 仓库）

```json
{
  "env": {
    "os_family": "windows",
    "git": { "clean": false, "changed": 1 }
  },
  "path": {
    "status": "RECOMMEND",
    "path": "D:\\Projects\\demo",
    "reason": "prefer D drive for new projects",
    "auto_fallback": false
  },
  "risks": [
    {
      "code": "UNCOMMITTED_CHANGES",
      "severity": "high",
      "detail": "existing workspace has uncommitted changes; will not overwrite",
      "auto_fix_allowed": false
    }
  ]
}
```

读法：

| 字段 | 含义 | 你要做什么 |
|---|---|---|
| `env.git.clean: false` | 当前 Git 工作区**不干净**（有未提交修改） | 先提交或暂存你自己的改动 |
| `risks[0].code: UNCOMMITTED_CHANGES`（severity: high） | 高风险：不处理就可能被覆盖 | 按上一条处理后再让 AI 开工 |
| `auto_fix_allowed: false` | 这条风险**只报告、不自动修** | 修复动作由你决定 |
| `path.status: RECOMMEND` | 正常：建议把新项目建在 `D:\Projects\demo` | 同意后照做即可 |
| `risks: []`（空） | 没发现风险，一切正常 | 直接交棒给 AI 开发 |

其他常见风险代码：`PATH_CONFLICT`（目标路径已有内容）、`PERMISSION`（目录不可写）、`ENV_MISMATCH`（版本/系统不符）、`MISSING_DEP`（缺依赖）。
路径被阻断时会出现 `path.status: BLOCKED` + `code`（如 `NO_D_DRIVE`）——**不会**自动退回 C 盘，需要你明确授权。

## 与 Goal-Driven Delivery 的关系

- **Local Dev Guard（本仓库）** 负责**开工前检查**：环境、路径、风险，查完即止。
- **doraemon-goal-driven-delivery（另一仓库）** 负责**后续任务交付**：目标拆解、调度、验收。
- 两者互补，不是互相替代。Guard 缺失时，任务按其自身规则继续，不阻塞。

## 常见问题

**Q：不会 Python 怎么办？**
只需要系统里装有 Python 3（运行 `python --version` 检查；Windows 可从 [python.org](https://www.python.org) 安装，勾选加入 PATH）。本工具**只用 Python 标准库，不安装任何第三方包**，你也不需要读 Python 代码——照抄命令即可。

**Q：会修改我的电脑吗？**
不会。零网络、零模型调用、零环境修改：不装依赖、不建目录、不迁移项目、不改 Git 历史。发现风险**只报告**（`auto_fix_allowed` 恒为 `false`）。

**Q：为什么建议 D 盘？**
C 盘通常放系统，新建项目容易混进系统目录、权限受限；D 盘一般数据盘、空间充足。所以 Windows 上新项目默认建议 `D:\Projects\<项目名>`。

**Q：没有 D 盘怎么办？**
工具会报 `BLOCKED: NO_D_DRIVE`（D 不可写 / 空间不足同理），**绝不自动退回 C 盘**，等你明确授权后再指定位置。

**Q：原来的项目会被迁移吗？**
不会。已有项目一律 `USE_EXISTING`，原地不动；路径无法核验时会如实标注 `existence_verified: false`，绝不谎称。

**Q：可以单独使用吗？**
可以。不装 Skill、不配合任何交付工具，直接在仓库里运行第 6 节的命令就能拿到完整报告；它也不依赖其他 Skill 才能工作。

## 技术说明与许可证

- 核心实现：[scripts/local_dev_guard.py](scripts/local_dev_guard.py)（Python 3 标准库，跨平台）
- 验收测试：[tests/test_guard.py](tests/test_guard.py)（`python -m unittest discover -s tests`，26 项）
- Claude Code 说明：[SKILL.md](SKILL.md)；Codex 适配：[agents/openai.yaml](agents/openai.yaml)
- 版本与变更记录：[CHANGELOG.md](CHANGELOG.md)
- 许可证：[MIT](LICENSE)
