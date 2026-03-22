"""
Vector Store — interface ChromaDB + nomic-embed-text (via Ollama).
Gère l'embedding, le stockage et la recherche sémantique.
"""

import json
import urllib.request
import urllib.error
from pathlib import Path

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text:latest"
DB_DIR = Path(__file__).parent / "vectordb"
COLLECTION_NAME = "uiux_knowledge"


# ── Embedding via Ollama ──────────────────────────────────────────────────────

def embed(text: str) -> list[float]:
    """Encode un texte en vecteur via nomic-embed-text."""
    payload = json.dumps({
        "model": EMBED_MODEL,
        "prompt": text
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_EMBED_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["embedding"]
    except urllib.error.URLError as e:
        raise ConnectionError(f"Ollama embed indisponible: {e}")


def embed_batch(texts: list[str], show_progress: bool = False) -> list[list[float]]:
    """Encode une liste de textes, un par un (Ollama n'a pas de batch natif)."""
    vectors = []
    total = len(texts)
    for i, text in enumerate(texts):
        if show_progress and i % 50 == 0:
            print(f"  Embedding {i}/{total}...", end="\r", flush=True)
        vectors.append(embed(text))
    if show_progress:
        print(f"  Embedding {total}/{total} ✓          ")
    return vectors


# ── ChromaDB Store ────────────────────────────────────────────────────────────

class VectorStore:
    """
    Interface ChromaDB pour stocker et chercher les chunks UI/UX.
    Utilise un stockage persistant local dans ./vectordb/
    """

    def __init__(self):
        self._client = None
        self._collection = None

    def _get_client(self):
        if self._client is None:
            try:
                import chromadb
                self._client = chromadb.PersistentClient(path=str(DB_DIR))
            except ImportError:
                raise ImportError(
                    "ChromaDB non installé.\n"
                    "Lance: pip install chromadb"
                )
        return self._client

    def _get_collection(self):
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def count(self) -> int:
        """Nombre de chunks dans la base."""
        try:
            return self._get_collection().count()
        except Exception:
            return 0

    def is_built(self) -> bool:
        """Vérifie si l'index est déjà construit."""
        return self.count() > 0

    @staticmethod
    def _sanitize(metadata: dict) -> dict:
        """ChromaDB n'accepte que str, int, float, bool. None → '' """
        clean = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
            elif v is None:
                clean[k] = ""
            else:
                clean[k] = str(v)
        return clean

    def add(self, chunks: list[dict]):
        """
        Ajoute des chunks à la base.
        Chaque chunk : {"id": str, "text": str, "metadata": dict}
        """
        collection = self._get_collection()

        ids = [c["id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [self._sanitize(c["metadata"]) for c in chunks]

        print(f"  Calcul des embeddings ({len(chunks)} chunks)...")
        vectors = embed_batch(texts, show_progress=True)

        collection.add(
            ids=ids,
            embeddings=vectors,
            documents=texts,
            metadatas=metadatas
        )

    def search(self, query: str, k: int = 8, domain_filter: str = None) -> list[dict]:
        """
        Recherche sémantique : retourne les k chunks les plus proches.

        Args:
            query: texte de recherche
            k: nombre de résultats
            domain_filter: filtre optionnel sur le domaine (ex: "style", "ux")

        Returns:
            liste de dicts avec {text, metadata, score}
        """
        collection = self._get_collection()

        if collection.count() == 0:
            return []

        query_vector = embed(query)

        where = {"domain": domain_filter} if domain_filter else None

        results = collection.query(
            query_embeddings=[query_vector],
            n_results=min(k, collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"]
        )

        output = []
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        for doc, meta, dist in zip(docs, metas, dists):
            score = 1 - dist  # cosine distance → similarity
            output.append({
                "text": doc,
                "metadata": meta,
                "score": round(score, 3)
            })

        return output

    def reset(self):
        """Supprime et recrée la collection."""
        client = self._get_client()
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        self._collection = None
        self._get_collection()
        print("Collection réinitialisée.")


# Singleton
_store = None

def get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store