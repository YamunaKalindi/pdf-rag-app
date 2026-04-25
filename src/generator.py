import os
from huggingface_hub import InferenceClient

try:
    import ollama
except:
    ollama = None


IS_LOCAL = os.getenv("ENV", "DEV") == "DEV"
print("DEBUG MODE:", "LOCAL" if IS_LOCAL else "HF")


# 🔥 STRONGER PROMPT
def build_prompt(query, context):
    return f"""
You are a strict research assistant.

Follow these rules EXACTLY:

1. Answer ONLY using the provided context.
2. Do NOT use prior knowledge.
3. Do NOT infer or generalize.
4. If the answer is not explicitly stated in the context, return EXACTLY:
   Not found in document.

5. If answering:
   - Use only sentences from context
   - Provide complete information from context (do not omit key details)
   - Cite like: (Source: <document>.pdf, Page <number>)
   - Do NOT add extra explanation

Context:
{context}

Question:
{query}
"""


def build_context(retrieved_docs):
    context = ""

    for i, doc in enumerate(retrieved_docs):
        context += f"""
[Chunk {i+1}]
Document: {doc['source']}
Page: {doc['page']}
Text: {doc['text']}
"""

    return context


# 🔥 BETTER CONFIDENCE CHECK
def is_low_confidence(retrieved_docs):
    if not retrieved_docs:
        return True

    # if all scores are weak → reject
    avg_score = sum(d["score"] for d in retrieved_docs) / len(retrieved_docs)

    return avg_score > 0.75  # 🔥 tuned for your system


def generate_answer(query, retrieved_docs):
    print("DEBUG - entering generate_answer")
    print("DEBUG - retrieved_docs:", retrieved_docs)

    # 🔥 Step 1: confidence check
    if is_low_confidence(retrieved_docs):
        return "Not found in document."

    # 🔥 Step 2: structured context
    context = build_context(retrieved_docs)

    # 🔥 Step 3: prompt
    prompt = build_prompt(query, context)

    # 🔹 LOCAL MODE
    if IS_LOCAL:
        if ollama is None:
            raise RuntimeError("Ollama not running")

        response = ollama.chat(
            model="mistral",
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response['message']['content']

    # 🔹 HF MODE
    else:
        hf_token = os.getenv("HF_TOKEN")

        if hf_token is None:
            raise ValueError("HF_TOKEN not set")

        client = InferenceClient(
            model="mistralai/Mistral-7B-Instruct-v0.3",
            token=hf_token
        )

        response = client.text_generation(
            prompt,
            max_new_tokens=300,
            temperature=0.0,  # 🔥 IMPORTANT (no creativity)
        )

        answer = str(response)

    print("DEBUG - raw answer:", answer)

    # 🔥 HARD ENFORCEMENT
    if "not found" in answer.lower():
        return "Not found in document."

    # 🔥 GROUNDING CHECK (VERY IMPORTANT)
    # 🔥 RELAXED GROUNDING CHECK
    if len(answer.strip()) < 20:
        return "Not found in document."

    # 🔥 Sources
    sources_dict = {}

    for doc in retrieved_docs[:2]:
        key = (doc['source'], doc['page'])

        if key not in sources_dict:
            sources_dict[key] = 1
        else:
            sources_dict[key] += 1

    sources = "\n\nSources:\n"

    for (source, page), count in sources_dict.items():
        if count > 1:
            sources += f"- {source}.pdf (Page {page}, {count} chunks)\n"
        else:
            sources += f"- {source}.pdf (Page {page})\n"

    return answer.strip() + sources