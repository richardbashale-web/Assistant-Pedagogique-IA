from django.db import models

from courses.models import Course
from users.models import Professor


class CourseDocument(models.Model):
    """Représente un document pédagogique uploadé par un enseignant."""
    file = models.FileField(upload_to="course_documents/")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="documents")
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, related_name="course_documents")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return self.title or self.file.name


class DocumentChunk(models.Model):
    """Stocke un chunk de texte extrait d'un document avec ses métadonnées."""
    document = models.ForeignKey(CourseDocument, on_delete=models.CASCADE, related_name="chunks")
    text = models.TextField()
    chunk_index = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["document", "chunk_index"]

    def __str__(self) -> str:
        return f"{self.document} - chunk {self.chunk_index}"
