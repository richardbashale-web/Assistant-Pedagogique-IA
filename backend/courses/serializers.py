from rest_framework import serializers
from .models import Course, CourseNote

class CourseSerializer(serializers.ModelSerializer):
    professeur_nom = serializers.CharField(source='professeur.nom', read_only=True, allow_null=True, default=None)
    faculte_nom = serializers.CharField(source='faculte.nom', read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'titre', 'description', 'professeur', 'professeur_nom', 'faculte', 'faculte_nom', 'promotions', 'date_creation']
        read_only_fields = ['professeur_nom', 'faculte_nom', 'date_creation']
        extra_kwargs = {
            'professeur': {'required': False, 'allow_null': True},
            'promotions': {'required': False},
        }

    def validate_promotions(self, value):
        if not value:
            raise serializers.ValidationError("Veuillez associer ce cours à au moins une promotion.")
        if not isinstance(value, list):
            raise serializers.ValidationError("Les promotions doivent être fournies sous forme de liste.")
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        if not cleaned:
            raise serializers.ValidationError("Veuillez associer ce cours à au moins une promotion.")
        return cleaned

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
