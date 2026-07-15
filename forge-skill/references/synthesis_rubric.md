# Synthesis Rubric

Use this rubric after collecting GitHub evidence. Keep the final answer evidence-grounded and concise.

## Repository Evaluation

For each relevant repository, extract:

- Purpose: what problem it solves and who it appears to serve.
- Core workflow: the main user path or developer integration path.
- Strengths: concrete advantages visible in README, docs, code structure, demos, releases, or community signals.
- Weaknesses: missing features, narrow scope, stale maintenance, difficult setup, UX gaps, architectural limitations, unclear license, safety gaps, or weak docs.
- Reusable patterns: abstractions, workflows, architecture, prompt patterns, data models, plugin systems, evaluation loops, or onboarding ideas worth adapting.
- Non-reusable parts: project-specific assumptions, licensing-restricted code/assets, overfit implementation choices, and features outside the user's goal.
- Adoption posture: whether the scan marks it as `strong-reference`, `usable-reference`, `study-with-caution`, `study-patterns-only`, `reference-only`, or `review-carefully`, and why.

## Comparison Dimensions

Use these dimensions selectively:

- Product fit: clear target user, practical workflows, onboarding, examples, and end-to-end use cases.
- Technical design: modularity, dependency choices, data model, extension points, deployment path, and local/cloud assumptions.
- AI behavior: prompt/control surfaces, memory/context handling, evaluation, human review, failure recovery, and safety controls.
- UX: clarity, friction, defaults, export/import, collaboration, and visibility into intermediate steps.
- Ecosystem: integrations, API shape, plugin support, file formats, and interoperability.
- Maintenance: stars, forks, recent activity, issue volume, release cadence, archived status, and bus-factor hints.
- License and reuse: license clarity, compatibility, and whether ideas can be adapted without copying protected material.
- Scan scores and flags: use relevance as the domain-fit signal, quality as a maintenance/reuse signal, risk flags as prompts for closer review, and recommendation as an adoption posture. Treat them as aids for review, not as final truth.

## Synthesis Rules

- Favor patterns that appear in multiple strong projects or clearly solve the user's stated pain.
- Do not rank by stars alone; stars are a discovery signal, not proof of product quality.
- Do not rank by quality score alone; a healthy but adjacent project may be less useful than a narrower domain-specific project.
- Do not blindly reject every risky project; an archived or no-license repo may still reveal useful product ideas, but it should not be copied or used as the main implementation reference.
- Convert weaknesses into design requirements for the new project.
- Combine complementary strengths, not every feature. A strong synthesis should have a smaller coherent surface area than the union of all repos.
- Identify the "missing middle": what users still cannot do easily across the top projects.
- State uncertainty when evidence is thin or inferred from README-level information.

## Output Guidance

When creating a new Codex skill, produce:

- Trigger-focused frontmatter description.
- A short workflow that tells future Codex instances when to gather fresh evidence, what scripts to run, and how to validate.
- Scripts only for repeatable deterministic steps.
- References only for detailed judgment frameworks or domain-specific procedures.
- No extra README, installation guide, changelog, or process notes.

When creating a new software project, produce:

- Concept name and one-sentence promise.
- Target users and primary workflows.
- Feature set split into MVP, near-term, and later.
- Architecture and key modules.
- Data model or file layout when relevant.
- Risks, validation plan, and first implementation steps.
