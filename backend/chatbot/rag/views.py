import os
from typing import Any, Dict

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from courses.models import Course
from users.models import Professor

from .ingestion import chunk_text, embed_and_store, extract_text
from .models import CourseDocument, DocumentChunk
from .generation import generate_answer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_document(request):
    """Upload d'un document pédagogique par un enseignant."""
    file = request.FILES.get("file")
    course_id = request.data.get("course")
    title = request.data.get("title", "")
    description = request.data.get("description", "")

    if not file:
        return Response({"error": "Aucun fichier fourni."}, status=status.HTTP_400_BAD_REQUEST)
    if not course_id:
        return Response({"error": "Le cours est obligatoire."}, status=status.HTTP_400_BAD_REQUEST)

    professor = getattr(request.user, "professor_profile", None)
    if not professor and not request.user.is_staff:
        return Response({"error": "Seul un professeur peut uploader un document."}, status=status.HTTP_403_FORBIDDEN)

    course = Course.objects.filter(id=course_id).first()
    if not course:
        return Response({"error": "Cours introuvable."}, status=status.HTTP_404_NOT_FOUND)

    if professor and not request.user.is_staff and course.professeur != professor:
        return Response({"error": "Vous ne pouvez uploader que pour vos propres cours."}, status=status.HTTP_403_FORBIDDEN)

    document = CourseDocument.objects.create(
        file=file,
        course=course,
        professor=professor or request.user.professor_profile,
        title=title or file.name,
        description=description,
    )

    try:
        extracted = extract_text(document.file)
    except Exception as exc:
        return Response({"error": f"Impossible d'extraire le texte : {exc}"}, status=status.HTTP_400_BAD_REQUEST)

    if not extracted.strip():
        return Response({"error": "Le fichier ne contient pas de texte lisible."}, status=status.HTTP_400_BAD_REQUEST)

    chunks = chunk_text(extracted)
    if not chunks:
        return Response({"error": "Le texte n'a pas pu être découpé en chunks."}, status=status.HTTP_400_BAD_REQUEST)

    metadata_list = []
    for index, chunk in enumerate(chunks):
        metadata_list.append({
            "document_id": str(document.id),
            "document_title": document.title or document.file.name,
            "course_id": str(course.id),
            "course_title": course.titre,
            "professor_name": professor.nom if professor else request.user.username,
            "source": document.file.name,
            "chunk_index": index,
        })

    try:
        embed_and_store(chunks, metadata_list)
    except Exception as exc:
        return Response({"error": f"Échec de l'indexation RAG : {exc}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    DocumentChunk.objects.filter(document=document).delete()
    for index, chunk in enumerate(chunks):
        DocumentChunk.objects.create(document=document, text=chunk, chunk_index=index, metadata=metadata_list[index])

    return Response({"success": True, "document_id": document.id, "chunks": len(chunks)})


@api_view(["POST"])
@permission_classes([AllowAny])
def ask_question(request):
    """Reçoit la question d'un utilisateur et retourne une réponse générée via RAG."""
    question = (request.data.get("message") or request.data.get("question") or "").strip()
    if not question:
        return Response({"error": "La question est vide."}, status=status.HTTP_400_BAD_REQUEST)

    course_id = request.data.get("course_id")
    try:
        course_id_int = int(course_id) if course_id not in [None, "", "undefined", "null"] else None
    except ValueError:
        course_id_int = None

    result = generate_answer(question, course_id=course_id_int)
    return Response({
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
        "used_rag": result.get("used_rag", False),
    })
