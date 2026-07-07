# ForgeSkill

Turn top GitHub repositories into evidence-grounded Codex skills and project scaffolds.

ForgeSkill 是一个面向 Codex 的开源生态研究与生成型 skill。它能根据用户提出的软件方向，自动扫描 GitHub 上相关的高 star 项目，筛选真正匹配主题的候选，分析每个项目的优缺点、架构模式、维护状态和可复用设计，然后把这些经验融合成一个新的 Codex skill 或项目骨架。

它的目标不是简单搬运 GitHub 排行榜，而是把 GitHub 当作一个可研究的开源样本库：先找到相关项目，再用 LLM 做二次判断，最后把多个项目里真正值得复用的模式锻造成新的工具雏形。

## 一句话介绍

ForgeSkill turns open-source project research into new Codex skills and project scaffolds.

中文可以理解为：

> 输入一个软件想法，ForgeSkill 会调研 GitHub 上相关的优秀项目，总结优缺点，并融合生成一个新的 skill 或项目骨架。

## 项目亮点

- **不是 GitHub 排行榜复读机**：ForgeSkill 会先扩大候选池，再用相关度、质量评分和 LLM 二次重排过滤噪声。
- **适合中文创意输入**：可以把 `AI小说创作`、`智能体框架`、`数据看板` 这类中文或宽泛方向扩展成更适合 GitHub 搜索的英文 query。
- **有固定融合蓝图**：最终产物不是散乱的调研笔记，而是包含竞品分析、可复用模式、MVP 范围、架构设计和实施计划的结构化方案。
- **能从研究走到落地**：内置 materializer，可以把融合后的 concept 自动生成新的 Codex skill 或项目 scaffold。
- **重视证据与安全**：每个结论都应回到仓库证据，不默认复制被调研项目的代码、文档、品牌或资产。

## 典型用法

```text
Use $forge-skill to research AI小说创作, summarize the top GitHub projects, and create a better new skill.
```

或者：

```text
Use $forge-skill to scan GitHub for agent framework projects, compare the best patterns, and scaffold a new project.
```

## 为什么需要 ForgeSkill

很多新项目并不是从零开始想出来的，而是从已有工具、框架和开源生态中提炼出来的。问题是，手动做这件事很慢：

- GitHub 搜索结果容易被高 star 但不相关的项目污染。
- 中文想法往往需要转换成多个英文搜索词才能搜准。
- Stars 只能说明热度，不能说明项目是否适合复用。
- README 里的卖点、真实架构、维护状态、license 风险需要一起判断。
- 从“调研结论”到“真正可用的 skill/project scaffold”还需要额外落地步骤。

ForgeSkill 把这些步骤串成一个可复用流程：**发现项目 → 过滤候选 → LLM 重排 → 优缺点分析 → 模式融合 → 生成蓝图 → 自动落地**。

## 核心能力

### GitHub 候选扫描

ForgeSkill 会调用 GitHub API 搜索相关仓库，并抓取候选项目的核心证据：

- stars、forks、open issues
- license、topics、主语言
- 最近 push 时间和维护活跃度
- README 摘要
- GitHub URL 和 matched query

### 中文与宽泛主题自动扩展

当用户输入类似 `AI小说创作`、`智能体框架`、`数据看板` 这类中文或宽泛主题时，ForgeSkill 会自动扩展成更适合 GitHub 搜索的英文 query。

例如 `AI小说创作` 会扩展出：

```text
AI novel writing
AI fiction writing
AI story generator
LLM creative writing
worldbuilding writing assistant
long-form fiction AI
```

### 相关度与质量评分

ForgeSkill 不只看 stars。它会给每个候选项目生成两个辅助信号：

- `relevance_score`：项目和用户主题的真实匹配度。
- `quality_score`：项目作为参考样本的健康度，包括维护活跃度、license 清晰度、README 完整度、fork/issue 比例、topics 等。

这两个分数不会替代判断，而是帮助 Codex 做更可靠的二次筛选。

### LLM 二次重排

ForgeSkill 会生成 `LLM Rerank Worksheet`。Codex 会根据证据判断哪些仓库真正值得进入最终分析，而不是机械选择 star 最高的项目。

它会主动排除：

