from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-small-en-v1.5")


def embed_texts(texts):
    return model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True
    ).tolist()


def embed_query(query):
    return model.encode(
        [f"query: {query}"],
        normalize_embeddings=True
    )[0].tolist()