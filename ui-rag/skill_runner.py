"""
Skill Runner v2 — RAG vectoriel (ChromaDB + nomic-embed-text).
Fallback automatique sur BM25 si l'index n'est pas construit.
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent / "skill" / "scripts"


# ── Fallback BM25 ─────────────────────────────────────────────────────────────

def _bm25_search(query: str, domain: str, max_results: int = 3) -> list:
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    import core as _core
    _core.DATA_DIR = Path(__file__).parent / "skill" / "data"
    result = _core.search(query, domain, max_results)
    return result.get("results", [])


def _bm25_stack(query: str, stack: str, max_results: int = 3) -> list:
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    import core as _core
    _core.DATA_DIR = Path(__file__).parent / "skill" / "data"
    result = _core.search_stack(query, stack, max_results)
    return result.get("results", [])


# ── RAG Search ────────────────────────────────────────────────────────────────

def _rag_search(query: str, stack: str = None, k: int = 10) -> list:
    from vector_store import get_store
    store = get_store()
    results = store.search(query, k=k)

    if stack:
        stack_results = store.search(f"{query} {stack}", k=4, domain_filter="stack")
        stack_results = [r for r in stack_results if r["metadata"].get("stack") == stack]
        seen = set()
        merged = []
        for r in stack_results + results:
            t = r["text"]
            if t not in seen:
                seen.add(t)
                merged.append(r)
        results = merged[:k]

    return results


def _chunks_to_context(chunks: list) -> dict:
    domain_map = {
        "style":      "styles",
        "color":      "colors",
        "typography": "typography",
        "ux":         "ux_guidelines",
        "stack":      "stack_guidelines",
        "product":    "products",
        "landing":    "landing",
    }
    context = {v: [] for v in domain_map.values()}

    for chunk in chunks:
        domain = chunk["metadata"].get("domain", "")
        key = domain_map.get(domain)
        if key:
            entry = dict(chunk["metadata"])
            entry["_text"] = chunk["text"]
            entry["_score"] = chunk["score"]
            context[key].append(entry)

    return {k: v for k, v in context.items() if v}


# ── Interface publique ────────────────────────────────────────────────────────

def build_context_for_ai(analysis: dict) -> dict:
    try:
        from vector_store import get_store
        store = get_store()

        if not store.is_built():
            print("⚠️  Index RAG absent → fallback BM25")
            print("   Lance 'python build_index.py' pour construire l'index.")
            return _build_context_bm25(analysis)

        rich_query = _build_rich_query(analysis)
        chunks = _rag_search(rich_query, stack=analysis.get("stack"), k=10)

        if not chunks:
            return _build_context_bm25(analysis)

        return _chunks_to_context(chunks)

    except ImportError:
        return _build_context_bm25(analysis)
    except Exception as e:
        print(f"⚠️  Erreur RAG ({e}) → fallback BM25")
        return _build_context_bm25(analysis)


def _build_rich_query(analysis: dict) -> str:
    parts = [
        analysis.get("original_query", ""),
        analysis.get("product_type", ""),
        " ".join(analysis.get("styles", [])),
        analysis.get("stack", ""),
    ]
    return " ".join(p for p in parts if p).strip()


def _build_context_bm25(analysis: dict) -> dict:
    q = analysis["skill_query"]
    stack = analysis["stack"]
    product = analysis["product_type"]
    raw = {
        "styles":           _bm25_search(q, "style", 3),
        "colors":           _bm25_search(product, "color", 2),
        "typography":       _bm25_search(q, "typography", 2),
        "ux_guidelines":    _bm25_search(q, "ux", 3),
        "stack_guidelines": _bm25_stack(q, stack, 2),
    }
    return {k: v for k, v in raw.items() if v}


def is_rag_available() -> bool:
    try:
        from vector_store import get_store
        return get_store().is_built()
    except Exception:
        return False