- 只是碰巧包含关键词的泛项目
- awesome list 或资料集合
- 个人主页、组织 profile、内容 dump
- 只适合学习但不适合借鉴架构的教程项目
- license 或维护状态明显不适合复用的项目

### 优缺点与可复用模式提炼

对最终入选项目，ForgeSkill 会总结：

- 项目目标和核心用户
- 主要工作流
- 产品优点和技术优点
- 缺点、风险和缺失能力
- 值得复用的架构、数据模型、prompt/workflow 设计
- 不应该复制或不适合过度借鉴的部分

### 固定融合蓝图

ForgeSkill 使用固定输出结构，把调研结果变成可执行方案：

- 研究快照
- LLM 重排后的 Top 项目
- 项目逐个分析
- 跨项目模式总结
- 新概念定位
- MVP 范围
- 架构或 skill 设计
- 实施计划
- 证据附录

### 自动落地成文件

当用户要求“做出来”“生成 skill”“生成项目骨架”时，ForgeSkill 可以把融合蓝图转换成 JSON spec，并调用内置 materializer 自动创建：

- 新 Codex skill
- 新项目 scaffold

生成 skill 时会包含 `SKILL.md`、`agents/openai.yaml`、可选 `references/` 和 `scripts/`，并可自动运行 skill validator。

生成项目时会创建 README、blueprint、基础目录结构和可扩展文件。

## 适合场景

ForgeSkill 适合这些任务：

- 基于 GitHub 上成熟项目快速做开源生态研究。
- 总结某类软件工具的共同模式和设计缺口。
- 从多个开源项目中融合出一个新的产品方向。
- 自动创建一个新的 Codex skill。
- 快速生成项目 scaffold 和 MVP 蓝图。
- 对某个方向做竞品分析、技术选型或灵感收集。
- 把“我想做一个类似某类工具”的模糊想法变成可执行计划。

## 工作原理

```text
User idea
  -> query expansion
  -> GitHub candidate scan
  -> relevance and quality scoring
  -> LLM rerank worksheet
  -> project-by-project analysis
  -> cross-project synthesis
  -> fusion blueprint
  -> optional skill/project materialization
```

这个流程让 ForgeSkill 既能保持自动化速度，又不会把“高 star”误当成“高价值”。它把搜索、证据、判断和落地分开处理，让最终产物更可靠。

## 你会得到什么

一次完整的 ForgeSkill 工作流通常会产出三类结果：

- **GitHub 研究报告**：包含候选项目、stars、维护状态、license、README 摘要、相关度和质量评分。
- **融合蓝图**：包含 Top 项目重排理由、逐项优缺点、跨项目模式、差异化定位、MVP 范围和实施计划。
- **可落地文件**：按需生成新的 Codex skill 或项目骨架，包括 README、blueprint、基础目录、`SKILL.md`、`agents/openai.yaml`、`references/` 和 `scripts/`。

换句话说，它把“我想做一个类似某类工具”的一句话，推进到“我知道该参考谁、避免什么、怎么设计、文件已经生成好”的状态。

## 仓库结构

```text
forge-skill/
  SKILL.md
  agents/
    openai.yaml
  references/
    fusion_blueprint.md
    materialization_spec.md
    synthesis_rubric.md
  scripts/
    github_scan.py
    materialize.py
```

## 安装到 Codex

把本仓库里的 `forge-skill/` 文件夹复制到你的 Codex skills 目录。

Windows PowerShell:

```powershell
Copy-Item -Recurse -Force .\forge-skill "$env:USERPROFILE\.codex\skills\forge-skill"
```

安装后，在新对话或刷新后的 Codex 会话里可以直接调用：

```text
Use $forge-skill to scan AI小说创作 projects on GitHub and synthesize a new skill.
```

## 二次开发

如果你想基于 ForgeSkill 做自己的分支，建议优先改这几个位置：

```text
forge-skill/SKILL.md
forge-skill/references/fusion_blueprint.md
forge-skill/references/synthesis_rubric.md
forge-skill/references/materialization_spec.md
forge-skill/scripts/github_scan.py
forge-skill/scripts/materialize.py
```

常见扩展方向：

