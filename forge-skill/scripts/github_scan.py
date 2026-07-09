#!/usr/bin/env python3
"""Search top-starred GitHub repositories and write evidence reports."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import http.client
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

API_ROOT = "https://api.github.com"
DEFAULT_CACHE_DIR = Path.home() / ".forge-skill" / "cache"
DEFAULT_CONFIG_PATHS = [
    Path.cwd() / ".forge-skill.toml",
    Path.cwd() / "forge-skill" / "forge-skill.toml",
    Path.home() / ".forge-skill" / "config.toml",
]
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "in", "into",
    "is", "it", "of", "on", "or", "that", "the", "this", "to", "use", "with", "your",
}
GENERIC_TERMS = {
    "ai", "app", "apps", "bot", "code", "data", "demo", "dev", "generator", "github",
    "llm", "ml", "open", "project", "repo", "sdk", "software", "tool", "tools",
}

# Default built-in topic expansions — users can override via external file
DEFAULT_TOPIC_EXPANSIONS = [
    {
        "needles": ["novel", "fiction", "\u5c0f\u8bf4", "\u7f51\u6587"],
        "queries": [
            "AI novel writing",
            "AI fiction writing",
            "AI story generator",
            "LLM creative writing",
            "worldbuilding writing assistant",
            "long-form fiction AI",
        ],
    },
    {
        "needles": ["story", "narrative", "\u6545\u4e8b", "\u5267\u60c5", "\u53d9\u4e8b"],
        "queries": [
            "AI story generator",
            "story writing assistant",
            "narrative generation",
            "creative writing AI",
        ],
    },
    {
        "needles": ["writing", "writer", "\u5199\u4f5c", "\u521b\u4f5c"],
        "queries": [
            "AI writing assistant",
            "LLM writing assistant",
            "creative writing AI",
        ],
    },
    {
        "needles": ["agent", "agents", "\u667a\u80fd\u4f53"],
        "queries": [
            "AI agent framework",
            "LLM agent framework",
            "autonomous agents",
            "multi agent framework",
        ],
    },
    {
        "needles": ["dashboard", "\u4eea\u8868\u76d8", "\u5927\u5c4f", "\u6570\u636e\u770b\u677f"],
        "queries": [
            "dashboard builder",
            "admin dashboard",
            "analytics dashboard",
            "data visualization dashboard",
        ],
    },
    {
        "needles": ["workflow", "\u5de5\u4f5c\u6d41", "\u81ea\u52a8\u5316"],
        "queries": [
            "workflow automation",
            "AI workflow builder",
            "automation workflow engine",
        ],
    },
    {
        "needles": ["rag", "retrieval", "qa", "\u68c0\u7d22"],
        "queries": [
            "RAG framework",
            "retrieval augmented generation",
            "document QA",
            "knowledge base LLM",
        ],
    },
    {
        "needles": ["devops", "ci", "cd", "deploy", "\u8fd0\u7ef4"],
        "queries": [
            "devops tool",
            "CI CD pipeline",
            "infrastructure as code",
            "deployment automation",
        ],
    },
    {
        "needles": ["game", "\u6e38\u620f", "gaming"],
        "queries": [
            "game engine",
            "game development framework",
            "AI game",
            "procedural generation",
        ],
    },
    {
        "needles": ["data", "analytics", "\u6570\u636e", "\u5206\u6790"],
        "queries": [
            "data analysis tool",
            "analytics platform",
            "data pipeline",
            "business intelligence",
        ],
    },
]
DEFAULT_FOCUS_RULES = [
    {
        "needles": ["novel", "fiction", "\u5c0f\u8bf4", "\u7f51\u6587"],
        "terms": ["novel", "fiction", "story", "worldbuilding", "narrative"],
    },
    {
        "needles": ["story", "narrative", "\u6545\u4e8b", "\u5267\u60c5", "\u53d9\u4e8b"],
        "terms": ["story", "narrative", "fiction", "worldbuilding"],
    },
    {
        "needles": ["agent", "agents", "\u667a\u80fd\u4f53"],
        "terms": ["agent", "agents", "multiagent", "autonomous"],
    },
    {
        "needles": ["dashboard", "\u4eea\u8868\u76d8", "\u5927\u5c4f", "\u6570\u636e\u770b\u677f"],
        "terms": ["dashboard", "analytics", "visualization", "admin"],
    },
    {
        "needles": ["game", "\u6e38\u620f", "gaming"],
        "terms": ["game", "gaming", "procedural", "rpg"],
    },
    {
        "needles": ["rag", "retrieval", "\u68c0\u7d22", "qa"],
        "terms": ["rag", "retrieval", "qa", "knowledge"],
    },
]


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config() -> dict[str, Any]:
    """Load config from the first existing .forge-skill.toml."""
    for candidate in DEFAULT_CONFIG_PATHS:
        if candidate.exists():
            try:
                raw = candidate.read_text(encoding="utf-8")
                # Minimal TOML parser: handles [section] and key = value
                config: dict[str, Any] = {}
                section = config
                for line in raw.splitlines():
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    m = re.match(r"^\[(.+)\]$", stripped)
                    if m:
                        section_name = m.group(1)
                        config[section_name] = {}
                        section = config[section_name]
                        continue
                    if "=" in stripped:
                        key, _, value = stripped.partition("=")
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        # Try bool / int
                        if value.lower() in ("true", "yes", "on"):
                            value = True
                        elif value.lower() in ("false", "no", "off"):
                            value = False
                        else:
                            try:
                                value = int(value)
                            except ValueError:
                                try:
                                    value = float(value)
                                except ValueError:
                                    pass
                        section[key] = value
                return config
            except Exception:
                pass
    return {}


def config_get(config: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Traverse config with dotted keys."""
    current = config
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, {})
        else:
            return default
    if isinstance(current, dict) and not current:
        return default
    return current if current != {} else default


