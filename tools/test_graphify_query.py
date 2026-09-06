#!/usr/bin/env python3
"""
Test script for graphify_query tool
Run from the tools directory: python test_graphify_query.py
"""

import sys
import os
from pathlib import Path

# Get the tools directory and project root
TOOLS_DIR = Path(__file__).parent
BASE_DIR = TOOLS_DIR.parent

# Force reload if module was already imported
if 'graphify_query' in sys.modules:
    del sys.modules['graphify_query']

from graphify_query import Tools

print("=" * 60)
print("GRAPHIFY_QUERY TOOL - LOCAL TEST")
print("=" * 60)

tool = Tools()
print(f"\nTool Configuration:")
print(f"  Graph path: {tool.valves.graph_path}")
print(f"  Docs path: {tool.valves.docs_path}")
print(f"  Max chars per doc: {tool.valves.max_chars_per_doc}")

# Test with different queries
test_queries = [
    "low income bring foreign spouse to Singapore to work what needs to do spouse work pass requirements Singapore citizen PR sponsor",
    "financial assistance",
    "medical aid",
]

for query in test_queries:
    print(f"\n{'─' * 60}")
    print(f"Testing query: '{query}'")
    print(f"{'─' * 60}")

    response = tool.graphify_query(query)
    print(f"\nResponse:\n{response}")

print(f"\n{'=' * 60}")
print("TEST COMPLETE")
print("=" * 60)
