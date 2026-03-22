"""
retriever.py - Vector store retrieval logic for the Hack Canada RAG system.
"""
import requests
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL, VOYAGE_API_KEY


class DirectVoyageEmbeddings(Embeddings):
    """Call Voyage AI API directly via HTTP — no HuggingFace tokenizer needed."""

    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key

    def _call_api(self, texts: list[str], input_type: str = "document") -> list[list[float]]:
        resp = requests.post(
            "https://api.voyageai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"input": texts, "model": self.model, "input_type": input_type},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return [item["embedding"] for item in data["data"]]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._call_api(texts, input_type="document")

    def embed_query(self, text: str) -> list[float]:
        return self._call_api([text], input_type="query")[0]


def get_vectorstore() -> Chroma:
    """Load the persisted ChromaDB vectorstore."""
    embeddings = DirectVoyageEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=VOYAGE_API_KEY,
    )
    return Chroma(
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings
    )


def search(query: str, k: int = 5, use_mmr: bool = False) -> list[dict]:
    """
    Search the vector store for relevant chunks.

    Args:
        query: The search query
        k: Number of results to return
        use_mmr: If True, use Maximal Marginal Relevance for diversity

    Returns:
        List of dicts with 'content', 'metadata', and 'score'
    """
    vs = get_vectorstore()

    if use_mmr:
        docs = vs.max_marginal_relevance_search(query, k=k, fetch_k=k * 3)
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": None
            }
            for doc in docs
        ]
    else:
        results = vs.similarity_search_with_relevance_scores(query, k=k)
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": round(score, 4)
            }
            for doc, score in results
        ]


def get_retriever(k: int = 5):
    """Get a LangChain retriever object for use in chains."""
    vs = get_vectorstore()
    return vs.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )


def get_collection_stats() -> dict:
    """Get stats about the ChromaDB collection."""
    vs = get_vectorstore()
    collection = vs._collection
    count = collection.count()

    sample = collection.peek(min(count, 50))
    source_types = {}
    filenames = set()
    if sample and "metadatas" in sample:
        for meta in sample["metadatas"]:
            st = meta.get("source_type", "unknown")
            source_types[st] = source_types.get(st, 0) + 1
            filenames.add(meta.get("filename", "unknown"))

    return {
        "total_chunks": count,
        "sample_source_types": source_types,
        "sample_unique_files": len(filenames)
    }
