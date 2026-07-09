"""Tests for materialize.py — rendering, spec validation, and file generation."""

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "forge-skill" / "scripts"))

from materialize import (
    slugify,
    titleize,
    normalize_name,
    short_description,
    safe_relative_path,
    resolve_target,
    render_skill_md,
    render_openai_yaml,
    render_project_readme,
    render_blueprint,
    resource_entries,
    validate_spec,
    as_text_list,
    markdown_list,
    numbered_list,
)


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_basic(self):
        assert slugify("Hello World") == "hello-world"

    def test_long(self):
        long_str = "a" * 100
        result = slugify(long_str)
        assert len(result) == 63
        assert result == "a" * 63

    def test_empty_fallback(self):
        assert slugify("", fallback="my-fallback") == "my-fallback"


# ---------------------------------------------------------------------------
# titleize
# ---------------------------------------------------------------------------

class TestTitleize:
    def test_snake_case(self):
        assert titleize("hello_world") == "Hello World"

    def test_kebab_case(self):
        assert titleize("hello-world") == "Hello World"

    def test_mixed(self):
        assert titleize("hello  world") == "Hello World"

    def test_single_word(self):
        assert titleize("hello") == "Hello"


# ---------------------------------------------------------------------------
# normalize_name
# ---------------------------------------------------------------------------

class TestNormalizeName:
    def test_from_name(self):
        assert normalize_name({"name": "Hello World"}) == "hello-world"

    def test_from_title(self):
        assert normalize_name({"title": "Hello World"}) == "hello-world"

    def test_from_concept_name(self):
        assert normalize_name({"concept_name": "Hello World"}) == "hello-world"

    def test_missing(self):
        with pytest.raises(ValueError):
            normalize_name({})


# ---------------------------------------------------------------------------
# short_description
# ---------------------------------------------------------------------------

class TestShortDescription:
    def test_from_short_description(self):
        spec = {"short_description": "A great tool"}
        assert short_description(spec) == "A great tool"

    def test_from_promise(self):
        spec = {"promise": "A promise"}
        assert short_description(spec) == "A promise"

    def test_from_description(self):
        spec = {"description": "A description"}
        assert short_description(spec) == "A description"

    def test_truncated(self):
        spec = {"description": "x" * 200}
        result = short_description(spec)
        assert len(result) <= 96

    def test_fallback(self):
        spec = {}
        result = short_description(spec)
        assert "Generated" in result


# ---------------------------------------------------------------------------
# safe_relative_path
# ---------------------------------------------------------------------------

class TestSafeRelativePath:
    def test_normal(self):
        assert safe_relative_path("src/main.py") == Path("src/main.py")

    def test_raises_on_absolute_windows(self):
        with pytest.raises(ValueError):
            safe_relative_path("C:\\windows\\file.txt")

    def test_raises_on_absolute_unix(self):
        with pytest.raises(ValueError):
            safe_relative_path("/etc/passwd")

    def test_raises_on_empty(self):
        with pytest.raises(ValueError):
            safe_relative_path("")

    def test_raises_on_dot(self):
        with pytest.raises(ValueError):
            safe_relative_path(".")

    def test_raises_on_traversal(self):
        with pytest.raises(ValueError):
            safe_relative_path("../escape")

    def test_normalizes_backslashes(self):
        assert safe_relative_path("src\\main.py") == Path("src/main.py")


# ---------------------------------------------------------------------------
# resolve_target
# ---------------------------------------------------------------------------

class TestResolveTarget:
    def test_normal(self, tmp_path: Path):
        result = resolve_target(tmp_path, "my-skill")
        assert result == (tmp_path / "my-skill").resolve()

    def test_raises_on_escape(self, tmp_path: Path):
        with pytest.raises(ValueError):
            resolve_target(tmp_path, "../escape")


# ---------------------------------------------------------------------------
# as_text_list
# ---------------------------------------------------------------------------

class TestAsTextList:
    def test_list(self):
        assert as_text_list(["a", "b"]) == ["a", "b"]

    def test_single_string(self):
        assert as_text_list("hello") == ["hello"]

    def test_none(self):
        assert as_text_list(None) == []

    def test_strips_whitespace(self):
        assert as_text_list(["  a  ", "  b  "]) == ["a", "b"]

    def test_filters_empty(self):
        assert as_text_list(["a", "", "b"]) == ["a", "b"]


# ---------------------------------------------------------------------------
# markdown_list, numbered_list
# ---------------------------------------------------------------------------

class TestMarkdownList:
    def test_basic(self):
        result = markdown_list(["a", "b"])
        assert "- a" in result
        assert "- b" in result

    def test_empty_fallback(self):
        result = markdown_list([], fallback="nothing")
        assert "nothing" in result


class TestNumberedList:
    def test_basic(self):
        result = numbered_list(["a", "b"])
        assert "1. a" in result
        assert "2. b" in result

    def test_empty_fallback(self):
        result = numbered_list([], fallback="nothing")
        assert "1. nothing" in result


# ---------------------------------------------------------------------------
# render_skill_md
# ---------------------------------------------------------------------------

class TestRenderSkillMd:
    def test_basic(self):
        spec = {
            "name": "my-skill",
            "title": "My Skill",
            "description": "A test skill",
            "workflows": ["Do A", "Do B"],
            "inputs": ["User request"],
            "outputs": ["Result"],
        }
        text = render_skill_md("my-skill", spec)
        assert "name: my-skill" in text
        assert "My Skill" in text
        assert "Do A" in text
        assert "User request" in text
        assert "Validation" in text

    def test_minimal(self):
        spec = {"name": "minimal-skill"}
        text = render_skill_md("minimal-skill", spec)
        assert "name: minimal-skill" in text

    def test_custom_template(self):
        spec = {
            "name": "custom-skill",
            "_skel_skill_md_template": "# Custom: {{ name }}\n\nDescription: {{ description }}",
            "description": "custom desc",
        }
        text = render_skill_md("custom-skill", spec)
        assert "Custom: custom-skill" in text
        assert "custom desc" in text


