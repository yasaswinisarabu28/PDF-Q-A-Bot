import os
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

# Load environment variables (Groq API key lives in .env, never hardcoded)
load_dotenv()

# --- Configuration ---
CHROMA_PATH = "chroma_store"
COLLECTION_NAME = "pdf_chunks"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 4

# --- Initialize once ---
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

    query_filter = {"source": source_filename} if source_filename else None

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        where=query_filter
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
    """
    if chunks:
        if source_filename:
            context_text = "\n\n".join(
                f"[Page {c['page']}]: {c['text']}" for c in chunks
            )
        else:
            context_text = "\n\n".join(
                f"[{c['source']} - Page {c['page']}]: {c['text']}" for c in chunks
            )

        system_prompt = (
            "You are a helpful assistant answering questions about PDF document(s). "
            "Use ONLY the excerpts provided below to answer the question. "
            "Always cite the page number(s) you used, like (Page 3). "
            "If multiple documents are shown, mention which document each fact came from. "
            "If the excerpts don't fully answer the question, say what's missing.\n\n"
            "Match the length of your answer to what's actually being asked: "
            "for simple factual questions, answer in 2-4 sentences with no headers. "
            "Only use structure (short bullet points or brief sections) when the "
            "question explicitly asks for a comparison, evaluation, or a list of "
            "multiple distinct items. Never restate the question, never add a "
            "'Conclusion' section, and never list what the documents 'do not confirm' "
            "unless directly asked to assess something."
        )

        user_prompt = f"Excerpts:\n{context_text}\n\nQuestion: {question}"
    else:
        system_prompt = (
            "No relevant excerpts were found in the document(s) for this question. "
            "Answer using your own general knowledge instead, but start your answer "
            "by clearly stating: 'I couldn't find this in the document, so here's a "
            "general answer:' Keep the rest of your answer concise — 2-4 sentences "
            "unless the question specifically calls for more detail."
        )

        user_prompt = f"Question: {question}"

    return system_prompt, user_prompt


def ask_question(question: str, source_filename: str = None):
    """
    Full pipeline: retrieve -> build prompt -> call Groq -> return answer.
    """
    chunks = retrieve_chunks(question, source_filename=source_filename)
    system_prompt, user_prompt = build_prompt(
        question,
        chunks,
        source_filename=source_filename
    )

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


# --- Simple standalone test loop ---
if __name__ == "__main__":
    while True:
        q = input("\nAsk a question about the PDF (or 'exit'): ")

        if q.lower() == "exit":
            break

        answer = ask_question(q)
        print("\nAnswer:\n", answer)