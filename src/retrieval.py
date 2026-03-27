import chromadb
from sentence_transformers import SentenceTransformer

_model = None
_collection = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_collection(chroma_path: str = "data/chroma", collection_name: str = "cruxbot"):
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=chroma_path)
        _collection = client.get_collection(collection_name)
    return _collection


def retrieve(query: str, top_k: int = 5, chroma_path: str = "data/chroma") -> list[dict]:
    """
    Embed query and return top-k most relevant chunks.

    Each result dict contains:
        - text: str
        - source_url: str
        - score: float  (cosine distance, lower = more similar)
        - metadata: dict
    """
    model = _get_model()
    collection = _get_collection(chroma_path)

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": doc,
            "source_url": meta.get("source_url", ""),
            "score": dist,
            "metadata": meta,
        })

    return chunks
