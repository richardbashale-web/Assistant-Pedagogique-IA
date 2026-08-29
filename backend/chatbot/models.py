from django.db import models
from django.contrib.auth.models import User

# Import des modèles RAG pour que Django les reconnaisse dans l'app.
from .rag.models import CourseDocument, DocumentChunk  # noqa: F401


class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=100, default='Nouvelle conversation')
    summary = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class ChatMessage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    text = models.TextField(blank=True)
    file = models.FileField(upload_to='chat_uploads/', null=True, blank=True)
    sender = models.CharField(max_length=10, choices=[('user', 'User'), ('bot', 'Bot')])
    sources = models.JSONField(default=list, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender}: {self.text[:20]}..."

class Intent(models.Model):
    tag = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.tag

class Pattern(models.Model):
    intent = models.ForeignKey(Intent, on_delete=models.CASCADE, related_name='patterns')
    text = models.CharField(max_length=500)

    def __str__(self):
        return self.text

class Response(models.Model):
    intent = models.ForeignKey(Intent, on_delete=models.CASCADE, related_name='responses')
    text = models.TextField()

    def __str__(self):
        return self.text[:50]