- 增加更多领域的 query expansion 规则。
- 改进 `relevance_score` 和 `quality_score` 的评分逻辑。
- 增加新的 materializer，例如生成 Next.js app、CLI tool、Python package 或插件骨架。
- 把扫描结果接入数据库、向量检索或长期知识库。
- 为特定垂直领域定制融合蓝图，例如写作、设计、数据分析、agent、DevOps。

## 推荐工作流

### 1. 用户提出方向

例如：

```text
我想做一个 AI 小说创作 skill，扫描 GitHub 上相关项目，总结优缺点，然后融合成一个更好的 skill。
```

Codex 会触发本 skill，并按以下顺序执行：

1. 明确目标：生成 skill、项目方案，还是项目骨架。
2. 运行 GitHub 扫描脚本。
3. 读取候选报告。
4. 做 LLM 二次重排。
5. 总结优缺点和可复用模式。
6. 生成融合蓝图。
7. 如果用户要求落地，生成 JSON spec 并调用 `materialize.py`。
8. 运行 validator 或 smoke test。

### 2. GitHub 扫描

直接运行：

```powershell
python .\forge-skill\scripts\github_scan.py "AI小说创作" --limit 10 --candidate-limit 30 --out work\ai-novel-scan.json
```

它会同时生成：

```text
work\ai-novel-scan.json
work\ai-novel-scan.md
```

Markdown 报告里会包含：

- 自动扩展后的 queries
- focus terms
- candidate repositories
- stars
- relevance score
- quality score
- LLM rerank worksheet
- 每个仓库的证据摘要

### 3. Query 自动扩展

默认开启。比如输入：

```text
AI小说创作
```

会自动扩展成类似：

```text
AI novel writing
AI fiction writing
AI story generator
LLM creative writing
worldbuilding writing assistant
long-form fiction AI
AI writing assistant
```

如果你想精确搜索，不想自动扩展：

```powershell
python .\forge-skill\scripts\github_scan.py "exact topic" --no-auto-expand
```

### 4. LLM 二次重排

脚本不会把 GitHub stars 当最终答案。它会先给候选池，然后让 Codex 根据以下因素重排：

- 是否真的匹配用户主题
- stars 和社区热度
- 最近维护活跃度
- license 是否清晰
- README 和文档质量
- 可复用架构或工作流
- 是否只是泛项目、资料列表、个人主页、教程或相邻领域项目

报告中的 `relevance_score` 是领域相关度参考，`quality_score` 是维护和复用质量参考。最终判断仍由 Codex 根据证据完成。

## 常用命令

### 扫描 AI 小说创作项目

```powershell
python .\forge-skill\scripts\github_scan.py "AI小说创作" --limit 10 --candidate-limit 30 --out work\ai-novel-scan.json
```

### 扫描 agent 框架

```powershell
python .\forge-skill\scripts\github_scan.py "AI agent framework" --limit 10 --candidate-limit 40 --out work\agent-framework-scan.json
```

### 增加自定义 query

```powershell
python .\forge-skill\scripts\github_scan.py "AI writing" `
  --query "AI novel writing" `
  --query "worldbuilding writing assistant" `
  --query "LLM fiction writing" `
  --limit 10 `
  --candidate-limit 30 `
  --out work\writing-scan.json
```

### 搜 README

默认只搜 name 和 description，避免 README 里的泛词污染结果。如果结果太少，可以加 README：

```powershell
python .\forge-skill\scripts\github_scan.py "AI小说创作" --search-fields name,description,readme
```

### 调整相关性阈值

```powershell
python .\forge-skill\scripts\github_scan.py "AI小说创作" --min-relevance 4
```

阈值越高，候选越干净，但可能漏掉项目。

## 自动落地成新 skill

当 Codex 完成研究和融合后，先生成一个 JSON spec，例如：

```json
{
  "name": "ai-novel-architect",
  "title": "AI Novel Architect",
  "description": "Plan, critique, and generate long-form fiction workflows with worldbuilding, continuity checks, and revision loops.",
  "promise": "Turn a rough fiction idea into a structured, reviewable novel-production workflow.",
  "workflows": [
    "Clarify genre, audience, theme, and constraints.",
    "Build premise, cast, world rules, plot arc, and chapter plan.",
    "Draft scenes with continuity checks and revision passes."
  ],
  "inputs": [
    "User brief",
    "Existing notes or draft text"
  ],
  "outputs": [
    "World bible",
    "Outline",
    "Scene plan",
    "Revision checklist"
  ],
  "validation": [
    "Check continuity across characters, timeline, setting, and theme."
  ]
}
```