# ---------------------------------------------------------------------------
# render_openai_yaml
# ---------------------------------------------------------------------------

class TestRenderOpenaiYaml:
    def test_basic(self):
        result = render_openai_yaml("my-skill", {"title": "My Skill", "description": "A test"})
        assert "display_name" in result
        assert "short_description" in result
        assert "default_prompt" in result

    def test_with_display_name(self):
        result = render_openai_yaml("my-skill", {"display_name": "My Skill", "promise": "promise text"})
        assert "My Skill" in result


# ---------------------------------------------------------------------------
# render_project_readme
# ---------------------------------------------------------------------------

class TestRenderProjectReadme:
    def test_basic(self):
        spec = {
            "name": "my-project",
            "title": "My Project",
            "promise": "A great project",
            "target_users": ["Developers"],
            "workflows": ["Build", "Deploy"],
            "mvp": {"must_have": ["Core"], "should_have": ["Extras"]},
            "architecture": {"stack": ["Python"]},
        }
        text = render_project_readme("my-project", spec)
        assert "My Project" in text
        assert "A great project" in text
        assert "Developers" in text
        assert "Core" in text
        assert "Python" in text

    def test_minimal(self):
        spec = {"name": "minimal"}
        text = render_project_readme("minimal", spec)
        assert "Minimal" in text


# ---------------------------------------------------------------------------
# render_blueprint
# ---------------------------------------------------------------------------

class TestRenderBlueprint:
    def test_basic(self):
        spec = {"name": "test", "key": "value"}
        result = json.loads(render_blueprint(spec))
        assert result["name"] == "test"
        assert result["key"] == "value"


# ---------------------------------------------------------------------------
# resource_entries
# ---------------------------------------------------------------------------

class TestResourceEntries:
    def test_dict_entries(self):
        spec = {
            "references": [
                {"path": "guide.md", "content": "# Guide"},
            ]
        }
        entries = resource_entries(spec, "references")
        assert len(entries) == 1
        assert entries[0]["path"] == "guide.md"

    def test_string_entries(self):
        spec = {
            "scripts": ["print('hello')"],
        }
        entries = resource_entries(spec, "scripts")
        assert len(entries) == 1
        assert entries[0]["path"].endswith(".md")

    def test_empty(self):
        assert resource_entries({}, "references") == []


# ---------------------------------------------------------------------------
# validate_spec
# ---------------------------------------------------------------------------

class TestValidateSpec:
    def test_valid_skill(self):
        spec = {
            "name": "my-skill",
            "description": "A skill",
            "workflows": ["Do A"],
        }
        issues = validate_spec(spec, "skill")
        assert len(issues) == 0

    def test_missing_name(self):
        issues = validate_spec({}, "skill")
        assert any("name" in i.lower() for i in issues)

    def test_missing_description(self):
        issues = validate_spec({"name": "test"}, "skill")
        assert any("description" in i.lower() for i in issues)

    def test_valid_project(self):
        spec = {
            "name": "my-project",
            "description": "A project",
            "mvp": {"must_have": ["Core"]},
        }
        issues = validate_spec(spec, "project")
        assert len(issues) == 0

    def test_project_without_mvp(self):
        spec = {"name": "my-project", "description": "desc"}
        issues = validate_spec(spec, "project")
        assert any("mvp" in i.lower() for i in issues)

    def test_absolute_path_in_files(self):
        spec = {
            "name": "test",
            "description": "desc",
            "workflows": ["A"],
            "files": [{"path": "/etc/passwd", "content": "evil"}],
        }
        issues = validate_spec(spec, "skill")
        assert any("absolute" in i.lower() for i in issues)

    def test_path_traversal_in_files(self):
        spec = {
            "name": "test",
            "description": "desc",
            "workflows": ["A"],
            "files": [{"path": "../../escape.txt", "content": "evil"}],
        }
        issues = validate_spec(spec, "skill")
        assert any("traversal" in i.lower() for i in issues)


# ---------------------------------------------------------------------------
# Integration: materialize_skill with dry-run
# ---------------------------------------------------------------------------

class TestMaterializeDryRun:
    def test_dry_run_skill(self, tmp_path: Path):
        """Test that dry-run mode works without creating files."""
        from materialize import materialize_skill

        spec = {
            "name": "dry-run-skill",
            "title": "Dry Run Skill",
            "description": "A dry run test",
            "workflows": ["Test workflow"],
        }

        result = materialize_skill(
            spec, tmp_path,
            force=False, dry_run=True,
            validate_script=None,
        )

        assert result["kind"] == "skill"
        assert result["name"] == "dry-run-skill"
        assert len(result["files"]) > 0
        # Files should NOT actually exist on disk
        for file_path in result["files"]:
            assert not Path(file_path).exists()

    def test_dry_run_project(self, tmp_path: Path):
        """Test that project dry-run mode works."""
        from materialize import materialize_project

        spec = {
            "name": "dry-run-project",
            "title": "Dry Run Project",
            "description": "A project dry run",
            "workflows": ["Build"],
        }

        result = materialize_project(
            spec, tmp_path,
            force=False, dry_run=True,
        )

        assert result["kind"] == "project"
        assert result["name"] == "dry-run-project"
        for file_path in result["files"]:
            assert not Path(file_path).exists()
