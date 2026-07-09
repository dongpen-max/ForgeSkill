"""Tests for github_scan.py — core scoring and utility functions."""

import sys
import pytest

# Ensure the scripts directory is on sys.path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent / "forge-skill" / "scripts"))

# Import functions from github_scan (they are at module level)
from github_scan import (
    slugify,
    dedupe,
    contains_non_ascii,
    auto_expand_queries,
    focus_terms,
    words,
    strip_qualifiers,
    query_terms,
    field_tokens,
    phrase_variants,
    relevance_score,
    quality_score,
    activity_label,
    days_since,
    safe_license,
    normalize_query,
    DEFAULT_TOPIC_EXPANSIONS,
    DEFAULT_FOCUS_RULES,
)

# We need to call _ensure_rules_loaded to set up globals
import github_scan as gs
gs._loaded_expansions = gs.DEFAULT_TOPIC_EXPANSIONS
gs._loaded_focus_rules = gs.DEFAULT_FOCUS_RULES


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_basic(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_chars(self):
        assert slugify("AI novel writing!") == "ai-novel-writing"

    def test_chinese(self):
        assert slugify("AI小说创作") == "ai"

    def test_empty_fallback(self):
        assert slugify("!!") == "github-scan"

    def test_trailing_dashes(self):
        assert slugify("  test  ") == "test"

    def test_mixed(self):
        assert slugify("Hello, World! 123") == "hello-world-123"


# ---------------------------------------------------------------------------
# dedupe
# ---------------------------------------------------------------------------

class TestDedupe:
    def test_no_dupes(self):
        assert dedupe(["a", "b", "c"]) == ["a", "b", "c"]

    def test_with_dupes(self):
        assert dedupe(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]

    def test_case_insensitive(self):
        result = dedupe(["Hello", "hello", "HELLO"])
        assert len(result) == 1
        assert result[0].lower() == "hello"

    def test_empty_strings(self):
        assert dedupe(["a", "", "  ", "b"]) == ["a", "b"]

    def test_whitespace_normalized(self):
        result = dedupe(["hello  world", "hello world"])
        assert len(result) == 1


# ---------------------------------------------------------------------------
# contains_non_ascii
# ---------------------------------------------------------------------------

class TestContainsNonAscii:
    def test_ascii_only(self):
        assert contains_non_ascii("hello world") is False

    def test_with_chinese(self):
        assert contains_non_ascii("AI小说创作") is True

    def test_with_accents(self):
        assert contains_non_ascii("café") is True

    def test_mixed(self):
        assert contains_non_ascii("AI agent 框架") is True

    def test_empty(self):
        assert contains_non_ascii("") is False


# ---------------------------------------------------------------------------
# auto_expand_queries
# ---------------------------------------------------------------------------

class TestAutoExpandQueries:
    def test_novel_expansion(self):
        queries = auto_expand_queries("AI小说创作", [], 8)
        assert len(queries) > 0
        # Should include novel/fiction related queries
        assert any("novel" in q for q in queries) or any("fiction" in q for q in queries)

    def test_agent_expansion(self):
        queries = auto_expand_queries("agent framework", [], 8)
        assert len(queries) > 0
        assert any("agent" in q for q in queries)

    def test_dashboard_expansion(self):
        queries = auto_expand_queries("数据看板", [], 8)
        assert len(queries) > 0

    def test_no_expansion_for_known(self):
        queries = auto_expand_queries("AI novel writing", ["AI novel writing"], 8)
        assert len(queries) >= 1

    def test_max_variants(self):
        queries = auto_expand_queries("AI小说创作", [], 3)
        assert len(queries) <= 3

    def test_non_ascii_fallback(self):
        queries = auto_expand_queries("一些奇怪的主题", [], 8)
        # Should have fallback AI/LLM queries
        assert any("AI" in q for q in queries)


# ---------------------------------------------------------------------------
# focus_terms
# ---------------------------------------------------------------------------

class TestFocusTerms:
    def test_novel_focus(self):
        terms = focus_terms("AI小说创作", ["AI novel writing"])
        assert len(terms) > 0
        assert any(t in terms for t in ["novel", "fiction", "story"])

    def test_agent_focus(self):
        terms = focus_terms("agent framework", ["AI agent"])
        assert "agent" in terms

    def test_no_match(self):
        terms = focus_terms("something unrelated", [])
        assert terms == []


# ---------------------------------------------------------------------------
# words
# ---------------------------------------------------------------------------

class TestWords:
    def test_basic(self):
        assert words("Hello World") == ["hello", "world"]

    def test_with_punctuation(self):
        assert words("Hello, World!") == ["hello", "world"]

    def test_none(self):
        assert words(None) == []

    def test_empty(self):
        assert words("") == []

    def test_numbers(self):
        assert words("test123") == ["test123"]


# ---------------------------------------------------------------------------
# strip_qualifiers
# ---------------------------------------------------------------------------

class TestStripQualifiers:
    def test_simple(self):
        assert strip_qualifiers("hello world") == "hello world"

    def test_with_qualifier(self):
        assert strip_qualifiers("hello in:name world") == "hello world"

    def test_with_stars(self):
        assert strip_qualifiers('hello world stars:">=100"') == "hello world"

    def test_quotes(self):
        assert strip_qualifiers('"hello world" test') == "hello world test"

    def test_empty(self):
        assert strip_qualifiers("") == ""


# ---------------------------------------------------------------------------
# query_terms
# ---------------------------------------------------------------------------

class TestQueryTerms:
    def test_basic(self):
        all_terms, high_signal = query_terms("AI novel writing", [])
        assert len(all_terms) > 0
        assert "novel" in all_terms or "writing" in all_terms

    def test_high_signal(self):
        all_terms, high_signal = query_terms("AI novel writing", [])
        assert len(high_signal) > 0
        # "ai" is in GENERIC_TERMS, should NOT be high signal
        assert "ai" not in high_signal

    def test_stopwords_removed(self):
        all_terms, _ = query_terms("the and of", [])
        assert "the" not in all_terms
        assert "and" not in all_terms


# ---------------------------------------------------------------------------
# field_tokens
# ---------------------------------------------------------------------------

class TestFieldTokens:
    def test_string(self):
        assert field_tokens("Hello World") == {"hello", "world"}

    def test_list(self):
        assert field_tokens(["Hello", "World"]) == {"hello", "world"}

    def test_none(self):
        assert field_tokens(None) == set()

    def test_mixed_case(self):
        assert field_tokens("Hello WORLD") == {"hello", "world"}


# ---------------------------------------------------------------------------
# phrase_variants
# ---------------------------------------------------------------------------

class TestPhraseVariants:
    def test_basic(self):
        variants = phrase_variants("AI novel writing", [])
        assert "ai novel writing" in variants

    def test_with_queries(self):
        variants = phrase_variants("AI", ["novel writing"])
        assert "novel writing" in variants

    def test_qualifiers_stripped(self):
        variants = phrase_variants("test", ["AI in:name"])
        assert "ai" in variants
        assert "in:name" not in variants


# ---------------------------------------------------------------------------
# relevance_score
# ---------------------------------------------------------------------------

class TestRelevanceScore:
    def _make_repo(self, name="test-org/test-repo", description="an AI novel writing tool", topics=None):
        return {
            "full_name": name,
            "name": name.split("/")[-1] if "/" in name else name,
            "description": description,
            "topics": topics or ["ai", "writing"],
        }

    def test_exact_match_in_name(self):
        repo = self._make_repo(name="novel-writer/awesome-novel-ai", description="AI novel writing")
        score = relevance_score(repo, "AI novel writing", [])
        assert score > 10  # phrase match in name gives high score

    def test_zero_for_unrelated(self):
        repo = self._make_repo(name="data-viz/chart-lib", description="charting library", topics=["chart"])
        score = relevance_score(repo, "AI novel writing", [])
        assert score == 0

    def test_match_in_description(self):
        repo = self._make_repo(description="a great AI novel writing assistant for authors")
        score = relevance_score(repo, "AI novel writing", [])
        assert score > 0

    def test_match_in_topics(self):
        repo = self._make_repo(description="some tool", topics=["novel", "fiction", "writing"])
        score = relevance_score(repo, "novel writing", [])
        assert score > 0

    def test_high_signal_zero_hits(self):
        repo = self._make_repo(name="random/pkg", description="a generic utility", topics=["utility"])
        score = relevance_score(repo, "novel writing fiction", [])
        assert score == 0  # high_signal_terms would be ["novel", "writing", "fiction"], none hit

    def test_minimal_score_for_long_desc_no_name_hit(self):
        repo = self._make_repo(
            description="x" * 1000 + " novel writing related but mostly noise" * 20,
            topics=[],
        )
        score = relevance_score(repo, "novel", [])
        # Without name/topic hits and long description, score is capped
        assert score <= 1

    def test_focus_term_filter(self):
        # If focus terms exist and none match, score should be 0
        repo = self._make_repo(description="a dashboard tool", topics=["dashboard"])
        # "novel" is a focus term for fiction domain
        score = relevance_score(repo, "AI novel writing", [])
        assert score == 0

    def test_empty_topics(self):
        repo = self._make_repo(name="write/novel-ai", description="novel writing", topics=[])
        score = relevance_score(repo, "AI novel writing", [])
        assert score > 0


# ---------------------------------------------------------------------------
# quality_score
# ---------------------------------------------------------------------------

class TestQualityScore:
    def _make_repo(self, **overrides):
        defaults = {
            "archived": False,
            "pushed_at": "2026-06-01T00:00:00Z",
            "license": {"spdx_id": "MIT", "name": "MIT License"},
            "topics": ["ai", "writing", "novel"],
            "stargazers_count": 5000,
            "forks_count": 800,
            "open_issues_count": 30,
            "language": "Python",
        }
        defaults.update(overrides)
        return defaults

    def test_high_quality(self):
        repo = self._make_repo()
        result = quality_score(repo, "x" * 5000)
        assert result["score"] >= 80
        assert len(result["signals"]) > 0

    def test_archived(self):
        repo = self._make_repo(archived=True)
        result = quality_score(repo, "x" * 5000)
        assert "archived" in result["signals"]

    def test_stale_activity(self):
        repo = self._make_repo(pushed_at="2020-01-01T00:00:00Z")
        result = quality_score(repo, "x" * 5000)
        assert "stale activity" in result["signals"]

    def test_no_license(self):
        repo = self._make_repo(license=None)
        result = quality_score(repo, "x" * 100)
        assert "no license metadata" in result["signals"]

    def test_small_community(self):
        repo = self._make_repo(stargazers_count=10, forks_count=1, open_issues_count=2)
        result = quality_score(repo, "x" * 100)
        # 10 not-archived + 25 active + 12 license = 47, + 6 topics + 2 stars + 5 language + 3 readme = 63
        # But with low stars, fork_ratio is 0.1 (8) and issue_ratio is 0.2 (0) → ~71
        assert result["score"] < 80

    def test_no_readme(self):
        repo = self._make_repo()
        result = quality_score(repo, None)
        # not archived(10) + active(25) + license(12) + topic(10) + 5k stars(10) + fork_ratio(8) + low issues(8) + lang(5) + 0 readme = 78
        assert result["score"] > 70 and result["score"] <= 100

    def test_score_capped(self):
        repo = self._make_repo()
        result = quality_score(repo, "x" * 10000)
        assert result["score"] <= 100


# ---------------------------------------------------------------------------
# activity_label
# ---------------------------------------------------------------------------

class TestActivityLabel:
    def test_active(self):
        assert activity_label("2026-06-01T00:00:00Z") == "active"

    def test_quiet(self):
        assert activity_label("2025-01-01T00:00:00Z") == "quiet"

    def test_stale(self):
        assert activity_label("2020-01-01T00:00:00Z") == "stale"

    def test_unknown(self):
        assert activity_label(None) == "unknown"


# ---------------------------------------------------------------------------
# days_since
# ---------------------------------------------------------------------------

class TestDaysSince:
    def test_recent(self):
        d = days_since("2026-07-01T00:00:00Z")
        assert d is not None
        assert d >= 0

    def test_none(self):
        assert days_since(None) is None


# ---------------------------------------------------------------------------
# safe_license
# ---------------------------------------------------------------------------

class TestSafeLicense:
    def test_spdx(self):
        repo = {"license": {"spdx_id": "MIT", "name": "MIT License"}}
        assert safe_license(repo) == "MIT"

    def test_name_fallback(self):
        repo = {"license": {"name": "Apache 2.0"}}
        assert safe_license(repo) == "Apache 2.0"

    def test_none(self):
        assert safe_license({}) is None
        assert safe_license({"license": None}) is None


# ---------------------------------------------------------------------------
# normalize_query
# ---------------------------------------------------------------------------

class TestNormalizeQuery:
    def test_adds_in(self):
        result = normalize_query("test query", None, "name,description")
        assert "in:name,description" in result

    def test_skips_existing_in(self):
        result = normalize_query("test in:name", None, "name,description")
        assert "in:name,description" not in result
        assert "in:name" in result

    def test_adds_stars(self):
        result = normalize_query("test", 100, "name,description")
        assert "stars:>=100" in result

    def test_skips_existing_stars(self):
        result = normalize_query("test stars:>=500", 100, "name,description")
        assert "stars:>=500" in result
        assert "stars:>=100" not in result