保存为：

```text
work\spec.json
```

然后执行：

```powershell
python .\forge-skill\scripts\materialize.py skill work\spec.json `
  --out-dir "$env:USERPROFILE\.codex\skills" `
  --validate-script "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py"
```

如果验证通过，会输出新 skill 路径和生成文件列表。

## 自动落地成项目骨架

示例 spec：

```json
{
  "name": "novel-lab",
  "title": "Novel Lab",
  "promise": "A local-first workspace for planning, drafting, and revising AI-assisted long-form fiction.",
  "target_users": [
    "Web novel authors",
    "Indie fiction writers"
  ],
  "workflows": [
    "Create story bible",
    "Generate chapter plan",
    "Draft scenes",
    "Run continuity review"
  ],
  "mvp": {
    "must_have": [
      "Story bible",
      "Chapter outline",
      "Draft workspace"
    ],
    "should_have": [
      "Continuity checker",
      "Export to Markdown"
    ],
    "later": [
      "Collaboration",
      "Publishing integrations"
    ],
    "out_of_scope": [
      "Full autonomous book generation without review"
    ]
  },
  "architecture": {
    "stack": [
      "TypeScript",
      "SQLite",
      "Local LLM adapter"
    ],
    "modules": [
      "story-bible",
      "outline-engine",
      "draft-runner",
      "continuity-checker"
    ]
  }
}
```

执行：

```powershell
python .\forge-skill\scripts\materialize.py project work\spec.json --out-dir work\generated-projects
```

会生成：

```text
generated-projects/
  novel-lab/
    README.md
    docs/
      blueprint.json
    src/
      .gitkeep
    tests/
      .gitkeep
    .gitignore
```

## 可选 GitHub Token

GitHub API 匿名请求有较低限流。建议设置 token：

```powershell
$env:GITHUB_TOKEN="your_token_here"
```

或者：

```powershell
$env:GH_TOKEN="your_token_here"
```

脚本会自动读取这两个环境变量。

注意：不要把真实 token 写进 README、JSON spec、脚本默认值或提交历史。ForgeSkill 只需要从本地环境变量读取 token，不需要把密钥保存到仓库里。

## 验证

验证本 skill：

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .\forge-skill
```

检查脚本帮助：

```powershell
python .\forge-skill\scripts\github_scan.py --help
python .\forge-skill\scripts\materialize.py --help
```

## 排错

### 结果太泛

提高相关性阈值：

```powershell
--min-relevance 4
```

或加更具体 query：

```powershell
--query "novel writing assistant" --query "worldbuilding AI"
```

### 结果太少

降低相关性阈值：

```powershell
--min-relevance 1
```

或扩大搜索字段：

```powershell
--search-fields name,description,readme
```

### GitHub 限流

设置 `GITHUB_TOKEN` 或稍后重试。

### 生成 skill 失败

检查：

- `name` 是否能转为小写 hyphen-case
- `description` 是否存在
- JSON 是否有效
- 目标目录是否已存在

如果确认要覆盖，给 `materialize.py` 加：

```powershell
--force
```

## 设计原则

- Stars 只是发现信号，不是质量结论。
- LLM rerank 必须优先判断真实领域匹配。
- 不复制被调研项目的代码、文档、品牌或资产，除非 license 允许且用户明确要求。
- 融合时保留强模式，舍弃噪声功能。
- 生成 skill 时保持 `SKILL.md` 精简，把复杂规则放入 `references/`，把确定性流程放入 `scripts/`。

## 安全与合规

- ForgeSkill 不要求把 GitHub token、OpenAI key 或其他密钥写入仓库。
- GitHub token 仅通过 `GITHUB_TOKEN` 或 `GH_TOKEN` 环境变量读取。
- 研究报告应区分事实证据和 Codex 的推断。
- 生成新项目时默认借鉴设计模式和工作流，不复制第三方代码、文档、品牌、图片或专有资产。
- 如需复用第三方代码，必须先检查 license，并在新项目中保留必要的 attribution 和 license notice。
