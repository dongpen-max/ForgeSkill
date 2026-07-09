#!/usr/bin/env python3
"""Materialize a fused GitHub research concept into a skill or project scaffold."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from jinja2 import Environment, BaseLoader

    HAS_JINJA = True
except ImportError:
    HAS_JINJA = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(value: str, *, fallback: str = "generated-artifact") -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:63] or fallback


def titleize(value: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[-_\s]+", value.strip()) if part)


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def as_text_list(value: Any) -> list[str]:
    return [str(item).strip() for item in ensure_list(value) if str(item).strip()]


def load_spec(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("spec must be a JSON object")
    return payload


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip() + '"'


def markdown_list(items: list[str], *, fallback: str = "TBD") -> str:
    if not items:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in items)


def numbered_list(items: list[str], *, fallback: str = "TBD") -> str:
    if not items:
        return f"1. {fallback}"
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, 1))


def normalize_name(spec: dict[str, Any]) -> str:
    raw = spec.get("name") or spec.get("title") or spec.get("concept_name")
    if not raw:
        raise ValueError("spec requires name, title, or concept_name")
    return slugify(str(raw))


def short_description(spec: dict[str, Any], *, max_len: int = 96) -> str:
    for key in ("short_description", "promise", "description"):
        value = str(spec.get(key) or "").strip()
        if value:
            return value[:max_len].rstrip()
    return "Generated from a GitHub research synthesis."


def commonpath_contains(base: Path, target: Path) -> bool:
    try:
        return os.path.commonpath([str(base), str(target)]) == str(base)
    except ValueError:
        return False


def display_path(path: Path | str) -> str:
    text = os.path.normpath(str(path))
    if text.startswith("\\\\?\\"):
        return text[4:]
    return text


def resolve_target(base_dir: Path, name: str) -> Path:
    base = base_dir.resolve()
    target = (base / name).resolve()
    if not commonpath_contains(base, target):
        raise ValueError(f"target path escapes output directory: {target}")
    return target


def safe_relative_path(raw_path: str) -> Path:
    if not raw_path or raw_path.strip() in {".", "/"}:
        raise ValueError("file path must not be empty")
    if re.match(r"^[a-zA-Z]:", raw_path) or raw_path.startswith(("/", "\\")):
        raise ValueError(f"absolute file paths are not allowed in spec: {raw_path}")
    posix = PurePosixPath(raw_path.replace("\\", "/"))
    if any(part in {"", ".", ".."} for part in posix.parts):
        raise ValueError(f"path traversal is not allowed in spec: {raw_path}")
    return Path(*posix.parts)


# ---------------------------------------------------------------------------
# Jinja2 template rendering (optional)
# ---------------------------------------------------------------------------

def _jinja_env() -> Environment:
    """Get a Jinja2 Environment with basic filters."""
    env = Environment(loader=BaseLoader(), autoescape=False)
    env.filters["slugify"] = slugify
    env.filters["titleize"] = titleize
    env.filters["yaml_quote"] = yaml_quote
    env.filters["markdown_list"] = markdown_list
    env.filters["numbered_list"] = numbered_list
    return env


def render_template(template_text: str, spec: dict[str, Any]) -> str:
    """Render a Jinja2 template string with spec vars."""
    if not HAS_JINJA:
        # Fallback: simple variable substitution
        result = template_text
        for key, value in _flat_spec(spec).items():
            result = result.replace(f"{{{{ {key} }}}}", str(value))
            result = result.replace(f"{{{{ {key}|slugify }}}}", slugify(str(value)))
            result = result.replace(f"{{{{ {key}|titleize }}}}", titleize(str(value)))
        return result
    env = _jinja_env()
    template = env.from_string(template_text)
    return template.render(**spec)


def _flat_spec(spec: dict[str, Any], prefix: str = "") -> dict[str, str]:
    """Flatten spec dict for simple string substitution."""
    result: dict[str, str] = {}
    for key, value in spec.items():
        full_key = f"{prefix}{key}" if prefix else key
        if isinstance(value, dict):
            result.update(_flat_spec(value, prefix=f"{full_key}_"))
        elif isinstance(value, list):
            result[full_key] = json.dumps(value, ensure_ascii=False)
        else:
            result[full_key] = str(value)
    return result


# ---------------------------------------------------------------------------
# File writing
# ---------------------------------------------------------------------------

_DryRunFiles: list[dict[str, str]] = []


def write_text(
    target_root: Path,
    relative_path: str,
    content: str,
    *,
    force: bool,
    dry_run: bool,
    written: list[str],
) -> None:
    rel = safe_relative_path(relative_path)
    path = (target_root / rel).resolve()
    if not commonpath_contains(target_root.resolve(), path):
        raise ValueError(f"refusing to write outside target root: {path}")

    if dry_run:
        _DryRunFiles.append({"path": display_path(path), "size": len(content), "preview": content[:500]})
        written.append(display_path(path))
        return

    if path.exists() and not force:
        raise FileExistsError(f"file already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    written.append(display_path(path))


# ---------------------------------------------------------------------------
# Section rendering helpers
# ---------------------------------------------------------------------------

def section_from_mapping(title: str, mapping: dict[str, Any]) -> str:
    lines = [f"## {title}", ""]
    if not mapping:
        lines.append("- TBD")
        return "\n".join(lines)
    for key, value in mapping.items():
        label = str(key).replace("_", " ").title()
        lines.append(f"### {label}")
        lines.append("")
        lines.append(markdown_list(as_text_list(value)))
        lines.append("")
    return "\n".join(lines).rstrip()


# ---------------------------------------------------------------------------
# Skill materialization
# ---------------------------------------------------------------------------

def render_skill_md(name: str, spec: dict[str, Any]) -> str:
    title = str(spec.get("title") or titleize(name))
    description = str(spec.get("description") or spec.get("promise") or short_description(spec)).strip()
    overview = str(spec.get("overview") or spec.get("promise") or description).strip()
    workflows = as_text_list(spec.get("workflows") or spec.get("core_workflows"))
    inputs = as_text_list(spec.get("inputs"))
    outputs = as_text_list(spec.get("outputs"))
    validation = as_text_list(spec.get("validation") or spec.get("validation_steps"))
    resources = as_text_list(spec.get("resource_notes"))

    # Check if spec embeds a template override
    custom_template = spec.get("_skel_skill_md_template")
    if custom_template:
        return render_template(str(custom_template), spec)

    return f"""---
