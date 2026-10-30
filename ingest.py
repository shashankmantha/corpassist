"""
One-off (or on-startup) ingest: embed docs/ into the Chroma vector store.

Re-run this after planting the poisoned document (AI-02) so it lands in the index:
    python ingest.py
"""
import config
import rag

if __name__ == "__main__":
    n = rag.build_index()
    print(f"Ingested {n} chunk(s) from '{config.DOCS_DIR}/' into '{config.CHROMA_DIR}/'.")
