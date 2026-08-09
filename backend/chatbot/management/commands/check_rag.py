"""
Commande de diagnostic du système RAG.

Usage :
    python manage.py check_rag
    python manage.py check_rag --question "Qu'est-ce que la recursivite ?"
    python manage.py check_rag --reindex   # re-indexe toutes les notes existantes
    python manage.py check_rag --threshold 0.0  # affiche tous les resultats bruts
"""
import sys
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Diagnostique l'etat de la base ChromaDB et teste la recherche RAG."

    def add_arguments(self, parser):
        parser.add_argument(
            "--question",
            type=str,
            default="Qu'est-ce que la recursivite ?",
            help="Question de test pour la recherche semantique.",
        )
        parser.add_argument(
            "--reindex",
            action="store_true",
            help="Re-indexe toutes les notes existantes dans ChromaDB.",
        )
        parser.add_argument(
            "--threshold",
            type=float,
            default=0.0,
            help="Seuil de similarite pour le test (0.0 = tout afficher).",
        )

    def _out(self, msg):
        """Ecriture safe en ASCII pour eviter les erreurs d'encodage Windows."""
        try:
            self.stdout.write(msg)
        except UnicodeEncodeError:
            self.stdout.write(msg.encode("ascii", errors="replace").decode("ascii"))

    def handle(self, *args, **options):
        self._out("\n=== Diagnostic RAG ===\n")

        # --- 1. Verification de ChromaDB ---
        try:
            import chromadb
            from django.conf import settings
            from pathlib import Path

            chroma_path = str(Path(settings.BASE_DIR) / "chroma_db")
            client = chromadb.PersistentClient(path=chroma_path)
            self._out(f"[OK] ChromaDB accessible : {chroma_path}")
        except Exception as exc:
            self._out(f"[ERREUR] ChromaDB inaccessible : {exc}")
            return

        try:
            collection = client.get_or_create_collection(
                name="course_documents",
                metadata={"hnsw:space": "cosine"},
            )
            total = collection.count()
            self._out(f"[OK] Chunks stockes dans ChromaDB : {total}")
        except Exception as exc:
            self._out(f"[ERREUR] Impossible d'acceder a la collection : {exc}")
            return

        if total == 0:
            self._out(
                "\n[ATTENTION] La collection est VIDE.\n"
                "  -> Utilisez --reindex pour re-indexer les notes existantes,\n"
                "  -> ou uploadez une note via l'onglet 'Note' du compte professeur."
            )
        else:
            # Afficher 3 exemples de chunks
            self._out("\n--- Exemples de chunks stockes ---")
            try:
                sample = collection.get(limit=3, include=["documents", "metadatas"])
                for i, (doc, meta) in enumerate(zip(sample["documents"], sample["metadatas"]), 1):
                    source = (meta or {}).get("document_title", "N/A")
                    preview = (doc or "")[:120].replace("\n", " ")
                    self._out(f"  [{i}] Source: {source}")
                    self._out(f"       Extrait: {preview}...")
            except Exception as exc:
                self._out(f"[WARN] Impossible de lire des exemples : {exc}")

        # --- 2. Test de recherche semantique ---
        question = options["question"]
        threshold = options["threshold"]
        self._out(f"\n--- Test de recherche ---")
        self._out(f"    Question  : {question}")
        self._out(f"    Threshold : {threshold}")

        try:
            from chatbot.rag.retrieval import retrieve_relevant_chunks
            chunks = retrieve_relevant_chunks(question, top_k=5, threshold=threshold)
            if chunks:
                self._out(f"[OK] {len(chunks)} chunk(s) trouve(s) :")
                for i, chunk in enumerate(chunks, 1):
                    meta = chunk.get("metadata", {}) or {}
                    sim = chunk.get("similarity", 0)
                    source = meta.get("document_title", "N/A")
                    extrait = (chunk.get("text", "")[:80]).replace("\n", " ")
                    self._out(f"  [{i}] sim={sim:.3f} | source={source}")
                    self._out(f"       extrait: {extrait}...")
            else:
                self._out(
                    f"[ATTENTION] Aucun chunk trouve pour cette question (threshold={threshold}).\n"
                    "  -> Verifiez que des documents ont ete indexes (voir total ci-dessus).\n"
                    "  -> Si ChromaDB est vide, lancez : python manage.py check_rag --reindex"
                )
        except Exception as exc:
            self._out(f"[ERREUR] Lors de la recherche : {exc}")

        # --- 3. Re-indexation (optionnel) ---
        if options["reindex"]:
            self._out("\n--- Re-indexation de toutes les notes ---")
            try:
                from courses.models import CourseNote
                from chatbot.rag.ingestion import chunk_text, embed_and_store, extract_text
                from chatbot.rag.models import CourseDocument, DocumentChunk

                notes = CourseNote.objects.exclude(attachment="").exclude(attachment=None)
                self._out(f"Notes avec piece jointe trouvees : {notes.count()}")

                for note in notes:
                    try:
                        text = extract_text(note.attachment)
                        if not text.strip():
                            self._out(f"  [SKIP] Note id={note.id} : texte vide, ignoree.")
                            continue

                        chunks = chunk_text(text)
                        # Prendre le document existant le plus recent, ou en creer un
                        document = CourseDocument.objects.filter(
                            course=note.course,
                            professor=note.professor,
                        ).order_by("-uploaded_at").first()
                        if not document:
                            document = CourseDocument.objects.create(
                                course=note.course,
                                professor=note.professor,
                                file=note.attachment,
                                title=note.title or note.attachment.name,
                                description=note.content or "",
                            )
                        metadata_list = [
                            {
                                "document_id": str(document.id),
                                "document_title": document.title or document.file.name,
                                "course_id": str(note.course.id) if note.course else "",
                                "course_title": note.course.titre if note.course else "",
                                "professor_name": note.professor.nom if note.professor else "",
                                "source": note.attachment.name,
                                "chunk_index": idx,
                            }
                            for idx, _ in enumerate(chunks)
                        ]
                        embed_and_store(chunks, metadata_list)
                        DocumentChunk.objects.filter(document=document).delete()
                        for idx, chunk in enumerate(chunks):
                            DocumentChunk.objects.create(
                                document=document, text=chunk, chunk_index=idx, metadata=metadata_list[idx]
                            )
                        self._out(f"  [OK] Note id={note.id} ({note.title}) : {len(chunks)} chunk(s) indexes.")
                    except Exception as exc:
                        self._out(f"  [ERREUR] Note id={note.id} : {exc}")

                new_total = collection.count()
                self._out(f"\nRe-indexation terminee. Total chunks dans ChromaDB : {new_total}")
            except Exception as exc:
                self._out(f"[ERREUR] Re-indexation : {exc}")

        self._out("\n=== Fin du diagnostic ===\n")
