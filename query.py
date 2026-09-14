import os
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

# Load environment variables (Groq API key lives in .env, never hardcoded)
load_dotenv()

# --- Configuration ---
CHROMA_PATH = "chroma_store"          # must match the path used in embed_store.py
COLLECTION_NAME = "pdf_chunks"        # must match the collection name in embed_store.py
EMBED_MODEL_NAME = "all-MiniLM-L6-v2" # must match the model used to embed the chunks
TOP_K = 4                              # how many chunks to retrieve per question

# --- Initialize once (not inside the loop, so we don't reload models every question) ---
embed_model = SentenceTransformer(EMBED_MODEL_NAME)
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def retrieve_chunks(question: str, source_filename: str = None, top_k: int = TOP_K):
    """
    Embeds the question and finds the top_k most similar chunks.
    If source_filename is given, only searches chunks from that PDF.
    If source_filename is None, searches across ALL stored PDFs.
    """
    question_embedding = embed_model.encode(question).tolist()

    # 'where' is Chroma's filter syntax — only applied if source_filename given
    query_filter = {"source": source_filename} if source_filename else None

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        where=query_filter,   # None means "no filter, search everything"
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    chunks = []
    for doc, meta in zip(documents, metadatas):
        chunks.append({
            "text": doc,
            "page": meta.get("page", "unknown"),
            "source": meta.get("source", "unknown"),
        })

    return chunks


def build_prompt(question: str, chunks: list, source_filename: str = None):
    """
    Builds the prompt sent to the LLM.
    - If chunks were retrieved: answer strictly from them, cite pages
      (and cite source filenames too, if searching across multiple PDFs).
    - If chunks is empty: fall back to general knowledge, but say so clearly.
    """
    if chunks:
        if source_filename:
            # Scoped to one PDF — page number alone is enough context
            context_text = "\n\n".join(
                f"[Page {c['page']}]: {c['text']}" for c in chunks
            )
        else:
            # Searching across all PDFs — label each excerpt with its source too
            context_text = "\n\n".join(
                f"[{c['source']} - Page {c['page']}]: {c['text']}" for c in chunks
            )

        system_prompt = (
            "You are a helpful assistant answering questions about PDF document(s). "
            "Use ONLY the excerpts provided below to answer the question. "
            "Always cite the page number(s) you used, like (Page 3). "
            "If multiple documents are shown, mention which document each fact came from. "
            "If the excerpts don't fully answer the question, say what's missing."
        )
        user_prompt = f"Excerpts:\n{context_text}\n\nQuestion: {question}"
    else:
        # No relevant chunks found — fall back to general knowledge
        system_prompt = (
            "No relevant excerpts were found in the document(s) for this question. "
            "Answer using your own general knowledge instead, but start your "
            "answer by clearly stating: 'I couldn't find this in the document, "
            "so here's a general answer:'"
        )
        user_prompt = f"Question: {question}"

    return system_prompt, user_prompt


def ask_question(question: str, source_filename: str = None):
    """
    Full pipeline: retrieve -> build prompt -> call Groq -> return answer.
    source_filename: pass a specific PDF's filename to scope the search,
    or None to search across all stored PDFs.
    """
    chunks = retrieve_chunks(question, source_filename=source_filename)
    system_prompt, user_prompt = build_prompt(question, chunks, source_filename=source_filename)

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,  # low temperature -> grounded, not "creative"
    )

    return response.choices[0].message.content


# --- Simple standalone test loop (main.py replaces this with the full menu) ---
if __name__ == "__main__":
    while True:
        q = input("\nAsk a question about the PDF (or 'exit'): ")
        if q.lower() == "exit":
            break
        answer = ask_question(q)
        print("\nAnswer:\n", answer)