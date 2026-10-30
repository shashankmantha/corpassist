"""
CorpAssist retrieval (RAG) over a folder of fake internal documents.

A persistent Chroma collection with local sentence-transformers embeddings.
No network: embeddings run locally, the store is on disk.

AI-02 — the indexed folder (config.DOCS_DIR) is trusted implicitly. Any file
dropped in it, including an attacker-planted "poisoned" document, becomes
retrievable context. There is no validation on ingest.
"""
import glob
import os

import chromadb
from chromadb.utils import embedding_functions

import config

_COLLECTION = "corpassist"


def _client():
    return chromadb.PersistentClient(path=config.CHROMA_DIR)


def _embed_fn():
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=config.EMBED_MODEL
    )


def build_index() -> int:
    """(Re)build the vector store from every *.md in config.DOCS_DIR.

    Returns the number of chunks indexed. Run via ingest.py or on container start.
    """
    client = _client()
    try:
        client.delete_collection(_COLLECTION)
    except Exception:
        pass
    col = client.get_or_create_collection(_COLLECTION, embedding_function=_embed_fn())

    docs, ids, metas = [], [], []
    for path in sorted(glob.glob(os.path.join(config.DOCS_DIR, "*.md"))):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        # naive paragraph chunking — fine for a toy corpus
        chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
        for i, chunk in enumerate(chunks):
            docs.append(chunk)
            ids.append(f"{os.path.basename(path)}::{i}")
            metas.append({"source": os.path.basename(path)})

    if docs:
        col.add(documents=docs, ids=ids, metadatas=metas)
    return len(docs)


def search(query: str, k: int | None = None):
    """Return up to k (chunk_text, source_filename) pairs for the query."""
    k = k or config.TOP_K
    col = _client().get_or_create_collection(_COLLECTION, embedding_function=_embed_fn())
    res = col.query(query_texts=[query], n_results=k)
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    sources = [m.get("source", "?") for m in metas]
    return list(zip(docs, sources))
