import os
import gradio as gr

from extract import extract_text
from chunk import chunk_text
from embed_store import store_chunks, collection
from query import ask_question


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


def get_dropdown_choices():
    """
    Builds the dropdown options: 'All PDFs' plus every stored filename.
    """
    pdfs = get_stored_pdfs()
    return ["All PDFs"] + pdfs


def process_pdf(file_path):
    """
    Runs the full pipeline on an uploaded PDF, then returns an updated
    dropdown (so the new PDF shows up immediately) plus a status message.
    """
    if file_path is None:
        return gr.update(), "No file uploaded."

    filename = os.path.basename(file_path)

    pages = extract_text(file_path)
    chunks = chunk_text(pages)
    store_chunks(chunks, source_filename=filename)

    new_choices = get_dropdown_choices()
    return gr.update(choices=new_choices, value=filename), f"'{filename}' processed and ready to query."


def answer_question(question, selected_pdf):
    """
    Calls the existing ask_question() pipeline, scoped to the selected
    PDF, or across all PDFs if 'All PDFs' is chosen.
    """
    if not question.strip():
        return "Please enter a question."

    source_filename = None if selected_pdf == "All PDFs" else selected_pdf
    return ask_question(question, source_filename=source_filename)


with gr.Blocks(title="PDF Q&A Bot") as demo:
    gr.Markdown("# 📄 PDF Q&A Bot")
    gr.Markdown("Upload a PDF, then ask questions about it — grounded in the actual document content, with page citations.")

    with gr.Row():
        file_input = gr.File(label="Upload a PDF", file_types=[".pdf"], type="filepath")
        process_btn = gr.Button("Process PDF")

    status_box = gr.Textbox(label="Status", interactive=False)

    pdf_dropdown = gr.Dropdown(
        choices=get_dropdown_choices(),
        value="All PDFs",
        label="Ask about"
    )

    question_box = gr.Textbox(label="Your question", placeholder="e.g. What is this document about?")
    ask_btn = gr.Button("Ask")

    answer_box = gr.Textbox(label="Answer", interactive=False, lines=6)

    # Wiring: processing a PDF updates BOTH the dropdown and the status message
    process_btn.click(
        fn=process_pdf,
        inputs=file_input,
        outputs=[pdf_dropdown, status_box]
    )

    # Wiring: asking a question uses the current dropdown selection
    ask_btn.click(
        fn=answer_question,
        inputs=[question_box, pdf_dropdown],
        outputs=answer_box
    )

if __name__ == "__main__":
    demo.launch()