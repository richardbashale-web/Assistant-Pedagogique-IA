from typing import Any, Dict, List
import re

from chatbot.ml_model import _gemini_generate_text

# Balise que le LLM doit ajouter UNIQUEMENT s'il juge le contexte hors-sujet
# et qu'il a répondu avec ses connaissances générales à la place.
OUT_OF_CONTEXT_MARKER = "[HORS_CONTEXTE]"


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
        "1. Réponds en te basant PRIORITAIREMENT sur le contexte fourni ci-dessus, tant qu'il est pertinent pour la question.\n"
        f"2. Si, et seulement si, le contexte fourni n'a AUCUN rapport avec la question, ignore-le, réponds avec tes "
        f"connaissances générales, et ajoute OBLIGATOIREMENT le texte exact '{OUT_OF_CONTEXT_MARKER}' à la toute fin "
        "de ta réponse (rien après ce texte).\n"
        "3. Si tu utilises le contexte fourni (cas normal), NE METS AUCUNE balise spéciale à la fin de ta réponse.\n\n"
        f"Question de l'étudiant : {question}\n\nRéponse :"
    )


def generate_answer(question: str, top_k: int = 4, threshold: float = 0.35, course_id: int | None = None) -> Dict[str, Any]:
    """Orchestre la recherche sémantique et la génération de réponse.

    Le seuil 0.35 est volontairement conservateur pour ne pas rater des chunks pertinents.
    Si les réponses sont trop hors-sujet, augmenter progressivement jusqu'à 0.55 max.
    Logger les scores réels ci-dessous pour calibrer.

    NB : l'attribution des sources se base sur les chunks RÉELLEMENT récupérés au-dessus
    du seuil de similarité (et non plus sur une balise que le LLM devait recopier mot pour
    mot) : cette dernière approche s'est révélée trop fragile (timeout, troncature de la
    réponse, oubli du LLM) et faisait disparaître les sources même quand le contexte avait
    bien été utilisé. On ne retire les sources que si le LLM signale explicitement, via
    OUT_OF_CONTEXT_MARKER, qu'il a ignoré le contexte fourni.
    """
    from .retrieval import retrieve_relevant_chunks

    print(f"[RAG] generate_answer appelé pour : {question[:120]} | threshold={threshold}")
    relevant_chunks = retrieve_relevant_chunks(question, top_k=top_k, threshold=threshold, course_id=course_id)

    if relevant_chunks:
        best_score = relevant_chunks[0].get("similarity", 0)
        print(f"[RAG] Meilleur score de similarité : {best_score:.3f} | {len(relevant_chunks)} chunk(s) retenus")
        prompt = build_prompt(question, relevant_chunks)
        llm_text = _gemini_generate_text([{"text": prompt}])

        if not llm_text:
            # Échec réel de génération (timeout, quota, erreur réseau...) : pas de réponse
            # fiable produite à partir du contexte, donc pas de source à afficher.
            print("[RAG] Échec de génération LLM malgré des chunks pertinents trouvés.")
            return {
                "answer": "Je n'ai pas pu générer une réponse à partir du contexte fourni. Réessaie dans un instant.",
                "sources": [],
                "used_rag": False,
            }

        # Construction de la liste des sources à partir des chunks réellement récupérés
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

        if OUT_OF_CONTEXT_MARKER.lower() in answer.lower():
            # Le LLM signale explicitement qu'il a ignoré le contexte fourni
            answer = re.sub(re.escape(OUT_OF_CONTEXT_MARKER), "", answer, flags=re.IGNORECASE).strip()
            print("[RAG] Le LLM indique avoir ignoré le contexte fourni (hors-sujet) — aucune source affichée.")
            return {"answer": answer, "sources": [], "used_rag": False}

        # Cas normal : des chunks pertinents ont été trouvés et le LLM n'a pas signalé
        # les avoir ignorés -> on attribue la réponse aux notes de cours retrouvées.
        print(f"[RAG] Sources attribuées à la réponse : {primary_source}")
        return {"answer": answer, "sources": primary_source, "used_rag": True}

    prompt = (
        "Tu es un assistant pédagogique universitaire. Réponds à la question ci-dessous de manière claire avec tes connaissances générales.\n\n"
        f"Question : {question}\n\nRéponse :"
    )
    llm_text = _gemini_generate_text([{"text": prompt}]) or "Je n'ai pas pu générer une réponse pour le moment."
    return {"answer": llm_text.strip(), "sources": [], "used_rag": False}