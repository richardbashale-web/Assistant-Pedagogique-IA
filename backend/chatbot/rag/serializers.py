from rest_framework import serializers

from .models import CourseDocument


class CourseDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseDocument
        fields = ["id", "file", "course", "professor", "title", "description", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at"]
