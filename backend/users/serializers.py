from rest_framework import serializers
from .models import Student, Professor
from django.utils import timezone
import random


def generate_matricule():
    """Génère un matricule unique au format ETU-YYYY-XXXX"""
    year = timezone.now().year
    while True:
        number = random.randint(1000, 9999)
        matricule = f"ETU-{year}-{number}"
        if not Student.objects.filter(matricule=matricule).exists():
            return matricule


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

    def create(self, validated_data):
        # Génération automatique du matricule si non fourni ou vide
        if not validated_data.get('matricule'):
            validated_data['matricule'] = generate_matricule()
        return super().create(validated_data)


class ProfessorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professor
        fields = '__all__'