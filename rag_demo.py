import math
import re
from collections import Counter
from pathlib import Path


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "before",
    "for",
    "from",
    "happen",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "that",
    "the",
    "to",
    "what",
    "when",
    "who",
}


def load_documents(path="knowledge.txt"):
    """Load the knowledge file and split it into paragraph chunks."""
    knowledge_path = Path(path)
    if not knowledge_path.is_absolute():
        knowledge_path = Path(__file__).resolve().parent / knowledge_path

    with open(knowledge_path, "r", encoding="utf-8") as file:
        return [chunk.strip() for chunk in file.read().split("\n\n") if chunk.strip()]


def tokenize(text):
    """Convert text into lowercase word tokens."""
    raw_tokens = re.findall(r"[a-z0-9']+", text.lower())
    return [token for token in raw_tokens if token not in STOPWORDS]


def build_index(documents):
    """Build a tiny in-memory keyword index for fast local demos."""
    doc_tokens = [tokenize(document) for document in documents]
    document_frequencies = Counter()
    for tokens in doc_tokens:
        document_frequencies.update(set(tokens))

    return {
        "documents": documents,
        "doc_tokens": doc_tokens,
        "document_frequencies": document_frequencies,
        "document_count": len(documents),
    }


def score_document(query_tokens, document_tokens, document_frequencies, document_count):
    """Score a document using a simple TF-IDF-style overlap metric."""
    if not query_tokens or not document_tokens:
        return 0.0

    term_counts = Counter(document_tokens)
    score = 0.0
    unique_query_tokens = set(query_tokens)

    for token in unique_query_tokens:
        if token not in term_counts:
            continue
        document_frequency = document_frequencies.get(token, 0)
        inverse_document_frequency = math.log((document_count + 1) / (document_frequency + 1)) + 1.0
        score += term_counts[token] * inverse_document_frequency

    return score


def search(question, index, k=2):
    """Search for the most relevant document chunks for a question."""
    query_tokens = tokenize(question)
    scored_documents = []

    for document, document_tokens in zip(index["documents"], index["doc_tokens"]):
        score = score_document(
            query_tokens,
            document_tokens,
            index["document_frequencies"],
            index["document_count"],
        )
        if score > 0:
            scored_documents.append((score, document))

    scored_documents.sort(key=lambda item: item[0], reverse=True)
    return scored_documents[:k]


def format_confidence(top_score):
    """Convert a raw retrieval score into a simple demo-friendly confidence label."""
    if top_score >= 5:
        return "High"
    if top_score >= 2:
        return "Medium"
    return "Low"


def generate_answer(question, search_results):
    """Create a short final answer using the top retrieved chunk."""
    if not search_results:
        return {
            "final_answer": "I could not find a grounded answer in the knowledge base.",
            "confidence": "Low",
            "sources": [],
        }

    top_score, top_document = search_results[0]
    answer = top_document
    if not answer.endswith("."):
        answer = f"{answer}."

    return {
        "final_answer": answer,
        "confidence": format_confidence(top_score),
        "sources": [document for _, document in search_results],
    }


def main():
    documents = load_documents()
    index = build_index(documents)

    print("Knowledge base loaded.")
    print("Ask a question or type exit to stop.")

    while True:
        question = input("\nAsk a question: ").strip()
        if question.lower() == "exit":
            break

        results = search(question, index)
        response = generate_answer(question, results)

        print("\nFinal answer:")
        print(response["final_answer"])
        print(f"Confidence: {response['confidence']}")

        print("\nSupporting evidence:")
        if not response["sources"]:
            print("- No matching source found.")
        else:
            for source in response["sources"]:
                print(f"- {source}")


if __name__ == "__main__":
    main()