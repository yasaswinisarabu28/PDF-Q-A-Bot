import os
import tkinter as tk
from tkinter import filedialog

from extract import extract_pages
from chunk import chunk_all_pages
from embed_store import store_chunks, collection
from query import ask_question


def get_stored_pdfs():
    """
    Looks at all metadata already in ChromaDB and returns the
    unique list of 'source' filenames stored so far.
    """
    all_data = collection.get()  # fetches everything (no query, just a dump)
    sources = set()
    for meta in all_data.get("metadatas", []):
        if meta and "source" in meta:
            sources.add(meta["source"])
    return sorted(sources)


def pick_pdf_from_dialog():
    """
    Opens a native file-picker dialog restricted to PDF files.
    Returns the full path selected, or None if the user cancels.
    """
    root = tk.Tk()
    root.withdraw()  # hide the empty tkinter root window, we only want the dialog
    file_path = filedialog.askopenfilename(
        title="Select a PDF to add",
        filetypes=[("PDF files", "*.pdf")]
    )
    root.destroy()
    return file_path if file_path else None


def add_new_pdf():
    """
    Runs the full pipeline (extract -> chunk -> embed & store)
    on a newly picked PDF.
    """
    file_path = pick_pdf_from_dialog()
    if not file_path:
        print("No file selected.")
        return

    filename = os.path.basename(file_path)  # e.g. "z.pdf" from the full path
    print(f"Processing '{filename}'...")

    pages = extract_pages(file_path)          # from extract.py
    chunks = chunk_all_pages(pages)                # from chunk.py
    store_chunks(chunks, source_filename=filename)  # from embed_store.py

    print(f"'{filename}' added and ready to query.")


def show_menu():
    pdfs = get_stored_pdfs()
    print("\n--- PDF Q&A Bot ---")
    for i, pdf in enumerate(pdfs, start=1):
        print(f"{i}. Ask about {pdf}")
    print("0. Ask across ALL stored PDFs")
    print("A. Add a new PDF")
    print("Q. Quit")
    return pdfs


def main():
    while True:
        pdfs = show_menu()
        choice = input("\nChoose an option: ").strip().lower()

        if choice == "q":
            break
        elif choice == "a":
            add_new_pdf()
            continue
        elif choice == "0":
            selected_source = None  # None -> search across all PDFs
        elif choice.isdigit() and 1 <= int(choice) <= len(pdfs):
            selected_source = pdfs[int(choice) - 1]
        else:
            print("Invalid choice, try again.")
            continue

        # Question loop for the chosen scope (one PDF or all)
        print(f"\nAsking about: {selected_source or 'ALL PDFs'}. Type 'back' to return to menu.")
        while True:
            q = input("Question: ")
            if q.lower() == "back":
                break
            answer = ask_question(q, source_filename=selected_source)
            print("\nAnswer:\n", answer)


if __name__ == "__main__":
    main()