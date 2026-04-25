import streamlit as st
import os
import shutil

from src.ingestor import extract_text_blocks
from src.chunker import chunk_blocks
from src.embedder import embed_texts
from src.vector_store import add_chunks, collection
from src.retriever import retrieve
from src.generator import generate_answer


st.set_page_config(page_title="PDF RAG App", layout="wide")

st.title("📄 PDF RAG Application")
st.write("Upload research papers and ask questions with citations.")

# 🔹 Session state
if "processed" not in st.session_state:
    st.session_state.processed = False


# 🔹 File Upload
uploaded_files = st.file_uploader(
    "Upload PDF files",
    type=["pdf"],
    accept_multiple_files=True
)

# 🔥 AUTO PROCESS (no button)
if uploaded_files and not st.session_state.processed:
    with st.spinner("Processing PDFs..."):

        # 🔥 Reset old DB (important)
        # if os.path.exists("db"):
        #     shutil.rmtree("db")

        for file in uploaded_files:
            file_path = f"data/pdfs/{file.name}"

            # Save file
            with open(file_path, "wb") as f:
                f.write(file.read())

            # 🔹 Pipeline
            blocks = extract_text_blocks(file_path)
            chunks = chunk_blocks(blocks)
            texts = [c["text"] for c in chunks]

            embeddings = embed_texts(texts)

            add_chunks(chunks, embeddings, file.name.replace(".pdf", ""))

    st.session_state.processed = True
    st.success("PDFs processed successfully!")


# 🔹 Query Section
query = st.text_input("Ask a question:")


# 🔥 Ask button (better UX)
if st.button("Get Answer"):
    if not st.session_state.processed:
        st.warning("Please upload and process a PDF first.")
    elif not query:
        st.warning("Please enter a question.")
    else:
        with st.spinner("Generating answer..."):
            docs = retrieve(query)
            answer = generate_answer(query, docs)

            st.subheader("Answer")
            st.write(answer)

            # 🔥 Highlight function
            def highlight_text(text, query):
                words = query.lower().split()
                for word in words:
                    if len(word) > 3:
                        text = text.replace(word, f"**{word}**")
                        text = text.replace(word.capitalize(), f"**{word.capitalize()}**")
                return text

            # 🔥 Retrieved context
            st.subheader("Retrieved Context")

            for i, doc in enumerate(docs):
                highlighted = highlight_text(doc['text'], query)

                st.markdown(f"""
**Chunk {i+1}**
- Source: {doc['source']}.pdf  
- Page: {doc['page']}  
- Score: {doc['score']:.4f}

> {highlighted}
""")


# 🔥 Reset button
if st.button("Reset App"):
    st.session_state.processed = False
    st.rerun()