import os
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = "chroma_store"
COLLECTION_NAME = "pdf_chunks"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

embed_model = SentenceTransformer(EMBED_MODEL_NAME)
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)


def store_chunks(chunks: list, source_filename: str):
    """
    Embeds and stores chunks in ChromaDB, tagging each one with
    the PDF filename it came from (source_filename) so we can
    filter by document later.

    chunks: [{"page": n, "text": "..."}, ...]  (from chunk.py)
    source_filename: e.g. "x.pdf"
    """
    texts = [c["text"] for c in chunks]

    # Batch-embed all chunk texts at once (faster than one-by-one)
    embeddings = embed_model.encode(texts).tolist()

    # Build unique IDs that include the source, so chunk IDs never collide
    # across different PDFs (e.g. "x.pdf" and "y.pdf" both having a "chunk_0")
    ids = [f"{source_filename}_chunk_{i}" for i in range(len(chunks))]

    # Metadata now carries BOTH page number and source filename
    metadatas = [
        {"page": c["page"], "source": source_filename}
        for c in chunks
    ]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    print(f"Stored {len(chunks)} chunks from '{source_filename}'.")