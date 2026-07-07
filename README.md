# ForgeSkill

Synthesize top GitHub repositories into evidence-grounded Codex skills and project scaffolds.

一个 Codex skill：根据用户给出的软件方向，自动扫描 GitHub 高 star 项目，做 LLM 二次相关性重排，总结优缺点，并融合生成新的 Codex skill 或项目骨架。

典型用法：

```text
Use $forge-skill to research AI小说创作, summarize the top GitHub projects, and create a better new skill.
```

## 能做什么

- 自动把中文或宽泛主题扩展成更适合 GitHub 搜索的英文 query。
- 扫描 GitHub 候选项目，抓取 stars、forks、issues、license、topics、语言、活跃度、README 摘要。
- 给候选项目计算 `relevance_score` 和 `quality_score`。
- 生成 LLM rerank worksheet，让 Codex 从候选池里选出真正相关的 top 项目。
- 按固定融合蓝图输出：研究快照、项目优缺点、跨项目模式、新概念、MVP、架构、实施计划、证据附录。
- 在用户要求时，把融合结果落地成：
  - 新 Codex skill
  - 新项目 scaffold

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

## 上传到 GitHub

如果你已经有一个空 GitHub 仓库，例如：

```text
https://github.com/YOUR_NAME/ForgeSkill.git
```

在本仓库根目录执行：

```powershell
git remote add origin https://github.com/YOUR_NAME/ForgeSkill.git
git push -u origin main
```

如果你安装了 GitHub CLI，也可以直接创建并推送：

```powershell
gh auth login
gh repo create ForgeSkill --private --source . --remote origin --push
```

想公开发布时，把 `--private` 改成 `--public`。

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
