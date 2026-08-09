from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import Student, Professor, SecretaireFacultaire
from courses.models import Course, CourseNote
from chatbot.models import Conversation


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    user = request.user
    profile = getattr(user, 'profile', None)
    role_name = profile.role.nom if profile and profile.role else None

    # Par défaut (pour les admins/gestionnaires)
    stats = {
        'total_students': Student.objects.count(),
        'total_professors': Professor.objects.count(),
        'total_courses': Course.objects.count(),
        'total_conversations': Conversation.objects.count(),
        'total_notes': CourseNote.objects.count()
    }

    if role_name == 'secretaire_facultaire':
        secretaire = SecretaireFacultaire.objects.filter(user=user).first()
        if secretaire and secretaire.faculte:
            stats = {
                'total_students': Student.objects.filter(faculte=secretaire.faculte).count(),
                'total_professors': Professor.objects.filter(faculte=secretaire.faculte).count(),
                'total_courses': Course.objects.filter(faculte=secretaire.faculte).count(),
                'faculty_name': secretaire.faculte.nom
            }

    elif role_name == 'professeur':
        professor = Professor.objects.filter(user=user).first()
        if professor:
            faculte = professor.faculte
            stats = {
                'my_courses': Course.objects.filter(professeur=professor).count(),
                'my_notes': CourseNote.objects.filter(professor=professor).count(),
                'students_in_faculty': Student.objects.filter(faculte=faculte).count() if faculte else 0,
                'faculty_name': faculte.nom if faculte else "Aucune"
            }

    elif role_name == 'etudiant':
        student = Student.objects.filter(user=user).first()
        if student:
            faculte = student.faculte
            stats = {
                'my_conversations': Conversation.objects.filter(user=user).count(),
                'available_courses': Course.objects.filter(faculte=faculte).count() if faculte else 0,
                'available_notes': CourseNote.objects.filter(course__faculte=faculte).count() if faculte else 0,
                'faculty_name': faculte.nom if faculte else "Aucune"
            }

    return Response(stats)
