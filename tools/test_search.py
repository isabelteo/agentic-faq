"""
Standalone CLI to test document_search.py without running OpenWebUI.

Usage:
    .venv/Scripts/python.exe tools/test_search.py "large family schemes"
    .venv/Scripts/python.exe tools/test_search.py "large family schemes" --top-k 5
"""

import argparse
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from document_search import Tools, _index

_TITLE_RE = re.compile(r'^title:\s*"?(.*?)"?\s*$', re.MULTILINE)


def _extract_title(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        head = f.read(1000)
    match = _TITLE_RE.search(head)
    return match.group(1) if match else os.path.basename(path)

DEFAULT_DOCS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "documents"
)


def main():
    parser = argparse.ArgumentParser(description="Test the document_search tool from the CLI.")
    parser.add_argument("query", help="I have a large family and the new baby has autism. I am struggling. I don't know what to do.")
    parser.add_argument("--docs-path", default=DEFAULT_DOCS_PATH, help="Path to markdown documents")
    parser.add_argument("--top-k", type=int, default=3, help="Number of results to return")
    parser.add_argument("--full", action="store_true", help="Print full document content, not just a preview")
    args = parser.parse_args()

    tool = Tools()
    tool.valves.docs_path = args.docs_path
    tool.valves.top_k = args.top_k

    start = time.perf_counter()
    if args.full:
        result = tool.search_documents(args.query)
    else:
        _index.ensure_built(tool.valves.docs_path)
        result = _index.search(args.query, tool.valves.top_k, tool.valves.min_score)
    elapsed = time.perf_counter() - start

    print(f"Query: {args.query!r}")
    print(f"Time: {elapsed:.4f}s")
    print("-" * 60)
    if args.full:
        print(result)
    elif not result:
        print("No results.")
    else:
        for i, (path, score) in enumerate(result, 1):
            print(f"{i}. {_extract_title(path)}  (score: {score:.2f})")


if __name__ == "__main__":
    main()
