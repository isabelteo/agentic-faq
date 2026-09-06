"""
title: Document Search
author: agentic-faq
version: 0.1.0
description: Searches the local data/documents markdown knowledge base with BM25 keyword search and returns the full text of the most relevant documents.
requirements: rank_bm25
"""

import os
import re
from typing import List, Tuple

from pydantic import BaseModel, Field
from rank_bm25 import BM25Okapi

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_MIN_TOKEN_LEN = 2


def _tokenize(text: str) -> List[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if len(t) >= _MIN_TOKEN_LEN]


class _Index:
    """Lazily-built, cached BM25 index over all markdown files under docs_path."""

    def __init__(self):
        self.docs_path = None
        self.paths: List[str] = []
        self.corpus: List[List[str]] = []
        self.bm25: BM25Okapi = None

    def ensure_built(self, docs_path: str):
        if not docs_path or not isinstance(docs_path, str):
            raise ValueError("docs_path must be a non-empty string")
        if not os.path.isdir(docs_path):
            raise FileNotFoundError(f"docs_path does not exist or is not a directory: {docs_path!r}")
        if self.bm25 is not None and self.docs_path == docs_path:
            return
        candidate_paths = []
        for root, _dirs, files in os.walk(docs_path):
            for name in files:
                if name.lower().endswith(".md"):
                    candidate_paths.append(os.path.join(root, name))

        self.docs_path = docs_path
        self.paths = []
        self.corpus = []
        for path in candidate_paths:
            with open(path, "r", encoding="utf-8", errors="strict") as f:
                tokens = _tokenize(f.read())
            if tokens:
                self.paths.append(path)
                self.corpus.append(tokens)
        self.bm25 = BM25Okapi(self.corpus) if self.corpus else None

    def search(self, query: str, top_k: int, min_score: float) -> List[Tuple[str, float]]:
        if self.bm25 is None:
            return []
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []
        scores = self.bm25.get_scores(query_tokens)
        ranked = sorted(zip(self.paths, scores), key=lambda x: x[1], reverse=True)
        effective_min_score = max(min_score, 1e-9)
        return [(path, score) for path, score in ranked[:top_k] if score >= effective_min_score]


_index = _Index()


class Tools:
    class Valves(BaseModel):
        docs_path: str = Field(
            default=r"C:\Users\isabe\OneDrive\文档\AgenticFAQ\agentic-faq\data\documents",
            description="Absolute path to the folder containing the markdown documents to search.",
        )
        top_k: int = Field(
            default=8,
            description="Number of top matching documents to return.",
        )
        min_score: float = Field(
            default=5.0,
            description="Minimum BM25 score for a document to be included. Raise this to be stricter about relevance; documents with no keyword overlap are always excluded regardless of this setting.",
        )
        max_chars_per_doc: int = Field(
            default=30000,
            description="Truncate each returned document to this many characters (safety cap).",
        )

    def __init__(self):
        self.valves = self.Valves()

    def search_documents(self, query: str) -> str:
        """
        Search the local knowledge base of Singapore government schemes and guides
        for documents relevant to the query, and return their full content so it can
        be used to answer the user's question.
        :param query: The search query, e.g. a scheme name, topic, or the user's question.
        """
        _index.ensure_built(self.valves.docs_path)
        results = _index.search(query, self.valves.top_k, self.valves.min_score)

        if not results:
            return f"No relevant documents found for query: {query!r}"

        chunks = []
        for path, score in results:
            rel_name = os.path.relpath(path, self.valves.docs_path)
            with open(path, "r", encoding="utf-8", errors="strict") as f:
                content = f.read()[: self.valves.max_chars_per_doc]
            chunks.append(
                f"### Document: {rel_name} (relevance score: {score:.2f})\n\n{content}"
            )

        return "\n\n---\n\n".join(chunks)
