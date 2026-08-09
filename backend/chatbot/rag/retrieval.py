import os
from typing import Any, Dict, List, Optional

import chromadb
from django.conf import settings

from .ingestion import get_embedding


def retrieve_relevant_chunks(
    question: str,
    top_k: int = 4,
    threshold: float = 0.2,
    course_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Interroge ChromaDB pour récupérer les chunks les plus pertinents."""
    if not question or not question.strip():
        return []

    print(f"[RAG] retrieval start question={question[:120]} threshold={threshold}")

    try:
        embedding = get_embedding(question)
    except Exception:
        return []

    if not embedding:
        return []

    try:
        client = chromadb.PersistentClient(path=str(settings.BASE_DIR / "chroma_db"))
        collection = client.get_or_create_collection(name="course_documents", metadata={"hnsw:space": "cosine"})
    except Exception:
        return []

    query_kwargs: Dict[str, Any] = {"query_embeddings": [embedding], "n_results": top_k, "include": ["documents", "metadatas", "distances"]}
    if course_id is not None:
        query_kwargs["where"] = {"course_id": str(course_id)}

    results = collection.query(**query_kwargs)
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    print(f"[RAG] retrieval raw_count={len(documents)}")
    relevant_chunks: List[Dict[str, Any]] = []
    for document, metadata, distance in zip(documents, metadatas, distances):
        try:
            similarity = max(0.0, 1.0 - float(distance))
        except Exception:
            similarity = 0.0
        print(f"[RAG] retrieval candidate similarity={similarity:.3f} source={metadata.get('document_title') if metadata else ''}")
        if similarity >= threshold:
            relevant_chunks.append({
                "text": document,
                "metadata": metadata or {},
                "similarity": similarity,
            })

    print(f"[RAG] retrieval returned={len(relevant_chunks)}")
    return relevant_chunks
