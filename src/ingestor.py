import fitz  # PyMuPDF


def clean_text(text):
    # Remove excessive whitespace
    text = " ".join(text.split())

    # Skip very short/noisy text
    if len(text) < 20:
        return None

    # Skip references section noise (basic filter)
    if text.lower().startswith(("references", "acknowledgements")):
        return None

    return text


def extract_text_blocks(pdf_path):
    doc = fitz.open(pdf_path)
    all_blocks = []

    for page_num, page in enumerate(doc):
        blocks = page.get_text("blocks")

        # 🔥 Sort blocks by vertical position (top → bottom)
        blocks = sorted(blocks, key=lambda b: b[1])

        for block in blocks:
            text = block[4].strip()

            text = clean_text(text)
            if not text:
                continue

            all_blocks.append({
                "text": text,
                "page": page_num + 1
            })

    return all_blocks