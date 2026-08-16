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
        "Tu es un assistant pédagogique universitaire. "
        "Voici un contexte extrait des notes de cours pour répondre à la question.\n\n"
        f"Contexte fourni :\n{context_text}\n\n"
        "Instructions :\n"
        "1. Si tu trouves la réponse dans le contexte fourni, réponds en utilisant CES informations, et ajoute OBLIGATOIREMENT le texte '[SOURCE_USED]' à la toute fin de ta réponse.\n"
        "2. Si l'information N'EST PAS dans le contexte, ignore le contexte et réponds de manière claire en utilisant tes connaissances générales. Dans ce cas, NE METS PAS '[SOURCE_USED]' à la fin.\n\n"
        f"Question de l'étudiant : {question}\n\nRéponse :"
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
            doc_title = metadata.get("document_title") or metadata.get("source") or "document"
            course_title = metadata.get("course_title")
            prof_name = metadata.get("professor_name")
            
            if course_title:
                label = f"{doc_title} (Cours : {course_title})"
            elif prof_name:
                label = f"{doc_title} (Prof : {prof_name})"
            else:
                label = doc_title
                
            sources.append(label)
            
        unique_sources = list(dict.fromkeys(sources))
        
        # Only return the top 1 source to avoid cluttering the UI
        primary_source = unique_sources[:1]
        
        answer = llm_text.strip()
        
        if "[SOURCE_USED]" in answer:
            answer = answer.replace("[SOURCE_USED]", "").strip()
            return {"answer": answer, "sources": primary_source, "used_rag": True}
        else:
            return {"answer": answer, "sources": [], "used_rag": False}

    prompt = (
        "Tu es un assistant pédagogique universitaire. Réponds à la question ci-dessous de manière claire avec tes connaissances générales.\n\n"
        f"Question : {question}\n\nRéponse :"
    )
    llm_text = _gemini_generate_text([{"text": prompt}]) or "Je n'ai pas pu générer une réponse pour le moment."
    return {"answer": llm_text.strip(), "sources": [], "used_rag": False}
