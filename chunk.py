import re

def split_into_sentences(text):
    """
    Simple sentence splitter using punctuation as boundaries.
    Not perfect (e.g., struggles with abbreviations like 'Dr.'), but
    good enough for chunking purposes.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_text(page_num, text, target_size=400, overlap_sentences=2):
    """
    Splits one page's text into overlapping, sentence-aware chunks.
    Returns a list of dicts: {"page": page_num, "text": chunk_text}
    """
    sentences = split_into_sentences(text)
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        current_chunk.append(sentence)
        current_length += len(sentence)

        if current_length >= target_size:
            chunk_str = " ".join(current_chunk)
            chunks.append({"page": page_num, "text": chunk_str})

            # start next chunk with the last N sentences as overlap
            current_chunk = current_chunk[-overlap_sentences:]
            current_length = sum(len(s) for s in current_chunk)

    # add whatever's left as the final chunk
    if current_chunk:
        chunk_str = " ".join(current_chunk)
        chunks.append({"page": page_num, "text": chunk_str})

    return chunks


def chunk_all_pages(pages, target_size=400, overlap_sentences=2):
    """
    pages: list of (page_num, text) from extract_pages()
    Returns a flat list of chunk dicts across all pages.
    """
    all_chunks = []
    for page_num, text in pages:
        page_chunks = chunk_text(page_num, text, target_size, overlap_sentences)
        all_chunks.extend(page_chunks)
    return all_chunks


if __name__ == "__main__":
    from extract import extract_pages

    pages = extract_pages("sample.pdf")
    chunks = chunk_all_pages(pages)
    print(f"Created {len(chunks)} chunks from {len(pages)} pages.")
    print(chunks[0])