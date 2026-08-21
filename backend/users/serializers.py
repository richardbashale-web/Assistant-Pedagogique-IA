from rest_framework import serializers
from .models import Student, Professor


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'
        # matricule est obligatoire (non auto-génér\u00e9), mais on tolère qu'il
        # soit absent lors d'une mise à jour partielle (PATCH).
        extra_kwargs = {
            'matricule': {'required': True},
        }

    def validate_matricule(self, value):
        """Vérifie que le matricule n'est pas déjà utilisé par un autre étudiant."""
        qs = Student.objects.filter(matricule=value)
        # En mode update, exclure l'instance courante
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ce matricule est déjà attribué à un autre étudiant.")
        return value


class ProfessorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professor
        fields = '__all__'