# 📄 PDF Q&A Bot

A Retrieval-Augmented Generation (RAG) application that lets you upload one or more PDFs and ask natural-language questions about their content — with answers grounded in the actual document text and cited by page number. Falls back to general knowledge (clearly labeled) when the answer isn't found in the uploaded documents.

Built as Project 1 of a 5-project AI/GenAI portfolio series.

---

## Features

- 📤 Upload and manage multiple PDFs, with the option to delete any of them
- 🔍 Semantic search over document content (not just keyword matching)
- 📌 Answers cite the exact page number(s) they came from, shown as styled citation tabs
- 🗂️ Query a single PDF, or search across all uploaded PDFs at once
- 🧠 Falls back to general knowledge (clearly labeled) if nothing relevant is found in the documents
- ✂️ Answers are length-adaptive — concise for simple factual questions, more structured for comparison/evaluation questions
- 💬 Chat-style interface with a collapsible sidebar, in the style of modern AI chat apps
- 🕘 Recent-questions history (saved locally in the browser) for quick re-asking
- 🖥️ Custom Flask + HTML/CSS/JS frontend — no third-party UI library

---

## Architecture

```
                         ┌─────────────────┐
                         │   Upload PDF    │
                         └────────┬────────┘
                                  ▼
                         ┌─────────────────┐
                         │   extract.py    │  PyMuPDF: page-by-page
                         │  extract_pages()│  text extraction
                         └────────┬────────┘
                                  ▼
                         ┌─────────────────┐
                         │    chunk.py     │  Sentence-aware chunking
                         │ chunk_all_pages()│ with overlap (char-length based)
                         └────────┬────────┘
                                  ▼
                         ┌─────────────────┐
                         │ embed_store.py  │  SentenceTransformers embeds
                         │  store_chunks() │  chunks → stored in ChromaDB
                         │                 │  (tagged with source filename)
                         └────────┬────────┘
                                  ▼
                         ┌─────────────────┐
                         │   ChromaDB      │  Persistent vector store
                         │  (chroma_store) │  supports delete-by-source
                         └────────┬────────┘
                                  ▲
                                  │  similarity search (top-k, filtered
                                  │  by source PDF if one is selected)
                         ┌────────┴────────┐
                         │    query.py     │  Embeds question → retrieves
                         │  ask_question() │  chunks → builds grounded,
                         │                 │  length-adaptive prompt →
                         │                 │  calls Groq LLM
                         └────────┬────────┘
                                  ▼
                         ┌─────────────────┐
                         │  Groq LLM       │  openai/gpt-oss-120b
                         │                 │  generates cited answer
                         └────────┬────────┘
                                  ▼
                         ┌─────────────────┐
                         │    app.py       │  Flask backend
                         │  /  /upload     │  serves the web UI and
                         │  /ask  /delete  │  exposes the API routes
                         └────────┬────────┘
                                  ▼
                         ┌─────────────────┐
                         │  Browser UI     │  Sidebar (shelf + recent
                         │ (HTML/CSS/JS)   │  questions) + chat log with
                         │                 │  markdown-rendered answers
                         └─────────────────┘
```

**Pipeline stages:**

1. **Extract** — `extract.py` (`extract_pages`) pulls text from each PDF page using PyMuPDF, skipping empty/image-only pages.
2. **Chunk** — `chunk.py` (`chunk_all_pages`) splits text into overlapping, sentence-aware chunks (sized by character length) so no sentence is cut mid-way and context isn't lost at chunk boundaries.
3. **Embed & Store** — `embed_store.py` (`store_chunks`) converts chunks into vector embeddings (`all-MiniLM-L6-v2`) and stores them in a persistent ChromaDB collection, tagged with page number and source filename — one shared collection for all PDFs, filtered by metadata rather than split into separate collections.
4. **Retrieve** — `query.py` (`retrieve_chunks`) embeds the user's question and retrieves the most similar chunks via cosine similarity, optionally filtered to a specific PDF via ChromaDB's `where` clause.
5. **Generate** — Retrieved chunks are passed to Groq's `openai/gpt-oss-120b`, which answers strictly from the provided excerpts, cites page numbers, adapts its answer length to the question type, and falls back to general knowledge (clearly labeled) if nothing relevant was retrieved.
6. **Serve** — `app.py` exposes this pipeline through a Flask backend (`/upload`, `/ask`, `/delete`) and a custom HTML/CSS/JS chat interface.

