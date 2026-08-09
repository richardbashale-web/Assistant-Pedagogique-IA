from typing import Any, Dict, List

from chatbot.ml_model import _gemini_generate_text


def build_prompt(question: str, chunks: List[Dict[str, Any]]) -> str:
    """Construit un prompt strict pour la génération guidée par le contexte."""
    if chunks:
        context_blocks = []
        for index, chunk in enumerate(chunks, start=1):
            metadata = chunk.get("metadata", {}) or {}
            source_name = metadata.get("document_title") or metadata.get("source") or "document"
            context_blocks.append(
                f"[Contexte {index}] {chunk.get('text', '')}\nSource : {source_name}"
            )
        context_text = "\n\n".join(context_blocks)
    else:
        context_text = "Aucun contexte pertinent n'a été trouvé dans les supports de cours."

    return (
        "Tu es un assistant pédagogique universitaire. Réponds uniquement à partir du contexte fourni ci-dessous. "
        "Si l'information n'est pas présente dans ce contexte, dis-le explicitement et ne fais pas d'hypothèse. "
        "Ne prétends pas avoir lu un support si aucun contexte n'a été trouvé.\n\n"
        f"Question de l'étudiant : {question}\n\n"
        f"Contexte fourni :\n{context_text}\n\nRéponse :"
    )


def generate_answer(question: str, top_k: int = 4, threshold: float = 0.35, course_id: int | None = None) -> Dict[str, Any]:
    """Orchestre la recherche sémantique et la génération de réponse.

    Le seuil 0.35 est volontairement conservateur pour ne pas rater des chunks pertinents.
    Si les réponses sont trop hors-sujet, augmenter progressivement jusqu'à 0.55 max.
    Logger les scores réels ci-dessous pour calibrer.
    """
    from .retrieval import retrieve_relevant_chunks

    print(f"[RAG] generate_answer appelé pour : {question[:120]} | threshold={threshold}")
    relevant_chunks = retrieve_relevant_chunks(question, top_k=top_k, threshold=threshold, course_id=course_id)

    if relevant_chunks:
        best_score = relevant_chunks[0].get("similarity", 0)
        print(f"[RAG] Meilleur score de similarité : {best_score:.3f} | {len(relevant_chunks)} chunk(s) retenus")
        prompt = build_prompt(question, relevant_chunks)
        llm_text = _gemini_generate_text([{"text": prompt}]) or "Je n'ai pas pu générer une réponse à partir du contexte fourni."
        sources = []
        for chunk in relevant_chunks:
            metadata = chunk.get("metadata", {}) or {}
            label = metadata.get("document_title") or metadata.get("source") or "support de cours"
            sources.append(label)
        unique_sources = list(dict.fromkeys(sources))
        answer = llm_text.strip()
        if unique_sources:
            answer = f"{answer}\n\nSource : {', '.join(unique_sources)}"
        return {"answer": answer, "sources": unique_sources, "used_rag": True}

    prompt = (
        "Tu es un assistant pédagogique universitaire. Réponds à la question ci-dessous avec tes connaissances générales. "
        "Précise clairement que la réponse ne provient pas d'un support de cours et que tu réponds de façon générale.\n\n"
        f"Question : {question}\n\nRéponse :"
    )
    llm_text = _gemini_generate_text([{"text": prompt}]) or "Je n'ai pas pu générer une réponse pour le moment."
    return {"answer": llm_text.strip(), "sources": [], "used_rag": False}
