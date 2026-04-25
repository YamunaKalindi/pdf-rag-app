from src.vector_store import collection
from src.embedder import embed_query


# 🔥 Query-aware reranking (definition boost)
def boost_definition_chunks(results, query):
    query_lower = query.lower()

    keywords = ["what is", "define", "meaning", "explain"]

    if any(k in query_lower for k in keywords):

        # extract entity (very simple)
        entity = query_lower.replace("what is", "").strip()

        results = sorted(
            results,
            key=lambda x: (
                entity in x["text"].lower(),        # 🔥 exact match boost
                " is " in x["text"].lower(),        # definition pattern
                " refers to " in x["text"].lower()
            ),
            reverse=True
        )

    return results


def retrieve(query, top_k=12):
    query_embedding = embed_query(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    structured_results = []

    for doc, meta, dist in zip(docs, metas, distances):
        structured_results.append({
            "text": doc,
            "page": meta.get("page", "N/A"),
            "source": meta.get("source", "unknown"),
            "score": dist
        })

    # 🔥 Step 1: Sort
    structured_results = sorted(structured_results, key=lambda x: x["score"])

    # 🔥 Step 2: Boost
    structured_results = boost_definition_chunks(structured_results, query)

    # 🔥 NEW: Step 3 → REMOVE DUPLICATES (CRITICAL)
    seen = set()
    unique_results = []

    for r in structured_results:
        key = (r["text"], r["page"])
        if key not in seen:
            seen.add(key)
            unique_results.append(r)

    # 🔥 Step 4: Filter weak matches
    filtered = [r for r in unique_results if r["score"] < 0.8]

    # 🔥 Fallback
    if len(filtered) < 2:
        filtered = unique_results[:5]

    # 🔥 NEW: Step 5 → FINAL LIMIT
    return filtered[:5]