---

## Tech Stack

| Component | Tool |
|---|---|
| PDF text extraction | PyMuPDF (`pymupdf`) |
| Chunking | Custom sentence-aware chunker |
| Embeddings | SentenceTransformers (`all-MiniLM-L6-v2`) |
| Vector store | ChromaDB (persistent, local) |
| LLM | Groq (`openai/gpt-oss-120b`) |
| Backend | Flask |
| Frontend | Custom HTML/CSS/JS, `marked.js` for markdown rendering |
| Config | python-dotenv |

---

## Project Structure

```
PDF-Q-A-Bot/
├── extract.py             # PDF → page-wise text (extract_pages)
├── chunk.py                # Sentence-aware chunking (chunk_all_pages)
├── embed_store.py           # Embed chunks + store in ChromaDB (store_chunks)
├── query.py                  # Retrieve + generate grounded, adaptive answers
├── app.py                     # Flask backend (routes + server)
├── templates/
│   └── index.html               # Sidebar + chat UI
├── static/
│   ├── style.css                 # Reading-desk visual design
│   └── script.js                  # Upload / ask / delete / history logic
├── uploaded_pdfs/           # Uploaded PDFs (gitignored)
├── requirements.txt
├── .env                      # GROQ_API_KEY (not committed)
├── .gitignore
└── README.md
```

---

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/yasaswinisarabu28/PDF-Q-A-Bot.git
   cd PDF-Q-A-Bot
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Add your Groq API key**
   Create a `.env` file in the project root:
   ```
   GROQ_API_KEY=your_actual_key_here
   ```

---

## Usage

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

- Click **"Add a PDF"** in the sidebar to upload and process a document.
- Use the **"Asking about"** dropdown to scope questions to one PDF or search across all of them.
- Type a question at the bottom of the chat panel and hit **Ask** (or Enter).
- Click the **☰** icon to collapse/expand the sidebar.
- Click the **×** on any shelf card to remove that PDF and its stored chunks.
- Your last 8 questions appear under **"Recent questions"** — click one to reuse it.

---

## Example

> **Question:** What is the main topic discussed on the first few pages?
>
> **Answer:** The document introduces [topic], covering [key points] `p. 1` `p. 2`.

If the answer isn't in the uploaded PDF:

> **Answer:** I couldn't find this in the document, so here's a general answer: [general knowledge response]

---

## Design Notes

- **Why sentence-aware chunking instead of fixed character cuts?** Fixed-length chunking can slice a sentence in half, corrupting the meaning captured in its embedding. Overlap between chunks further ensures ideas spanning a chunk boundary aren't lost.
- **Why tag chunks with a `source` field instead of separate ChromaDB collections per PDF?** A single collection with metadata filtering keeps single-document and cross-document queries both possible without restructuring the database — you can ask about one PDF, delete one PDF's chunks by filtering on `source`, or compare across several, all through the same query path.
- **Why fall back to general knowledge?** A strictly document-only bot returns unhelpful "not found" answers whenever retrieval comes up empty. Falling back — while clearly labeling that the answer isn't from the document — keeps the tool useful without misleading the user about where the answer came from.
- **Why adapt answer length to the question type?** Grounded, citation-heavy prompting tends to make LLMs over-explain by default. Instructing the model to match structure to question type (short answers for factual questions, brief structure for comparison/evaluation questions) keeps answers useful without turning every response into a report.
- **Why a custom Flask UI instead of Gradio/Streamlit?** Faster prebuilt UI libraries are a reasonable choice for a quick demo, but a hand-built frontend better demonstrates full-stack ability and allows a visual identity (the "reading desk" theme, citation tabs, chat-style layout) that a component library wouldn't offer out of the box.

---

## Roadmap

This is Project 1 of a 5-project portfolio series:

1. **PDF Q&A Bot** *(this project)*
2. Structured Data Extractor (Pydantic-focused)
3. Multi-Tool Research Agent
4. MCP Server + Client
5. Capstone: Agentic RAG Assistant

**Possible future additions to this project:** PowerPoint (`.pptx`) support via `python-pptx`, a similarity-score threshold for the general-knowledge fallback, persistent (server-side) chat history.

---

## License

MIT