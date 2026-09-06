#!/usr/bin/env python3
"""
Flattens the scraped firecrawl/ and web-scraper/ JSON outputs into plain
markdown files under /documents (grouped by their original site subfolder,
not by which scraper produced them), suitable for ingestion by a RAG tool
(Open WebUI, AnythingLLM, a custom embedding pipeline, etc).

Each output file gets a YAML frontmatter block (title, description,
source_url) followed by the page's markdown body.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    "firecrawl": REPO_ROOT / "data" / "scripts" / "output" / "firecrawl",
    "web-scraper": REPO_ROOT / "data" / "scripts" / "output" / "web-scraper",
}
OUTPUT_DIR = REPO_ROOT / "documents"


def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "page"


def slug_from_url(url):
    path = re.sub(r"^https?://[^/]+", "", url).rstrip("/")
    return slugify(path.replace("/", "-"))


def clean_title(title, metadata):
    """Strip a trailing " - <site name>" suffix (e.g. "- SupportGoWhere"),
    using og_title's generic first entry as the site name when available."""
    og_title = metadata.get("og_title")
    if isinstance(og_title, list):
        site_name = og_title[0] if og_title else None
    else:
        site_name = og_title or None
    if site_name:
        suffix = f" - {site_name}"
        if title.endswith(suffix):
            title = title[: -len(suffix)]
    return title.strip()


def extract_fields(payload, prefer_og_description=False):
    data = payload.get("data", {}) or {}
    metadata = data.get("metadata", {}) or {}

    title = metadata.get("title") or metadata.get("og_title") or ""
    if isinstance(title, list):
        title = title[-1] if title else ""
    title = clean_title(title.strip(), metadata)

    description = metadata.get("description") or metadata.get("og_description") or ""

    markdown = data.get("markdown") or ""
    og_description = metadata.get("og_description") or data.get("og_description") or ""

    if prefer_og_description:
        body = og_description or markdown
    else:
        body = markdown or og_description

    source_url = payload.get("source_url") or metadata.get("source_url") or metadata.get("url") or ""

    return title.strip(), description.strip(), body.strip(), source_url.strip()


def yaml_escape(value):
    return value.replace('"', '\\"').replace("\n", " ")


def write_document(out_path, title, description, source_url, body):
    frontmatter = (
        "---\n"
        f'title: "{yaml_escape(title)}"\n'
        f'description: "{yaml_escape(description)}"\n'
        f'source_url: "{yaml_escape(source_url)}"\n'
        "---\n\n"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(frontmatter + body + "\n", encoding="utf-8")


def unique_path(directory, stem):
    candidate = directory / f"{stem}.md"
    if not candidate.exists():
        return candidate
    i = 2
    while (directory / f"{stem}-{i}.md").exists():
        i += 1
    return directory / f"{stem}-{i}.md"


def process_source(source_dir):
    count = 0
    skipped = 0
    for json_path in sorted(source_dir.rglob("*.json")):
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"  SKIP (unreadable): {json_path.relative_to(source_dir)} ({e})")
            skipped += 1
            continue

        title, description, body, source_url = extract_fields(payload)

        if not body:
            print(f"  SKIP (no content): {json_path.relative_to(source_dir)}")
            skipped += 1
            continue

        rel_dir = json_path.parent.relative_to(source_dir)
        out_dir = OUTPUT_DIR / rel_dir

        stem = slug_from_url(source_url) if source_url else json_path.stem
        out_path = unique_path(out_dir, stem)

        write_document(out_path, title, description, source_url, body)
        count += 1

    return count, skipped


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    total_skipped = 0
    for source_name, source_dir in SOURCES.items():
        if not source_dir.exists():
            print(f"Source directory not found, skipping: {source_dir}")
            continue
        print(f"Processing {source_name} ({source_dir}) ...")
        count, skipped = process_source(source_dir)
        print(f"  -> {count} documents written, {skipped} skipped")
        total += count
        total_skipped += skipped

    print(f"\nDone. {total} documents written to {OUTPUT_DIR}, {total_skipped} skipped.")


if __name__ == "__main__":
    main()
