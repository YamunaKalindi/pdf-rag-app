def chunk_blocks(blocks, max_chars=800, overlap=100):
    chunks = []
    current_chunk = []
    current_length = 0

    for block in blocks:
        text = block["text"].strip()

        # Skip very small/noisy blocks
        if len(text) < 30:
            continue

        # If adding this block exceeds limit → finalize chunk
        if current_length + len(text) > max_chars:
            chunk_text = " ".join(current_chunk)

            chunks.append({
                "text": chunk_text,
                "page": block["page"]
            })

            # 🔁 Overlap handling (retain last part)
            if overlap > 0 and len(chunk_text) > overlap:
                overlap_text = chunk_text[-overlap:]
                current_chunk = [overlap_text]
                current_length = len(overlap_text)
            else:
                current_chunk = []
                current_length = 0

        # Add block
        current_chunk.append(text)
        current_length += len(text)

    # Final chunk
    if current_chunk:
        chunks.append({
            "text": " ".join(current_chunk),
            "page": blocks[-1]["page"]
        })

    return chunks