import os
from flask import Flask, request, jsonify, render_template

from extract import extract_pages
from chunk import chunk_all_pages
from embed_store import store_chunks, collection
from query import ask_question

app = Flask(__name__)

UPLOAD_DIR = "uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_stored_pdfs():
    """
    Looks at all metadata already in ChromaDB and returns the
    unique list of 'source' filenames stored so far.
    """
    all_data = collection.get()
    sources = set()
    for meta in all_data.get("metadatas", []):
        if meta and "source" in meta:
            sources.add(meta["source"])
    return sorted(sources)


@app.route("/")
def index():
    return render_template("index.html", pdfs=get_stored_pdfs())


@app.route("/upload", methods=["POST"])
def upload():
    if "pdf" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files["pdf"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    filename = file.filename
    save_path = os.path.join(UPLOAD_DIR, filename)
    file.save(save_path)

    # Run the pipeline: extract -> chunk -> embed & store
    pages = extract_pages(save_path)
    chunks = chunk_all_pages(pages)
    store_chunks(chunks, source_filename=filename)

    return jsonify({
        "message": f"'{filename}' processed successfully.",
        "pdfs": get_stored_pdfs(),
    })


@app.route("/delete", methods=["POST"])
def delete():
    data = request.get_json()
    filename = data.get("filename", "").strip()

    if not filename:
        return jsonify({"error": "No filename provided."}), 400

    # Remove all chunks in ChromaDB tagged with this source filename
    collection.delete(where={"source": filename})

    # Remove the uploaded file from disk, if it's still there
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    return jsonify({
        "message": f"'{filename}' removed.",
        "pdfs": get_stored_pdfs(),
    })


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "").strip()
    selected_pdf = data.get("selected_pdf")  # "" or None means "all"

    if not question:
        return jsonify({"error": "Question cannot be empty."}), 400

    source_filename = selected_pdf if selected_pdf else None
    answer = ask_question(question, source_filename=source_filename)

    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
