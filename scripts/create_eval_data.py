#!/usr/bin/env python3
"""
Generate evaluation data (queries.jsonl and qrels.json) for the Knowledge Search project.
This script scans the processed documents to match queries with relevant documents using keyword matching.
"""

import json
from pathlib import Path
import re

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_JSONL = PROJECT_ROOT / "data" / "processed" / "docs.jsonl"
QUERIES_JSONL = PROJECT_ROOT / "data" / "eval" / "queries.jsonl"
QRELS_JSON = PROJECT_ROOT / "data" / "eval" / "qrels.json"

QUERIES = [
    # Character-specific
    {"query_id": "q01", "query": "Elizabeth Bennet marriage"},
    {"query_id": "q02", "query": "Sherlock Holmes detective"},
    {"query_id": "q03", "query": "Mr. Darcy proposal"},
    {"query_id": "q04", "query": "Alice rabbit hole"},
    {"query_id": "q05", "query": "Dr. Frankenstein ambition"},
    
    # Theme-based
    {"query_id": "q06", "query": "monster creation horror"},
    {"query_id": "q07", "query": "whaling at sea"},
    {"query_id": "q08", "query": "french revolution guillotine"},
    {"query_id": "q09", "query": "social class prejudice"},
    {"query_id": "q10", "query": "madness and isolation"},
    
    # Cross-book
    {"query_id": "q11", "query": "Christmas celebration"},
    {"query_id": "q12", "query": "river adventure"},
    {"query_id": "q13", "query": "scientific discovery ethics"},
    {"query_id": "q14", "query": "unjust imprisonment"},
    {"query_id": "q15", "query": "supernatural haunting"},
    
    # Specific scenes
    {"query_id": "q16", "query": "tea party with mad hatter"},
    {"query_id": "q17", "query": "ghost of Christmas past"},
    {"query_id": "q18", "query": "whale attack Pequod"},
    {"query_id": "q19", "query": "monster meets creator"},
    {"query_id": "q20", "query": "London fog mystery"},
    
    # Abstract
    {"query_id": "q21", "query": "social class and prejudice"},
    {"query_id": "q22", "query": "science gone wrong"},
    {"query_id": "q23", "query": "nature of evil"},
    {"query_id": "q24", "query": "sacrifice and resurrection"},
    {"query_id": "q25", "query": "youth and corruption"},
]

def tokenize(text):
    """Simple tokenizer for matching."""
    return set(re.findall(r'[a-z0-9]+', text.lower()))

def main():
    print(f"Reading documents from {DOCS_JSONL}...")
    if not DOCS_JSONL.exists():
        print(f"Error: {DOCS_JSONL} not found.")
        return

    documents = []
    with open(DOCS_JSONL, 'r', encoding='utf-8') as f:
        for line in f:
            documents.append(json.loads(line))

    print(f"Loaded {len(documents)} documents.")

    qrels = {}
    
    # Ensure eval directory exists
    QUERIES_JSONL.parent.mkdir(parents=True, exist_ok=True)

    with open(QUERIES_JSONL, 'w', encoding='utf-8') as qf:
        for q_entry in QUERIES:
            query_id = q_entry["query_id"]
            query_text = q_entry["query"]
            query_tokens = tokenize(query_text)
            
            # Write queries.jsonl
            qf.write(json.dumps(q_entry) + "\n")
            
            relevant_docs = {}
            for doc in documents:
                doc_text = (doc.get("title", "") + " " + doc.get("text", "")).lower()
                doc_tokens = tokenize(doc_text)
                
                # Count matching tokens
                matches = len(query_tokens.intersection(doc_tokens))
                
                if matches >= 3:
                    relevant_docs[doc["doc_id"]] = 2
                elif matches >= 1:
                    # For very short queries, 1-2 might be enough for grade 2, but let's stick to the rules
                    relevant_docs[doc["doc_id"]] = 1
            
            # Filter to keep at most 10 best (if many) or at least 3 (if available)
            # Re-sort to prioritize grade 2
            sorted_docs = sorted(relevant_docs.items(), key=lambda x: x[1], reverse=True)
            
            # We want at least 3-10 relevant docs per query.
            # If we have too many, we take the top 10.
            # We don't discard if we have fewer than 10, as long as we have 3+.
            # If we have < 3, we just keep what we have.
            final_relics = dict(sorted_docs[:10])
            qrels[query_id] = final_relics

    print(f"Writing qrels to {QRELS_JSON}...")
    with open(QRELS_JSON, 'w', encoding='utf-8') as jf:
        json.dump(qrels, jf, indent=2)

    # Summary
    total_relevant = sum(len(docs) for docs in qrels.values())
    avg_relevant = total_relevant / len(QUERIES)
    
    print("\nSummary:")
    print(f"Queries generated: {len(QUERIES)}")
    print(f"Average relevant docs per query: {avg_relevant:.2f}")
    print(f"Files created: {QUERIES_JSONL} and {QRELS_JSON}")

if __name__ == "__main__":
    main()
