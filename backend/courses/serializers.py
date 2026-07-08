from rest_framework import serializers
from .models import Course, CourseNote

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

class CourseNoteSerializer(serializers.ModelSerializer):
    professor_name = serializers.CharField(source='professor.nom', read_only=True)
    course_title = serializers.CharField(source='course.titre', read_only=True)
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = CourseNote
        fields = ['id', 'course', 'course_title', 'professor', 'professor_name', 'title', 'content', 'attachment', 'attachment_url', 'created_at', 'updated_at']
        read_only_fields = ['professor', 'professor_name', 'course_title', 'attachment_url', 'created_at', 'updated_at']

    def get_attachment_url(self, obj):
        request = self.context.get('request')
        if obj.attachment:
            try:
                url = obj.attachment.url
            except Exception:
                return None
            if request:
                return request.build_absolute_uri(url)
            return url
        return None