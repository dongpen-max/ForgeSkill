---
name: forge-skill
description: "Research and synthesize top-starred GitHub projects for a user-specified category using a two-stage process: GitHub candidate discovery plus LLM relevance reranking, then produce a fixed fusion blueprint, implementation plan, scaffold, project, or ZCode skill. Use when the user asks to scan, compare, summarize, learn from, fuse, combine, generate, scaffold, materialize, or create a new project or skill based on popular GitHub repositories in a domain such as AI novel writing, agent frameworks, dashboards, developer tools, or similar software categories."
---

# ForgeSkill

## Overview

Use this skill to turn a broad software idea into evidence-grounded output by surveying GitHub candidates, reranking them for domain fit, extracting strengths and gaps, and synthesizing a new project or ZCode skill.

## Workflow

1. **Define the target domain and output.**
   - Use the user's phrase as the domain.
   - If the user says "skill", create or update a ZCode skill.
   - If the user says "project", "app", "tool", or "repo", create a project blueprint or scaffold.
   - If the user says "generate", "scaffold", "materialize", "create", or "build it", plan to create files after the fusion blueprint.
   - If unclear, produce a research summary plus a concrete recommended build plan.

2. **Gather fresh GitHub evidence.**
   - Top-star results are time-sensitive; collect fresh data instead of relying on memory.
   - Use `scripts/github_scan.py` first. It defaults to searching repository names and descriptions to avoid giant unrelated projects that only mention a term in README.
   - Leave automatic query expansion enabled by default. It adds English GitHub search variants for non-English or broad topics.
   - The script collects a candidate pool for LLM reranking. Use `--limit` for the desired final count and `--candidate-limit` for the pre-LLM review pool.
   - The script applies a lightweight relevance score and a quality score. Use relevance to filter domain fit; use quality as a maintenance/reuse signal, not as an automatic winner.
   - For broad topics, still pass 2-5 explicit `--query` variants when you know strong synonyms or product terms. Use `--no-auto-expand` only for exact GitHub searches.
   - If results are sparse, rerun with `--search-fields name,description,readme`.
   - The script uses disk caching and concurrent fetching for performance. Use `--clear-cache` to refresh stale data.
   - Example:
   ```bash
   python <skill-dir>/scripts/github_scan.py "AI novel writing" --limit 10 --candidate-limit 30 --out work/ai-novel-github-scan.json
   ```

3. **Perform LLM relevance reranking.**
   - Inspect the generated JSON and Markdown report.
   - Use the "LLM Rerank Worksheet" section as the review checklist.
   - Select up to `--limit` repositories that best match the user's domain. Prefer true domain fit over raw stars, but preserve star order when relevance and quality are comparable.
   - Use quality score to spot healthier projects, but do not let it override a clearly better domain match.
   - Reject famous adjacent projects, awesome lists, personal profiles, political/news/content dumps, tutorials, or generic frameworks unless they are directly useful to the requested domain.
   - If results are thin or off-topic, rerun with better search variants, GitHub qualifiers, or targeted web search.
   - Prefer repository metadata, READMEs, docs, examples, issues, releases, and demos. Clone repositories only when implementation details are necessary.

4. **Analyze the selected repositories.**
   - Read `references/synthesis_rubric.md` when preparing the comparison, pros/cons, or synthesis.
   - Compare projects on product scope, architecture, extensibility, UX, data model, automation, maintenance health, ecosystem, licensing, and safety.
   - Distinguish evidence from inference. Cite repository URLs and the scan date.

5. **Synthesize the new output.**
   - Read `references/fusion_blueprint.md` and use its section order for the final deliverable unless the user requested a narrower artifact.
   - Preserve useful patterns and discard avoidable weaknesses.
   - Do not copy code, branding, docs, or assets from surveyed projects unless their licenses permit it and the user explicitly asks.
   - For a new ZCode skill, follow local skill conventions: concise `SKILL.md`, optional scripts/references/assets only when reusable, `agents/openai.yaml`, and validation with the skill creator validator if available.
   - For a new software project, create a small coherent architecture, feature set, roadmap, and scaffold only when the user asked for implementation.

6. **Materialize files when requested.**
   - Read `references/materialization_spec.md` before creating a generated skill or project scaffold.
   - Convert the fused concept into a JSON spec, then run `scripts/materialize.py`.
   - For a skill, default the output directory to the user's personal ZCode skills directory when the user has not specified another location.
   - For a project, default the output directory to the current workspace unless the user specifies another location.
   - Never overwrite an existing generated target unless the user asked for overwrite or `--force`.
   - Use `--dry-run` to preview what will be created before writing.

7. **Validate.**
   - Check that claims about repos are supported by gathered evidence.
   - For generated skills, run the skill validator.
   - For generated projects, run the relevant tests, lint, build, or smoke checks.

## Output Shape

Use `references/fusion_blueprint.md` as the default output structure unless the user requests a smaller artifact. The final answer should include the reranked selection rationale, not just the raw GitHub order.

## Resource Guide

- `scripts/github_scan.py`: Searches GitHub repositories with concurrent enrichment, disk caching, and configurable expansion rules. Produces JSON + Markdown evidence reports with star sparkbar, relevance and quality scores, and an LLM Rerank Worksheet.
- `scripts/materialize.py`: Creates a ZCode skill or project scaffold from a structured JSON spec. Supports `--dry-run` preview, optional Jinja2 templates, and spec validation.
- `references/synthesis_rubric.md`: Evaluation dimensions and synthesis rules for turning repository research into a differentiated project or skill.
- `references/fusion_blueprint.md`: Fixed final-output blueprint for reranked research, pros/cons, cross-project synthesis, and fused project or skill design.
- `references/materialization_spec.md`: JSON schema and commands for turning the fused concept into generated files.
- `forge-skill.toml`: Per-skill configuration file for defaults, expansion rules path, and GitHub token.
- `.forge-skill.toml`: Per-project configuration file (auto-detected from current directory).
