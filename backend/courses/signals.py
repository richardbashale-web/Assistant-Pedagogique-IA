from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import CourseNote


@receiver(post_save, sender=CourseNote)
def feed_knowledge_base(sender, instance, created, **kwargs):
    """
    Chaque fois qu'un professeur crée ou modifie une note de cours,
    on injecte automatiquement son contenu dans la base de connaissances ML
    et dans ChromaDB pour la recherche sémantique RAG.
    """
    # --- Ingestion RAG (ChromaDB) ---
    try:
        from chatbot.ml_model import add_new_intent
        from chatbot.rag.ingestion import chunk_text, embed_and_store, extract_text
        from chatbot.rag.models import CourseDocument, DocumentChunk

        attachment = getattr(instance, "attachment", None)
        if attachment:
            print(f"[Signal RAG] Début ingestion pour la note id={instance.id} | fichier={attachment.name}")

            # Étape 1 : extraction du texte
            try:
                extracted_text = extract_text(attachment)
            except Exception as exc:
                print(f"[Signal RAG] ERREUR extraction texte : {exc}")
                extracted_text = ""

            if not extracted_text.strip():
                print(f"[Signal RAG] Aucun texte extrait du fichier {attachment.name} — ingestion annulée.")
            else:
                print(f"[Signal RAG] Texte extrait : {len(extracted_text)} caractères")

                # Étape 2 : découpage en chunks
                chunks = chunk_text(extracted_text, chunk_size=700, overlap=100)
                print(f"[Signal RAG] {len(chunks)} chunk(s) créés")

                if chunks:
                    # Étape 3 : création/récupération du document en base
                    document = None
                    if instance.id:
                        try:
                            # Utiliser filter().first() au lieu de get_or_create
                            # pour eviter l'erreur si plusieurs documents existent
                            document = CourseDocument.objects.filter(
                                course=instance.course,
                                professor=instance.professor,
                            ).order_by("-uploaded_at").first()
                            if not document:
                                document = CourseDocument.objects.create(
                                    course=instance.course,
                                    professor=instance.professor,
                                    file=attachment,
                                    title=instance.title or attachment.name,
                                    description=instance.content or "",
                                )
                                print(f"[Signal RAG] CourseDocument id={document.id} (cree)")
                            else:
                                print(f"[Signal RAG] CourseDocument id={document.id} (existant)")
                        except Exception as exc:
                            print(f"[Signal RAG] ERREUR CourseDocument : {exc}")

                    if document:
                        # Étape 4 : préparation des métadonnées
                        metadata_list = [
                            {
                                "document_id": str(document.id),
                                "document_title": document.title or document.file.name,
                                "course_id": str(instance.course.id) if instance.course else "",
                                "course_title": instance.course.titre if instance.course else "",
                                "professor_name": instance.professor.nom if instance.professor else "",
                                "source": attachment.name,
                                "chunk_index": idx,
                            }
                            for idx, _ in enumerate(chunks)
                        ]

                        # Étape 5 : envoi à ChromaDB
                        try:
                            embed_and_store(chunks, metadata_list)
                            print(f"[Signal RAG] Ingestion ChromaDB réussie : {len(chunks)} chunk(s) stockés")
                        except Exception as exc:
                            print(f"[Signal RAG] ERREUR embed_and_store : {exc}")
                            raise  # Re-lever pour voir l'erreur dans la console Django

                        # Étape 6 : sauvegarde en base Django (DocumentChunk)
                        DocumentChunk.objects.filter(document=document).delete()
                        for idx, chunk in enumerate(chunks):
                            DocumentChunk.objects.create(
                                document=document,
                                text=chunk,
                                chunk_index=idx,
                                metadata=metadata_list[idx],
                            )
        else:
            print(f"[Signal RAG] Note id={instance.id} sans pièce jointe — pas d'ingestion RAG.")

    except Exception as exc:
        # L'erreur est affichée mais n'interrompt pas la sauvegarde de la note
        print(f"[Signal RAG] ERREUR ingestion (non bloquante) : {exc}")

    # --- Mise à jour de la base ML (intentions) ---
    try:
        from chatbot.ml_model import add_new_intent

        tag = f"coursenote_{instance.id}"

        # Patterns : titre de la note + combinaisons avec le titre du cours
        course_title = instance.course.titre if instance.course else ""
        note_title = instance.title or ""
        patterns = []
        if note_title:
            patterns.append(note_title.lower())
        if course_title:
            patterns.append(course_title.lower())
            if note_title:
                patterns.append(f"{course_title.lower()} {note_title.lower()}")
                patterns.append(f"cours {course_title.lower()}")
                patterns.append(f"note de {course_title.lower()}")

        # Réponse : contenu de la note
        content = (instance.content or "").strip()
        if len(content) > 500:
            content = content[:500].rsplit(' ', 1)[0] + '...'

        professor_name = instance.professor.nom if instance.professor else "le professeur"
        response_text = (
            f"📘 Note de {professor_name} — {course_title} : {note_title}\n\n{content}"
            if content
            else f"📘 Note de {professor_name} — {course_title} : {note_title}\n(Pas de contenu textuel)"
        )

        if patterns:
            add_new_intent(tag, patterns, [response_text])
            print(f"[Signal ML] Base ML mise à jour avec la note : {tag}")
    except Exception as exc:
        print(f"[Signal ML] Erreur lors de la mise à jour ML: {exc}")


@receiver(post_delete, sender=CourseNote)
def delete_course_note_attachment(sender, instance, **kwargs):
    if instance.attachment:
        try:
            instance.attachment.delete(save=False)
        except Exception:
            pass


@receiver(pre_save, sender=CourseNote)
def delete_old_course_note_attachment(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old_instance = CourseNote.objects.get(pk=instance.pk)
    except CourseNote.DoesNotExist:
        return

    if old_instance.attachment and old_instance.attachment != instance.attachment:
        try:
            old_instance.attachment.delete(save=False)
        except Exception:
            pass
