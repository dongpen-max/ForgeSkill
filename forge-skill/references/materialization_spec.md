# Materialization Spec

Use this reference when the user wants the synthesis turned into an actual Codex skill or project scaffold.

## Workflow

1. Finish the GitHub scan, LLM rerank, and fusion blueprint first.
2. Convert the fused concept into a JSON spec.
3. Run `scripts/materialize.py skill` or `scripts/materialize.py project`.
4. Validate generated skills with `quick_validate.py`.
5. For generated projects, run the relevant test, lint, build, or smoke command if the scaffold includes runnable code.

## Skill Command

```bash
python <skill-dir>/scripts/materialize.py skill work/spec.json --out-dir <codex-home>/skills --validate-script <codex-home>/skills/.system/skill-creator/scripts/quick_validate.py
```

Use `--force` only when intentionally overwriting a generated artifact.

## Project Command

```bash
python <skill-dir>/scripts/materialize.py project work/spec.json --out-dir work/generated-projects
```

## JSON Fields

Common fields:

- `name`: lowercase/hyphen preferred; the script normalizes it.
- `title`: human-facing title.
- `description`: trigger or project description.
- `promise`: one-sentence promise.
- `target_users`: list of users.
- `workflows` or `core_workflows`: list of primary workflows.
- `success_criteria`: list of checks that define success.
- `validation` or `validation_steps`: list of validation steps.

Skill-specific fields:

- `display_name`: optional UI display name.
- `short_description`: optional UI description.
- `default_prompt`: optional default prompt that should mention `$skill-name`.
- `inputs`: list of expected inputs.
- `outputs`: list of expected outputs.
- `resource_notes`: list of notes for bundled resources.
- `references`: list of objects with `path` and `content`, written under `references/`.
- `scripts`: list of objects with `path` and `content`, written under `scripts/`.

Project-specific fields:

- `mvp`: object with keys such as `must_have`, `should_have`, `later`, and `out_of_scope`.
- `architecture`: object with keys such as `stack`, `modules`, `data_model`, and `integrations`.
- `directories`: optional list of directories to create. Defaults to `src` and `tests`.
- `files`: list of objects with `path` and `content`, written inside the project.

## Minimal Skill Spec

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
  "inputs": ["User brief", "Existing notes or draft text"],
  "outputs": ["World bible", "Outline", "Scene plan", "Revision checklist"],
  "validation": ["Check continuity across characters, timeline, setting, and theme."]
}
```

## Minimal Project Spec

```json
{
  "name": "novel-lab",
  "title": "Novel Lab",
  "promise": "A local-first workspace for planning, drafting, and revising AI-assisted long-form fiction.",
  "target_users": ["Web novel authors", "Indie fiction writers"],
  "workflows": ["Create story bible", "Generate chapter plan", "Draft scenes", "Run continuity review"],
  "mvp": {
    "must_have": ["Story bible", "Chapter outline", "Draft workspace"],
    "should_have": ["Continuity checker", "Export to Markdown"],
    "later": ["Collaboration", "Publishing integrations"],
    "out_of_scope": ["Full autonomous book generation without review"]
  },
  "architecture": {
    "stack": ["TypeScript", "SQLite", "Local LLM adapter"],
    "modules": ["story-bible", "outline-engine", "draft-runner", "continuity-checker"]
  }
}
```
