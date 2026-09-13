from sentence_transformers import SentenceTransformer
import chromadb

def build_vector_store(chunks, persist_dir="./chroma_store", collection_name="pdf_docs"):
    """
    chunks: list of {"page": int, "text": str} dicts from chunk_all_pages()
    Embeds each chunk and stores it in a persistent ChromaDB collection.
    """
    model = SentenceTransformer('all-MiniLM-L6-v2')

    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts).tolist()  # ChromaDB expects plain lists, not numpy arrays
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"page": chunk["page"]} for chunk in chunks]

    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection(collection_name)

    collection.add(
        documents=texts,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas
    )

    return collection


if __name__ == "__main__":
    from extract import extract_pages
    from chunk import chunk_all_pages

    pages = extract_pages("sample.pdf")
    chunks = chunk_all_pages(pages)
    collection = build_vector_store(chunks)
    print(f"Stored {collection.count()} chunks in ChromaDB.")