def make_config_argparser() -> argparse.ArgumentParser:
    """Add --config flag to an existing or new parser."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config", help="Path to config TOML file (default: auto-detect).")
    return parser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:80] or "github-scan"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def get_token() -> str | None:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


# ---------------------------------------------------------------------------
# Caching layer
# ---------------------------------------------------------------------------

_cache_dir: Path | None = None


def _get_cache_dir() -> Path:
    global _cache_dir
    if _cache_dir is None:
        _cache_dir = DEFAULT_CACHE_DIR
    return _cache_dir


def _cache_key(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _cached_path(url: str) -> Path:
    return _get_cache_dir() / _cache_key(url)


def cached_github_request(
    url: str,
    *,
    accept: str = "application/vnd.github+json",
    ttl_hours: float = 1,
) -> Any:
    """GitHub request with disk cache (get/set)."""
    cache_path = _cached_path(url)
    if cache_path.exists() and (time.time() - cache_path.stat().st_mtime) < ttl_hours * 3600:
        try:
            raw = cache_path.read_text(encoding="utf-8")
            cached = json.loads(raw)
            if isinstance(cached, dict) and "_forge_cache_meta" in cached:
                return cached["_forge_cache_data"]
            return cached
        except (json.JSONDecodeError, OSError):
            pass  # invalid cache → re-fetch

    data = github_request(url, accept=accept)

    # Save to cache
    try:
        _get_cache_dir().mkdir(parents=True, exist_ok=True)
        to_cache = {"_forge_cache_meta": {"cached_at": time.time(), "url": url}, "_forge_cache_data": data}
        cache_path.write_text(json.dumps(to_cache, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass  # non-fatal if cache write fails

    return data


def clear_cache(url_pattern: str | None = None) -> int:
    """Clear cache entries. Returns count removed."""
    cache_dir = _get_cache_dir()
    if not cache_dir.exists():
        return 0
    removed = 0
    for path in cache_dir.iterdir():
        if path.is_file() and len(path.name) == 16:
            if url_pattern is None or url_pattern in path.read_text(encoding="utf-8", errors="replace"):
                path.unlink()
                removed += 1
    return removed


# ---------------------------------------------------------------------------
# GitHub API (raw, no cache)
# ---------------------------------------------------------------------------

def github_request(url: str, *, accept: str = "application/vnd.github+json") -> Any:
    """Low-level GitHub API call with exponential backoff + jitter."""
    headers = {
        "Accept": accept,
        "User-Agent": "zcode-forge-skill",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = get_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    last_exc: Exception | None = None
    for attempt in range(3):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read()
                content_type = response.headers.get("Content-Type", "")
                if accept.endswith(".raw") or "text/" in content_type:
                    return body.decode("utf-8", errors="replace")
                return json.loads(body.decode("utf-8"))
        except http.client.IncompleteRead as exc:
            last_exc = RuntimeError(f"GitHub response was incomplete after retries for {url}: {exc}")
        except urllib.error.HTTPError as exc:
            reset = exc.headers.get("X-RateLimit-Reset")
            remaining = exc.headers.get("X-RateLimit-Remaining")
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code in {403, 429} and remaining == "0" and reset:
                reset_time = dt.datetime.fromtimestamp(int(reset), dt.timezone.utc).isoformat()
                raise RuntimeError(
                    f"GitHub rate limit reached. Resets at {reset_time}. "
                    f"Set GITHUB_TOKEN for a higher limit."
                ) from exc
            if exc.code == 404:
                return None
            last_exc = RuntimeError(f"GitHub request failed: HTTP {exc.code} for {url}\n{detail[:500]}")
        except urllib.error.URLError as exc:
            last_exc = RuntimeError(f"GitHub request failed for {url}: {exc}")
        except (ConnectionResetError, TimeoutError) as exc:
            last_exc = RuntimeError(f"Connection error for {url}: {exc}")

        if attempt == 2:
            raise last_exc  # type: ignore[misc]
        # Exponential backoff with jitter
        delay = 1.5 ** attempt + random.uniform(0, 0.5)
        time.sleep(delay)

    raise RuntimeError(f"GitHub request failed after retries for {url}")


# ---------------------------------------------------------------------------
# Query expansion & scoring
# ---------------------------------------------------------------------------

_loaded_expansions: list[dict[str, Any]] | None = None
_loaded_focus_rules: list[dict[str, Any]] | None = None


def _ensure_rules_loaded(expansion_rules_path: str | None = None) -> None:
    """Load expansion rules from external file or fallback to built-ins."""
    global _loaded_expansions, _loaded_focus_rules
    if _loaded_expansions is not None and _loaded_focus_rules is not None:
        return

    if expansion_rules_path:
        p = Path(expansion_rules_path)
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                expansions = data.get("expansions") or data.get("topic_expansions") or []
                focus = data.get("focus_rules") or []
                if expansions:
                    _loaded_expansions = expansions
                if focus:
                    _loaded_focus_rules = focus
                return
            except (json.JSONDecodeError, OSError):
                print(f"warning: could not load expansion rules from {p}", file=sys.stderr)

    if _loaded_expansions is None:
        _loaded_expansions = DEFAULT_TOPIC_EXPANSIONS
    if _loaded_focus_rules is None:
        _loaded_focus_rules = DEFAULT_FOCUS_RULES


def normalize_query(raw_query: str, min_stars: int | None, search_fields: str) -> str:
    query = raw_query.strip()
    if " in:" not in f" {query}":
        query = f"{query} in:{search_fields}"
    if min_stars is not None and " stars:" not in f" {query}":
        query = f"{query} stars:>={min_stars}"
    return query


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = " ".join(value.strip().split())
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def contains_non_ascii(value: str) -> bool:
    return any(ord(char) > 127 for char in value)


def auto_expand_queries(
    topic: str,
    queries: list[str],
    max_variants: int,
    expansion_rules_path: str | None = None,
) -> list[str]:
    _ensure_rules_loaded(expansion_rules_path)
    source = " ".join([topic, *queries]).lower()
    expanded = list(queries)

    for rule in _loaded_expansions or []:
        if any(needle.lower() in source for needle in rule.get("needles", [])):
            expanded.extend(rule.get("queries", []))

    if contains_non_ascii(source) and len(expanded) == len(queries):
        expanded.extend([
            f"{topic} AI",
            f"{topic} LLM",
            f"{topic} open source",
        ])

    return dedupe(expanded)[:max_variants]


def focus_terms(
    topic: str,
    queries: list[str],
    expansion_rules_path: str | None = None,
) -> list[str]:
    _ensure_rules_loaded(expansion_rules_path)
    source = " ".join([topic, *queries]).lower()
    terms: list[str] = []
    for rule in _loaded_focus_rules or []:
        if any(needle.lower() in source for needle in rule.get("needles", [])):
            terms.extend(rule.get("terms", []))
    return dedupe(terms)


def words(value: str | None) -> list[str]:
    if not value:
        return []
    return re.findall(r"[a-zA-Z0-9]+", value.lower())


def strip_qualifiers(query: str) -> str:
    parts = []
    for part in query.split():
        if ":" in part:
            continue
        if part.startswith("-"):
            continue
        parts.append(part.strip('"'))
    return " ".join(parts)


def query_terms(topic: str, queries: list[str]) -> tuple[list[str], list[str]]:
    raw = " ".join([topic, *[strip_qualifiers(query) for query in queries]])
    ordered: list[str] = []
    seen: set[str] = set()
    for term in words(raw):
        if term in STOPWORDS or term in seen:
            continue
        seen.add(term)
        ordered.append(term)
    high_signal = [term for term in ordered if len(term) >= 4 and term not in GENERIC_TERMS]
    return ordered, high_signal


def field_tokens(value: str | list[str] | None) -> set[str]:
    if isinstance(value, list):
        value = " ".join(value)
    return set(words(value))


def phrase_variants(topic: str, queries: list[str]) -> list[str]:
    variants: list[str] = []
    for value in [topic, *queries]:
        phrase = strip_qualifiers(value).lower().strip()
        if phrase and phrase not in variants:
            variants.append(phrase)
    return variants


def relevance_score(item: dict[str, Any], topic: str, queries: list[str]) -> int:
    all_terms, high_signal_terms = query_terms(topic, queries)
    if not all_terms:
        return 0

    name = " ".join([item.get("full_name") or "", item.get("name") or ""])
    description = item.get("description") or ""
    topics = item.get("topics") or []
    name_tokens = field_tokens(name)
    desc_tokens = field_tokens(description)
    topic_tokens = field_tokens(topics)
    name_text = name.lower()
    desc_text = description.lower()
    topic_text = " ".join(topics).lower()

    score = 0
    high_signal_hits = 0
    name_or_topic_hits = 0
    focus = focus_terms(topic, queries)
    focus_hit = False

    for term in focus:
        if term in name_tokens or term in topic_tokens or term in desc_tokens:
            focus_hit = True
            break
    if focus and not focus_hit:
        return 0

    for phrase in phrase_variants(topic, queries):
        if len(words(phrase)) < 2:
            continue
        if phrase in name_text:
            score += 12
        if phrase in topic_text:
            score += 8
        if phrase in desc_text:
            score += 4 if len(description) <= 800 else 1

    for term in high_signal_terms:
        hit = False
        if term in name_tokens:
            score += 4
            hit = True
            name_or_topic_hits += 1
        if term in topic_tokens:
            score += 4
            hit = True
            name_or_topic_hits += 1
        if term in desc_tokens:
            score += 1
            hit = True
        if hit:
            high_signal_hits += 1

    for term in all_terms:
        if term in high_signal_terms:
            continue
        if term in name_tokens or term in topic_tokens:
            score += 1

    if high_signal_terms and high_signal_hits == 0:
        return 0
    if name_or_topic_hits == 0 and len(description) > 800:
        return min(score, 1)
    return score


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search_repositories(
    topic: str,
    queries: list[str],
    candidate_limit: int,
    min_stars: int | None,
    search_fields: str,
    min_relevance: int,
) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    per_page = min(100, max(candidate_limit * 4, 50))

    for raw_query in queries:
        query = normalize_query(raw_query, min_stars, search_fields)
        params = urllib.parse.urlencode({
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": per_page,
        })
        url = f"{API_ROOT}/search/repositories?{params}"
        payload = cached_github_request(url)
        for item in payload.get("items", []):
            full_name = item.get("full_name")
            if full_name and full_name not in seen:
                item["_matched_query"] = query
                item["_relevance_score"] = relevance_score(item, topic, queries)
                seen[full_name] = item
        time.sleep(0.3)

    filtered = [item for item in seen.values() if item.get("_relevance_score", 0) >= min_relevance]
    if len(filtered) < candidate_limit:
        print(
            f"warning: only {len(filtered)} repositories met relevance >= {min_relevance}; "
            "try more query variants or --search-fields name,description,readme",
            file=sys.stderr,
        )
    return sorted(filtered, key=lambda item: item.get("stargazers_count", 0), reverse=True)[:candidate_limit]


# ---------------------------------------------------------------------------
# Enrichment
# ---------------------------------------------------------------------------

def days_since(date_text: str | None) -> int | None:
    if not date_text:
        return None
    parsed = dt.datetime.fromisoformat(date_text.replace("Z", "+00:00"))
    return (dt.datetime.now(dt.timezone.utc) - parsed).days


def activity_label(pushed_at: str | None) -> str:
    days = days_since(pushed_at)
    if days is None:
        return "unknown"
    if days <= 180:
        return "active"
    if days <= 730:
        return "quiet"
    return "stale"


def quality_score(repo: dict[str, Any], readme: str | None) -> dict[str, Any]:
    score = 0
    signals: list[str] = []

    if repo.get("archived"):
        signals.append("archived")
    else:
        score += 10
        signals.append("not archived")

    activity = activity_label(repo.get("pushed_at"))
    if activity == "active":
        score += 25
        signals.append("recent activity")
    elif activity == "quiet":
        score += 10
        signals.append("some activity")
    else:
        signals.append("stale activity")

    license_name = safe_license(repo)
    if license_name and license_name != "NOASSERTION":
        score += 12
        signals.append("clear license")
    elif license_name:
        score += 3
        signals.append("license unclear")
    else:
        signals.append("no license metadata")

    topics = repo.get("topics") or []
    if topics:
        topic_points = min(10, len(topics) * 2)
        score += topic_points
        signals.append("topic metadata")

    stars = repo.get("stargazers_count") or 0
    forks = repo.get("forks_count") or 0
    open_issues = repo.get("open_issues_count") or 0
    if stars >= 1000:
        score += 10
        signals.append("large community")
    elif stars >= 100:
        score += 6
        signals.append("moderate community")
    elif stars > 0:
        score += 2

    if stars > 0:
        fork_ratio = forks / stars
        issue_ratio = open_issues / stars
        if fork_ratio >= 0.1:
            score += 8
            signals.append("fork adoption")
        elif fork_ratio >= 0.03:
            score += 4
        if issue_ratio <= 0.03:
            score += 8
            signals.append("low issue load")
        elif issue_ratio <= 0.15:
            score += 4

    if repo.get("language"):
        score += 5
        signals.append("primary language")

    readme_len = len(readme or "")
    if readme_len >= 3000:
        score += 12
        signals.append("substantial README")
    elif readme_len >= 800:
        score += 7
        signals.append("useful README")
    elif readme_len > 0:
        score += 3

    return {"score": min(score, 100), "signals": signals[:6]}


def safe_license(repo: dict[str, Any]) -> str | None:
    license_info = repo.get("license")
    if not license_info:
        return None
    return license_info.get("spdx_id") or license_info.get("name")


def fetch_readme(full_name: str, max_chars: int) -> str | None:
    if max_chars <= 0:
        return None
    encoded = urllib.parse.quote(full_name, safe="/")
    text = cached_github_request(
        f"{API_ROOT}/repos/{encoded}/readme",
        accept="application/vnd.github.raw",
    )
    if not text:
        return None
    return text[:max_chars]


def fetch_languages(full_name: str) -> dict[str, int]:
    encoded = urllib.parse.quote(full_name, safe="/")
    payload = cached_github_request(f"{API_ROOT}/repos/{encoded}/languages")
    return payload or {}


def enrich(item: dict[str, Any], readme_chars: int) -> dict[str, Any]:
    full_name = item["full_name"]
    encoded = urllib.parse.quote(full_name, safe="/")
    detail = cached_github_request(f"{API_ROOT}/repos/{encoded}") or item
    languages = fetch_languages(full_name)
    readme = fetch_readme(full_name, readme_chars)
    quality = quality_score(detail, readme)

    return {
        "full_name": full_name,
        "name": detail.get("name") or item.get("name"),
        "owner": (detail.get("owner") or {}).get("login"),
        "html_url": detail.get("html_url") or item.get("html_url"),
        "description": detail.get("description") or item.get("description"),
        "stars": detail.get("stargazers_count") or item.get("stargazers_count"),
        "forks": detail.get("forks_count") or item.get("forks_count"),
        "open_issues": detail.get("open_issues_count") or item.get("open_issues_count"),
        "watchers": detail.get("subscribers_count"),
        "language": detail.get("language") or item.get("language"),
        "languages": languages,
        "topics": detail.get("topics") or item.get("topics") or [],
        "license": safe_license(detail) or safe_license(item),
        "archived": detail.get("archived"),
        "created_at": detail.get("created_at"),
        "updated_at": detail.get("updated_at"),
        "pushed_at": detail.get("pushed_at"),
        "activity": activity_label(detail.get("pushed_at")),
        "default_branch": detail.get("default_branch"),
        "matched_query": item.get("_matched_query"),
        "relevance_score": item.get("_relevance_score"),
        "quality_score": quality["score"],
        "quality_signals": quality["signals"],
        "readme_excerpt": readme,
    }


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def markdown_table_row(values: list[Any]) -> str:
    escaped = []
    for value in values:
        text = "" if value is None else str(value)
        escaped.append(text.replace("|", "\\|").replace("\n", " "))
    return "| " + " | ".join(escaped) + " |"


def sparkbar(values: list[int], width: int = 6) -> str:
    """Render a simple text sparkline / mini bar chart."""
    if not values:
        return ""
    mx = max(values)
    if mx == 0:
        return " " * width
    chars = "▁▂▃▄▅▆▇█"
    out = ""
    for v in values:
        idx = int((v / mx) * (len(chars) - 1))
        out += chars[idx]
    return out


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append(f"# GitHub Scan: {payload['topic']}")
    lines.append("")
    lines.append(f"- Scan time: `{payload['scanned_at']}`")
    lines.append(f"- Auto query expansion: `{payload['auto_expand']}`")
    lines.append(f"- Source queries: {', '.join(f'`{q}`' for q in payload['source_queries'])}")
    lines.append(f"- Queries: {', '.join(f'`{q}`' for q in payload['queries'])}")
    lines.append(f"- Focus terms: {', '.join(f'`{term}`' for term in payload['focus_terms']) or '`none`'}")
    lines.append(f"- Search fields: `{payload['search_fields']}`")
    lines.append(f"- Target final count: {payload['limit']}")
    lines.append(f"- Candidate count: {len(payload['repositories'])}")
    lines.append("")

    # Stars distribution bar
    star_values = [repo.get("stars") or 0 for repo in payload["repositories"]]
    if star_values:
        bar = sparkbar(star_values)
        lines.append("### Stars Distribution")
        lines.append("")
        lines.append(f"`{bar}`  (bigger = more stars)")
        lines.append("")

    lines.append("## Candidate Repositories (Pre-LLM)")
    lines.append("")
    lines.append(markdown_table_row(["#", "Repository", "Stars", "★Bar", "Relevance", "Quality", "Language", "Activity", "Pushed", "License"]))
    lines.append(markdown_table_row(["---", "---", "---:", "---", "---:", "---:", "---", "---", "---", "---"]))
    for index, repo in enumerate(payload["repositories"], 1):
        star_val = repo["stars"] or 0
        bar_char = sparkbar([star_val], width=1)
        lines.append(markdown_table_row([
            index,
            f"[{repo['full_name']}]({repo['html_url']})",
            repo["stars"],
            bar_char,
            repo["relevance_score"],
            repo["quality_score"],
            repo["language"],
            repo["activity"],
            repo["pushed_at"],
            repo["license"],
        ]))
    lines.append("")
    lines.append("## LLM Rerank Worksheet")
    lines.append("")
    lines.append(
        f"Select up to {payload['limit']} repositories that best match the user's domain. "
        "Prefer true domain fit over raw stars, but preserve star order when relevance is comparable."
    )
    lines.append("")
    lines.append(markdown_table_row(["Decision", "Final Rank", "Repository", "Stars", "Rel", "Qual", "Reason"]))
    lines.append(markdown_table_row(["---", "---:", "---", "---:", "---:", "---:", "---"]))
    for repo in payload["repositories"]:
        lines.append(markdown_table_row([
            "review", "", repo["full_name"],
            repo["stars"], repo["relevance_score"], repo["quality_score"], "",
        ]))
    lines.append("")
    lines.append("## Evidence Notes")
    for repo in payload["repositories"]:
        lines.append("")
        lines.append(f"### {repo['full_name']}")
        lines.append("")
        lines.append(f"- URL: {repo['html_url']}")
        lines.append(f"- Description: {repo.get('description') or 'No description'}")
        lines.append(f"- Topics: {', '.join(repo.get('topics') or []) or 'None listed'}")
        lines.append(f"- Relevance score: {repo.get('relevance_score')}")
        lines.append(f"- Quality score/signals: {repo.get('quality_score')} / {', '.join(repo.get('quality_signals') or []) or 'None'}")
        lines.append(f"- Stars/forks/issues: {repo.get('stars')} / {repo.get('forks')} / {repo.get('open_issues')}")
        lines.append(f"- Activity/license: {repo.get('activity')} / {repo.get('license') or 'Unclear'}")
        readme = (repo.get("readme_excerpt") or "").strip()
        if readme:
            excerpt = readme[:2000].replace("```", "'''")
            lines.append("")
            lines.append("README excerpt:")
            lines.append("")
            lines.append("```markdown")
            lines.append(excerpt)
            lines.append("```")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    # First pass: extract --config before full parse
    config_parser = make_config_argparser()
    known, remaining = config_parser.parse_known_args(argv)
    cfg: dict[str, Any] = {}
    if known.config:
        p = Path(known.config)
        if p.exists():
            try:
                raw = p.read_text(encoding="utf-8")
                cfg = json.loads(raw) if p.suffix == ".json" else _minimal_toml_parse(raw)
            except Exception as exc:
                print(f"warning: failed to load config {p}: {exc}", file=sys.stderr)
    else:
        cfg = load_config()

    parser = argparse.ArgumentParser(
        description="Scan top-starred GitHub repositories for a topic.",
        parents=[make_config_argparser()],
    )
    parser.add_argument("topic", help="User-facing topic/domain, e.g. 'AI novel writing'.")
    parser.add_argument("--query", action="append", help="GitHub repository search query variant. Can be repeated.")
    parser.add_argument("--no-auto-expand", action="store_true", help="Disable automatic query expansion for Chinese/broad topics.")
    parser.add_argument("--max-query-variants", type=int, default=config_get(cfg, "defaults", "max_query_variants", default=8),
                        help="Maximum query variants after automatic expansion.")
    parser.add_argument("--limit", type=int, default=config_get(cfg, "defaults", "limit", default=10),
                        help="Target number of repositories to keep after LLM rerank.")
    parser.add_argument("--candidate-limit", type=int,
                        help="Number of pre-LLM candidates to enrich. Defaults to max(limit * 3, limit).")
    parser.add_argument("--min-stars", type=int, default=config_get(cfg, "defaults", "min_stars", default=0),
                        help="Minimum stars qualifier to append unless query already includes stars:.")
    parser.add_argument("--readme-chars", type=int, default=config_get(cfg, "defaults", "readme_chars", default=6000),
                        help="Maximum README characters to store per repository. Use 0 to skip.")
    parser.add_argument("--search-fields", default=config_get(cfg, "defaults", "search_fields", default="name,description"),
                        help="GitHub in: fields to append. Use name,description by default; add readme only when results are sparse.")
    parser.add_argument("--min-relevance", type=int, default=config_get(cfg, "defaults", "min_relevance", default=2),
                        help="Minimum lightweight relevance score before a repository can be kept.")
    parser.add_argument("--max-workers", type=int, default=config_get(cfg, "defaults", "max_workers", default=5),
                        help="Number of concurrent enrichment workers.")
    parser.add_argument("--cache-ttl", type=float, default=config_get(cfg, "defaults", "cache_ttl_hours", default=1),
                        help="Cache TTL in hours.")
    parser.add_argument("--no-cache", action="store_true", help="Disable disk cache.")
    parser.add_argument("--clear-cache", action="store_true", help="Clear cache and exit.")
    parser.add_argument("--expansion-rules", help="Path to external expansion rules JSON file.")
    parser.add_argument("--out", help="Output JSON path. Defaults to ./github_scan_<topic>.json")
    parser.add_argument("--markdown-out", help="Output Markdown path. Defaults to JSON path with .md suffix.")
    args = parser.parse_args(remaining)

    # Apply config defaults for None values
    if args.candidate_limit is None:
        args.candidate_limit = config_get(cfg, "defaults", "candidate_limit", default=max(args.limit * 3, args.limit))
    if args.expansion_rules is None:
        args.expansion_rules = config_get(cfg, "expansion_rules", "path")

    # Override config from env
    env_token = config_get(cfg, "github", "token")
    if env_token and not get_token():
        os.environ["GITHUB_TOKEN"] = str(env_token)

    return args


def _minimal_toml_parse(text: str) -> dict[str, Any]:
    """Parse minimal TOML (sections + key = value)."""
    config: dict[str, Any] = {}
    section = config
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = re.match(r"^\[(.+)\]$", stripped)
        if m:
            section_name = m.group(1)
            config[section_name] = {}
            section = config[section_name]
            continue
        if "=" in stripped:
            key, _, value = stripped.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if value.lower() in ("true", "yes", "on"):
                value = True
            elif value.lower() in ("false", "no", "off"):
                value = False
            else:
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
            section[key] = value
    return config


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    args = parse_args(argv)

    # Cache management
    if args.clear_cache:
        count = clear_cache()
        print(f"Cleared {count} cache entries.")
        return 0

    global _cache_dir
    if args.no_cache:
        _cache_dir = None  # type: ignore[assignment]

    source_queries = args.query or [args.topic]
    queries = (
        source_queries
        if args.no_auto_expand
        else auto_expand_queries(args.topic, source_queries, args.max_query_variants, args.expansion_rules)
    )
    candidate_limit = args.candidate_limit or max(args.limit * 3, args.limit)
    if candidate_limit < args.limit:
        raise RuntimeError("--candidate-limit must be greater than or equal to --limit")

    out_path = Path(args.out or f"github_scan_{slugify(args.topic)}.json").resolve()
    md_path = Path(args.markdown_out).resolve() if args.markdown_out else out_path.with_suffix(".md")

    # Search
    repos = search_repositories(
        args.topic, queries, candidate_limit,
        args.min_stars, args.search_fields, args.min_relevance,
    )
    if not repos:
        raise RuntimeError("No repositories found. Try broader or English query variants.")

    # Concurrent enrichment
    enriched: list[dict[str, Any]] = []
    max_workers = args.max_workers
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(enrich, repo, args.readme_chars): repo
            for repo in repos
        }
        if tqdm is not None:
            iterator = tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Enriching repositories",
                unit="repo",
                file=sys.stderr,
            )
        else:
            print(
                f"Enriching {len(futures)} repositories ({max_workers} workers)...",
                file=sys.stderr,
            )
            iterator = as_completed(futures)

        for future in iterator:
            repo = futures[future]
            try:
                result = future.result()
                enriched.append(result)
            except Exception as exc:
                print(
                    f"error enriching {repo.get('full_name', 'unknown')}: {exc}",
                    file=sys.stderr,
                )

    # Sort enriched list by stars desc (they may come back out of order)
    enriched.sort(key=lambda r: r.get("stars") or 0, reverse=True)

    payload = {
        "topic": args.topic,
        "queries": queries,
        "source_queries": source_queries,
        "auto_expand": not args.no_auto_expand,
        "focus_terms": focus_terms(args.topic, queries, args.expansion_rules),
        "search_fields": args.search_fields,
        "scanned_at": utc_now(),
        "limit": args.limit,
        "candidate_limit": candidate_limit,
        "repositories": enriched,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(md_path, payload)
    print(json.dumps({
        "json": str(out_path),
        "markdown": str(md_path),
        "candidates": len(enriched),
        "target_limit": args.limit,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