name: {name}
description: {yaml_quote(description)}
---

# {title}

## Overview

{overview}

## Workflow

{numbered_list(workflows)}

## Inputs

{markdown_list(inputs, fallback="Use the user's request and any referenced artifacts as input.")}

## Outputs

{markdown_list(outputs, fallback="Produce the requested artifact with concise validation notes.")}

## Resources

{markdown_list(resources, fallback="Load bundled references only when they are directly relevant.")}

## Validation

{markdown_list(validation, fallback="Check the result against the user's request and run relevant tests or validators when available.")}
"""


def render_openai_yaml(name: str, spec: dict[str, Any]) -> str:
    display_name = str(spec.get("display_name") or spec.get("title") or titleize(name)).strip()
    description = short_description(spec)
    default_prompt = str(
        spec.get("default_prompt")
        or f"Use ${name} to {description[0].lower() + description[1:] if description else 'complete the requested task'}."
    ).strip()
    return "\n".join([
        "interface:",
        f"  display_name: {yaml_quote(display_name)}",
        f"  short_description: {yaml_quote(description)}",
        f"  default_prompt: {yaml_quote(default_prompt)}",
        "",
    ])


def resource_entries(spec: dict[str, Any], key: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for item in ensure_list(spec.get(key)):
        if isinstance(item, dict):
            path = str(item.get("path") or "").strip()
            content = str(item.get("content") or "").strip()
            if path and content:
                entries.append({"path": path, "content": content})
        elif isinstance(item, str) and item.strip():
            filename = slugify(item, fallback="note") + ".md"
            entries.append({"path": filename, "content": item.strip()})
    return entries


def materialize_skill(
    spec: dict[str, Any],
    out_dir: Path,
    *,
    force: bool,
    dry_run: bool,
    validate_script: Path | None,
) -> dict[str, Any]:
    name = normalize_name(spec)
    target = resolve_target(out_dir, name)

    if not dry_run:
        if target.exists() and any(target.iterdir()) and not force:
            raise FileExistsError(f"target skill directory already exists and is not empty: {target}")
        target.mkdir(parents=True, exist_ok=True)

    written: list[str] = []

    write_text(target, "SKILL.md", render_skill_md(name, spec), force=force, dry_run=dry_run, written=written)
    write_text(target, "agents/openai.yaml", render_openai_yaml(name, spec), force=force, dry_run=dry_run, written=written)

    for entry in resource_entries(spec, "references"):
        write_text(target, f"references/{entry['path']}", entry["content"], force=force, dry_run=dry_run, written=written)
    for entry in resource_entries(spec, "scripts"):
        write_text(target, f"scripts/{entry['path']}", entry["content"], force=force, dry_run=dry_run, written=written)

    validation: dict[str, Any] | None = None
    if validate_script and not dry_run:
        result = subprocess.run(
            [sys.executable, str(validate_script), str(target)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        validation = {
            "command": [sys.executable, str(validate_script), str(target)],
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
        if result.returncode != 0:
            raise RuntimeError(f"generated skill failed validation: {validation}")

    return {"kind": "skill", "name": name, "path": display_path(target) if not dry_run else "(dry-run)", "files": written, "validation": validation}


# ---------------------------------------------------------------------------
# Project materialization
# ---------------------------------------------------------------------------

def render_project_readme(name: str, spec: dict[str, Any]) -> str:
    title = str(spec.get("title") or titleize(name)).strip()
    promise = str(spec.get("promise") or spec.get("description") or "Generated project scaffold.").strip()
    workflows = as_text_list(spec.get("workflows") or spec.get("core_workflows"))
    users = as_text_list(spec.get("target_users"))
    success = as_text_list(spec.get("success_criteria"))
    mvp = spec.get("mvp") if isinstance(spec.get("mvp"), dict) else {}
    architecture = spec.get("architecture") if isinstance(spec.get("architecture"), dict) else {}

    # Check for Jinja2 template override
    custom_template = spec.get("_skel_project_readme_template")
    if custom_template:
        return render_template(str(custom_template), spec)

    return "\n\n".join([
        f"# {title}",
        promise,
        "## Target Users\n\n" + markdown_list(users),
        "## Core Workflows\n\n" + numbered_list(workflows),
        section_from_mapping("MVP Scope", mvp),
        section_from_mapping("Architecture", architecture),
        "## Success Criteria\n\n" + markdown_list(success),
        "## Validation\n\n" + markdown_list(as_text_list(spec.get("validation") or spec.get("validation_steps"))),
    ])


def render_blueprint(spec: dict[str, Any]) -> str:
    return json.dumps(spec, indent=2, ensure_ascii=False)


def materialize_project(
    spec: dict[str, Any],
    out_dir: Path,
    *,
    force: bool,
    dry_run: bool,
) -> dict[str, Any]:
    name = normalize_name(spec)
    target = resolve_target(out_dir, name)

    if not dry_run:
        if target.exists() and any(target.iterdir()) and not force:
            raise FileExistsError(f"target project directory already exists and is not empty: {target}")
        target.mkdir(parents=True, exist_ok=True)

    written: list[str] = []

    write_text(target, "README.md", render_project_readme(name, spec), force=force, dry_run=dry_run, written=written)
    write_text(target, "docs/blueprint.json", render_blueprint(spec), force=force, dry_run=dry_run, written=written)
    write_text(target, ".gitignore", "__pycache__/\n.env\nnode_modules/\ndist/\nbuild/\n", force=force, dry_run=dry_run, written=written)

    directories = as_text_list(spec.get("directories")) or ["src", "tests"]
    for directory in directories:
        rel = safe_relative_path(directory)
        marker = str(rel / ".gitkeep")
        write_text(target, marker, "", force=force, dry_run=dry_run, written=written)

    for entry in resource_entries(spec, "files"):
        write_text(target, entry["path"], entry["content"], force=force, dry_run=dry_run, written=written)

    return {"kind": "project", "name": name, "path": display_path(target) if not dry_run else "(dry-run)", "files": written, "validation": None}


# ---------------------------------------------------------------------------
# Spec validation
# ---------------------------------------------------------------------------

def validate_spec(spec: dict[str, Any], kind: str) -> list[str]:
    """Validate a materialization spec and return a list of issues."""
    issues: list[str] = []

    name = spec.get("name") or spec.get("title") or spec.get("concept_name")
    if not name:
        issues.append("Missing required field: name, title, or concept_name")
    elif not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9 _-]*$", str(name)):
        issues.append(f"name '{name}' should start with alphanumeric and contain only alphanumeric, space, hyphen, underscore")

    if not spec.get("description") and not spec.get("promise"):
        issues.append("Missing description or promise")

    if kind == "skill":
        if not spec.get("workflows") and not spec.get("core_workflows"):
            issues.append("Skill spec should include workflows or core_workflows")
    elif kind == "project":
        if not spec.get("mvp"):
            issues.append("Project spec should include mvp scope")

    # Check for absolute paths in files
    for entry in ensure_list(spec.get("files")):
        if isinstance(entry, dict):
            path = entry.get("path", "")
            if path.startswith("/") or re.match(r"^[a-zA-Z]:", path):
                issues.append(f"File path '{path}' is absolute; use relative paths")

    # Check for path traversal
    for entry in ensure_list(spec.get("files")):
        if isinstance(entry, dict):
            path = entry.get("path", "")
            if ".." in path.split("/") or ".." in path.split("\\"):
                issues.append(f"File path '{path}' contains '..' traversal")

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize a fused concept into a skill or project scaffold."
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview files that would be created without writing.")
    parser.add_argument("--validate-only", action="store_true", help="Only validate the spec JSON without creating files.")

    subparsers = parser.add_subparsers(dest="kind", required=True)

    skill = subparsers.add_parser("skill", help="Create a ZCode skill from a JSON spec.")
    skill.add_argument("spec", type=Path, help="Path to materialization spec JSON.")
    skill.add_argument("--out-dir", type=Path, required=True, help="Directory where the skill folder will be created.")
    skill.add_argument("--force", action="store_true", help="Overwrite existing files in the target folder.")
    skill.add_argument("--validate-script", type=Path, help="Path to skill-creator quick_validate.py.")
    skill.add_argument("--dry-run", action="store_true", dest="skill_dry_run", help=argparse.SUPPRESS)
    skill.add_argument("--validate-only", action="store_true", dest="skill_validate_only", help=argparse.SUPPRESS)

    project = subparsers.add_parser("project", help="Create a project scaffold from a JSON spec.")
    project.add_argument("spec", type=Path, help="Path to materialization spec JSON.")
    project.add_argument("--out-dir", type=Path, required=True, help="Directory where the project folder will be created.")
    project.add_argument("--force", action="store_true", help="Overwrite existing files in the target folder.")
    project.add_argument("--dry-run", action="store_true", dest="project_dry_run", help=argparse.SUPPRESS)
    project.add_argument("--validate-only", action="store_true", dest="project_validate_only", help=argparse.SUPPRESS)

    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    spec = load_spec(args.spec)

    # Consolidate dry-run and validate-only from top-level or subcommand
    dry_run = getattr(args, "dry_run", False) or getattr(args, "skill_dry_run", False) or getattr(args, "project_dry_run", False)
    validate_only = getattr(args, "validate_only", False) or getattr(args, "skill_validate_only", False) or getattr(args, "project_validate_only", False)

    # Validate spec
    issues = validate_spec(spec, args.kind)
    if issues:
        print("Spec validation issues:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        if validate_only:
            return 1 if issues else 0
        print("Aborting due to validation issues. Use --validate-only to check without creating.", file=sys.stderr)
        return 1

    if validate_only:
        print("Spec is valid.")
        return 0

    if dry_run:
        print("--- DRY RUN: no files will be written ---")

    if args.kind == "skill":
        result = materialize_skill(
            spec, args.out_dir,
            force=args.force, dry_run=dry_run,
            validate_script=args.validate_script,
        )
    else:
        result = materialize_project(
            spec, args.out_dir,
            force=args.force, dry_run=dry_run,
        )

    if dry_run and _DryRunFiles:
        print("\nFiles that would be created:")
        for f in _DryRunFiles:
            preview = f["preview"].replace("\n", "\\n")
            print(f"  {f['path']}  ({f['size']} bytes)  preview: {preview[:80]}")
        print()

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
