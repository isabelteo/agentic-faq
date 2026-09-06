"""
title: Graphify Query
author: agentic-faq
version: 0.1.0
description: Uses graphify to query the knowledge graph and returns relevant content from source documents with a list of source filenames.
"""

import os
import re
import subprocess
from typing import List, Tuple, Dict
from collections import defaultdict

from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        graph_path: str = Field(
            default=r"C:\Users\isabe\OneDrive\文档\AgenticFAQ\agentic-faq\graphify-out",
            description="Path to the graphify output directory containing graph.json",
        )
        docs_path: str = Field(
            default=r"C:\Users\isabe\OneDrive\文档\AgenticFAQ\agentic-faq\data\documents_normalized",
            description="Absolute path to the folder containing the markdown documents.",
        )
        max_chars_per_doc: int = Field(
            default=30000,
            description="Truncate each returned document to this many characters (safety cap).",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _find_file_in_docs(self, filename: str) -> str | None:
        """
        Find a file in docs_path, searching nested folders if needed.
        Returns the relative path to the file, or None if not found.
        """
        # Try direct path first
        direct_path = os.path.join(self.valves.docs_path, filename)
        if os.path.exists(direct_path):
            return filename

        # Search in nested folders
        for root, dirs, files in os.walk(self.valves.docs_path):
            if filename in files:
                full_path = os.path.join(root, filename)
                return os.path.relpath(full_path, self.valves.docs_path)

        return None

    def _parse_graphify_output(self, output: str) -> Dict[str, Tuple[str, str]]:
        """
        Parse graphify query output to extract nodes and their source files.
        Returns a dict mapping source_file -> (node_label, node_id)
        """
        sources = {}
        node_pattern = r"NODE\s+(.+?)\s+\[src=(.+?)\s+loc="

        for match in re.finditer(node_pattern, output):
            label = match.group(1).strip()
            source = match.group(2).strip()
            if source and source != "multiple":
                sources[source] = label

        return sources

    def graphify_query(self, query: str) -> str:
        """
        Query the graphify knowledge graph for relevant content.
        Uses graphify query to find related entities and their source documents.

        :param query: The search query for the knowledge graph
        :return: JSON-formatted response with content and source filenames
        """
        try:
            # graphify expects to run from the parent directory of graphify-out
            parent_dir = os.path.dirname(self.valves.graph_path)
            result = subprocess.run(
                ["graphify", "query", query],
                cwd=parent_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )

            if result.returncode != 0:
                stderr = result.stderr if result.stderr else ""
                return f"Error running graphify query: {stderr}"

            stdout = result.stdout if result.stdout else ""
            stderr = result.stderr if result.stderr else ""
            output = stdout + stderr
            sources = self._parse_graphify_output(output)

            if not sources:
                return f"No relevant documents found for query: {query!r}"

            # Group by source file and read content
            file_contents = {}
            unique_sources = []

            for source_file in sorted(sources.keys()):
                relative_path = self._find_file_in_docs(source_file)

                if relative_path:
                    unique_sources.append(source_file)
                    file_path = os.path.join(self.valves.docs_path, relative_path)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="strict") as f:
                            content = f.read()[: self.valves.max_chars_per_doc]
                        file_contents[source_file] = content
                    except Exception as e:
                        file_contents[source_file] = f"Error reading file: {e}"

            # Format response with content and filenames
            chunks = []
            for source_file in unique_sources:
                content = file_contents.get(source_file, "")
                chunks.append(
                    f"### Document: {source_file}\n\n{content}"
                )

            if not unique_sources:
                return f"No source files found for query: {query!r}"

            response = "\n\n---\n\n".join(chunks)
            response += f"\n\n## Source Files:\n{', '.join(unique_sources)}"

            return response

        except subprocess.TimeoutExpired:
            return "Graphify query timed out"
        except FileNotFoundError:
            return "Graphify command not found. Make sure graphify is installed and in PATH."
        except Exception as e:
            return f"Error executing graphify query: {str(e)}"
