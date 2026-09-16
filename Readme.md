# 📄 PDF Q&A Bot

A Retrieval-Augmented Generation (RAG) application that lets you upload one or more PDFs and ask natural-language questions about their content — with answers grounded in the actual document text and cited by page number. Falls back to general knowledge when the answer isn't found in the uploaded documents.

Built as part of a 5-project AI/GenAI portfolio series.

---

## Features

- 📤 Upload one or multiple PDFs
- 🔍 Semantic search over document content (not just keyword matching)
- 📌 Answers cite the exact page number(s) they came from
- 🗂️ Query a single PDF, or search across all uploaded PDFs at once
- 🧠 Falls back to general knowledge (clearly labeled) if nothing relevant is found in the documents
- 🖥️ Two interfaces: a terminal CLI (`main.py`) and a browser-based UI (`app.py`, built with Gradio)

---

## Architecture

```
                         ┌─────────────────┐
                         │   Upload PDF    │
                         └────────┬────────┘
                                  ▼
                         ┌─────────────────┐
                         │   extract.py    │  PyMuPDF: page-by-page
                         │                 │  text extraction
                         └────────┬────────┘
                                  ▼
                         ┌─────────────────┐
                         │    chunk.py     │  Sentence-aware chunking
                         │                 │  with overlap
                         └────────┬────────┘
                                  ▼
                         ┌─────────────────┐
                         │ embed_store.py  │  SentenceTransformers embeds
                         │                 │  chunks → stored in ChromaDB
                         │                 │  (tagged with source filename)
                         └────────┬────────┘
                                  ▼
                         ┌─────────────────┐
                         │   ChromaDB      │  Persistent vector store
                         │  (chroma_store) │
                         └────────┬────────┘
                                  ▲
                                  │  similarity search (top-k, filtered
                                  │  by source PDF if one is selected)
                         ┌────────┴────────┐
                         │    query.py     │  Embeds question → retrieves
                         │                 │  chunks → builds grounded
                         │                 │  prompt → calls Groq LLM
                         └────────┬────────┘
                                  ▼
                         ┌─────────────────┐
                         │  Groq LLM       │  llama-3.3-70b-versatile
                         │                 │  generates cited answer
                         └────────┬────────┘
                                  ▼
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
            ┌───────────────┐           ┌───────────────┐
            │   main.py     │           │    app.py     │
            │  (Terminal    │           │  (Gradio Web  │
            │   CLI menu)   │           │      UI)      │
            └───────────────┘           └───────────────┘
```

**Pipeline stages:**

1. **Extract** — `extract.py` pulls text from each PDF page using PyMuPDF, skipping empty/image-only pages.
2. **Chunk** — `chunk.py` splits text into overlapping, sentence-aware chunks so no sentence is cut mid-way and context isn't lost at chunk boundaries.
3. **Embed & Store** — `embed_store.py` converts chunks into vector embeddings (`all-MiniLM-L6-v2`) and stores them in a persistent ChromaDB collection, tagged with page number and source filename.
4. **Retrieve** — `query.py` embeds the user's question and retrieves the most similar chunks via cosine similarity, optionally filtered to a specific PDF.
5. **Generate** — Retrieved chunks are passed to Groq's `llama-3.3-70b-versatile`, which answers strictly from the provided excerpts and cites page numbers — or falls back to general knowledge (clearly labeled) if nothing relevant was retrieved.

---

## Tech Stack

| Component | Tool |
|---|---|
| PDF text extraction | PyMuPDF |
| Chunking | Custom sentence-aware chunker |
| Embeddings | SentenceTransformers (`all-MiniLM-L6-v2`) |
| Vector store | ChromaDB (persistent, local) |
| LLM | Groq (`llama-3.3-70b-versatile`) |
| Web UI | Gradio |
| Config | python-dotenv |

---

## Project Structure

```
PDF-Q-A-Bot/
├── extract.py          # PDF → page-wise text
├── chunk.py             # Sentence-aware chunking with overlap
├── embed_store.py        # Embed chunks + store in ChromaDB
├── query.py              # Retrieve + generate grounded answers
├── main.py                # Terminal CLI (menu-driven)
├── app.py                  # Gradio web UI
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

**Web UI (recommended):**
```bash
python app.py
```
Opens in your browser at `http://127.0.0.1:7860`. Upload a PDF, wait for it to process, pick it (or "All PDFs") from the dropdown, and start asking questions.

**Terminal CLI:**
```bash
python main.py
```
Follow the numbered menu to add PDFs and ask questions.

---

## Example

> **Question:** What is the main topic discussed on the first few pages?
>
> **Answer:** The document introduces [topic], covering [key points] (Page 1, Page 2).

If the answer isn't in the uploaded PDF:

> **Answer:** I couldn't find this in the document, so here's a general answer: [general knowledge response]

---

## Design Notes

- **Why sentence-aware chunking instead of fixed character cuts?** Fixed-length chunking can slice a sentence in half, corrupting the meaning captured in its embedding. Overlap between chunks further ensures ideas spanning a chunk boundary aren't lost.
- **Why tag chunks with a `source` field instead of separate ChromaDB collections per PDF?** A single collection with metadata filtering keeps single-document and cross-document queries both possible without restructuring the database — you can ask about one PDF or compare across several using the same query path.
- **Why fall back to general knowledge?** A strictly document-only bot returns unhelpful "not found" answers whenever retrieval comes up empty. Falling back — while clearly labeling that the answer isn't from the document — keeps the tool useful without misleading the user about where the answer came from.

---

## Roadmap

This is Project 1 of a 5-project portfolio series:

1. **PDF Q&A Bot** *(this project)*
2. Structured Data Extractor (Pydantic-focused)
3. Multi-Tool Research Agent
4. MCP Server + Client
5. Capstone: Agentic RAG Assistant

---
