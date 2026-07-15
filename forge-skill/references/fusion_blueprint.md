# Fusion Blueprint

Use this section order for the final deliverable after GitHub candidate discovery and LLM reranking. Keep claims tied to evidence from the scan, README excerpts, docs, or inspected code.

## 1. Research Snapshot

Include:

- Domain and user intent.
- Scan date/time.
- Query variants used.
- Candidate count and final selected count.
- Any important caveats, such as sparse results, noisy GitHub search, unclear licenses, or README-only evidence.

## 2. LLM Reranked Top Projects

Provide a table with:

- Final rank.
- Repository and URL.
- Stars.
- Recommendation and risk flags from the scan.
- Why it was selected.
- Main reusable idea.
- Main caveat.

When rejecting high-star candidates, briefly list the most important exclusions and why they were excluded.

## 3. Project-by-Project Notes

For each selected repository, summarize:

- What it does.
- Strengths.
- Weaknesses.
- Reusable patterns.
- What not to copy or overfit.

## 4. Cross-Project Pattern Synthesis

Summarize:

- Recurring strengths across the strongest projects.
- Recurring gaps or pain points.
- Missing middle: the useful product or skill that does not yet seem well served.
- Design principles for the fused output.

## 5. Fused Concept

Define:

- Name.
- One-sentence promise.
- Target users.
- Differentiator.
- Core workflows.
- Success criteria.

## 6. MVP Scope

Split scope into:

- Must have.
- Should have.
- Later.
- Explicitly out of scope.

## 7. Architecture Or Skill Design

For a software project, include:

- Proposed stack.
- Key modules.
- Data model or file layout.
- Integration points.
- Testing and validation plan.

For a Codex skill, include:

- Skill name.
- Trigger-focused description.
- SKILL.md workflow outline.
- Scripts to bundle.
- References to bundle.
- Validation steps.

## 8. Implementation Plan

Provide:

- First 3-7 implementation steps.
- Files to create or modify.
- Tests or smoke checks.
- Risks and mitigations.
- Materialization target when the user asked for files: `skill` or `project`.
- JSON spec path to pass into `scripts/materialize.py`.

## 9. Evidence Appendix

Include:

- Links to selected repositories.
- Link or path to the generated JSON/Markdown scan report when available.
- Notes about uncertainty or assumptions.
