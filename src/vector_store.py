import chromadb

client = chromadb.Client(
    chromadb.config.Settings(
        persist_directory="db",
        is_persistent=True
    )
)

collection = client.get_or_create_collection(
    name="rag_collection",
    metadata={"hnsw:space": "cosine"}  # 🔥 explicit similarity
)


def add_chunks(chunks, embeddings, source_name):
    documents = [c["text"] for c in chunks]

    metadatas = [
        {
            "page": c["page"],
            "source": source_name,
            "text": c["text"][:200]  # 🔥 small preview (useful for debugging)
        }
        for c in chunks
    ]

    # 🔥 Unique IDs (avoid collision)
    ids = [f"{source_name}_{i}_{hash(c['text'])}" for i, c in enumerate(chunks)]

    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

    # 🔥 Persist to disk
    #client.persist()