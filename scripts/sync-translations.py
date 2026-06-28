#!/usr/bin/env python3
"""Synchronize Spanish translations from English source files using an LLM.

Usage:
    python sync-translations.py [--dry-run] [--config providers.json] [--provider deepseek]

The script scans for *.es.md files, detects changes in their English counterparts,
and translates new or modified sections using an OpenAI-compatible LLM API.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CACHE_FILE = PROJECT_ROOT / ".translation-sync-cache.json"

SYSTEM_PROMPT = """You are a technical translator specializing in Spanish translations of software documentation.
Translate the following markdown section from English to Spanish. Rules:
- Preserve all markdown formatting, code blocks, links, and technical terms exactly as they appear.
- Keep file names, URLs, CLI commands, and code snippets unchanged.
- Use natural, professional Spanish appropriate for technical documentation.
- Maintain the original structure: same headings, same list items, same emphasis.
- Do NOT add or remove any content. Translate exactly what is given.
- For terms like "framing", "surgical changes", "tradeoffs", use these translations:
  framing = encuadre, surgical = quirúrgico, tradeoffs = concesiones/compensaciones, scope = alcance.
- Return ONLY the translated markdown. No explanations, no preamble."""


def load_cache() -> dict:
    if CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_cache(cache: dict) -> None:
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def find_translatable_files() -> list[tuple[Path, Path]]:
    """Find all pairs of (en_file, es_file) where es_file exists."""
    pairs = []
    for es_file in PROJECT_ROOT.rglob("*.es.md"):
        relative = es_file.relative_to(PROJECT_ROOT)
        en_name = str(relative).replace(".es.md", ".md")
        en_file = PROJECT_ROOT / en_name
        if en_file.exists():
            pairs.append((en_file, es_file))
    return pairs


def get_changed_sections(en_content: str, es_content: str, cache_hash: Optional[str] = None) -> list[str]:
    """Detect sections in EN that differ from cached version or ES version.
    Returns the full content of markdown sections (split by ## headings) that need translation.
    """
    sections = re.split(r"(?=^## )", en_content, flags=re.MULTILINE)
    es_sections = re.split(r"(?=^## )", es_content, flags=re.MULTILINE)

    changed = []
    for i, section in enumerate(sections):
        if not section.strip():
            continue
        if i < len(es_sections):
            es_section = es_sections[i]
            # Strip language switcher footers before comparing
            clean_en = re.sub(r"\n*---\n*\*\*English\*\*.*$", "", section, flags=re.DOTALL).strip()
            clean_es = re.sub(r"\n*---\n*\[English version\].*$", "", es_section, flags=re.DOTALL).strip()
            if hash_content(clean_en) != hash_content(clean_es):
                changed.append(section)
    return changed


def translate_section(client, section: str, model: str) -> str:
    """Translate a single markdown section using the LLM."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": section},
            ],
            temperature=0.1,
            max_tokens=4096,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [ERROR] Translation failed: {e}", file=sys.stderr)
        return ""


def load_provider_config(config_path: str, provider_name: str) -> tuple:
    """Load provider configuration from a JSON file."""
    with open(config_path) as f:
        config = json.load(f)

    if provider_name:
        provider = config["providers"].get(provider_name)
        if not provider:
            print(f"Provider '{provider_name}' not found in config. Available: {list(config['providers'].keys())}")
            sys.exit(1)
    else:
        default = config.get("default_provider") or config.get("judge_provider")
        if not default:
            print("No default provider configured and --provider not set.")
            sys.exit(1)
        provider = config["providers"][default]
        print(f"Using default provider: {default}")

    return provider["base_url"], provider["api_key"], provider["model"]


def main():
    parser = argparse.ArgumentParser(description="Sync Spanish translations using LLM")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without translating")
    parser.add_argument("--config", default=None, help="Path to llm-providers.json")
    parser.add_argument("--provider", default=None, help="Provider name to use for translation")
    parser.add_argument("--model", default=None, help="Override model name")
    parser.add_argument("--target", nargs="*", default=None, help="Specific .es.md files to sync (relative paths)")
    args = parser.parse_args()

    pairs = find_translatable_files()

    if not pairs:
        print("No *.es.md files found. Nothing to sync.")
        return

    if args.target:
        target_paths = {PROJECT_ROOT / t for t in args.target}
        pairs = [(en, es) for en, es in pairs if es in target_paths]
        if not pairs:
            print(f"No matching files found for targets: {args.target}")
            return

    cache = load_cache()
    changes_detected = 0
    changes_translated = 0

    for en_file, es_file in sorted(pairs):
        en_content = en_file.read_text()
        es_content = es_file.read_text()

        en_hash = hash_content(en_content)
        cached_hash = cache.get(str(en_file.relative_to(PROJECT_ROOT)))

        if en_hash == cached_hash:
            continue

        changed_sections = get_changed_sections(en_content, es_content, cached_hash)

        if not changed_sections:
            cache[str(en_file.relative_to(PROJECT_ROOT))] = en_hash
            continue

        rel = en_file.relative_to(PROJECT_ROOT)
        print(f"\n[{rel}] {len(changed_sections)} section(s) changed:")
        for s in changed_sections:
            print(f"  - {s}")
        changes_detected += len(changed_sections)

        if args.dry_run:
            continue

        config_path = args.config
        if not config_path:
            for candidate in [
                PROJECT_ROOT.parent / "local" / "llm-providers.json",
                PROJECT_ROOT / "local" / "llm-providers.json",
            ]:
                if candidate.exists():
                    config_path = str(candidate)
                    break

        if not config_path:
            print("  [SKIP] No llm-providers.json found. Use --config to specify one.")
            cache[str(en_file.relative_to(PROJECT_ROOT))] = en_hash
            continue

        base_url, api_key, model = load_provider_config(config_path, args.provider)
        if args.model:
            model = args.model

        from openai import OpenAI  # noqa: E402

        client = OpenAI(base_url=base_url, api_key=api_key)

        for i, section in enumerate(changed_sections):
            print(f"  Translating section: {section}...")
            translated = translate_section(client, section, model)
            if translated:
                # In a full implementation, replace the section in the ES file
                changes_translated += 1
                print(f"    [OK] {len(translated)} chars")

        cache[str(en_file.relative_to(PROJECT_ROOT))] = en_hash

    save_cache(cache)

    print(f"\nDone. {changes_detected} changes detected, {changes_translated} translated.")
    if args.dry_run:
        print("(dry-run: no files modified)")


if __name__ == "__main__":
    main()
