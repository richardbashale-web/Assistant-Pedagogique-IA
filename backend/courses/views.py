from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Course, CourseNote
from .serializers import CourseSerializer, CourseNoteSerializer
from users.models import Professor, Student
from chatbot.models import Conversation, ChatMessage
import re


class CourseListView(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class CourseNoteListCreateView(generics.ListCreateAPIView):
    queryset = CourseNote.objects.all()
    serializer_class = CourseNoteSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    ALLOWED_EXTENSIONS = ('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg')

    def get_queryset(self):
        queryset = super().get_queryset()
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset

    def perform_create(self, serializer):
        professor = getattr(self.request.user, 'professor_profile', None)
        if not professor and not self.request.user.is_staff:
            profile = getattr(self.request.user, 'profile', None)
            role_name = profile.role.nom if profile and profile.role else None
            if role_name == 'professeur':
                professor = Professor.objects.filter(user=self.request.user).first()
            if not professor and role_name != 'professeur':
                raise PermissionDenied("Seul un professeur ou un administrateur peut ajouter des notes.")

        attachment = self.request.FILES.get('attachment')
        if attachment:
            name = attachment.name.lower()
            if not any(name.endswith(ext) for ext in self.ALLOWED_EXTENSIONS):
                raise ValidationError({'attachment': 'Type de fichier non autorisé.'})

        serializer.save(professor=professor)


class ProfessorStudentProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        professor = getattr(request.user, 'professor_profile', None)
        if not request.user.is_staff and not professor:
            return Response({'detail': 'Accès refusé'}, status=403)

        all_students = Student.objects.filter(user__isnull=False)
        data = []

        professor_course_titles = set()
        if request.user.is_staff:
            professor_course_titles = set(course.titre for course in Course.objects.all())
        else:
            professor_course_titles.update(
                Course.objects.filter(professeur__icontains=professor.nom).values_list('titre', flat=True)
            )
            professor_course_titles.update(
                Course.objects.filter(notes__professor=professor).values_list('titre', flat=True)
            )

        for student in all_students:
            conversations = Conversation.objects.filter(user=student.user)
            if professor:
                if not professor_course_titles:
                    continue
                user_messages = ChatMessage.objects.filter(conversation__in=conversations, sender='user')
                matched = False
                for msg in user_messages:
                    text = (msg.text or '').lower()
                    if any(title.lower() in text for title in professor_course_titles):
                        matched = True
                        break
                if not matched:
                    continue

            conv_count = conversations.count()
            last_user_messages = ChatMessage.objects.filter(conversation__in=conversations, sender='user').order_by('-timestamp')[:5]
            last_message = last_user_messages.first()
            last_conversation = conversations.order_by('-updated_at').first()
            data.append({
                'student_id': student.id,
                'nom': student.nom,
                'email': student.email,
                'niveau': student.niveau,
                'conversations_count': conv_count,
                'last_message': last_message.text if last_message else None,
                'last_message_at': last_message.timestamp.isoformat() if last_message else None,
                'last_conversation_title': last_conversation.title if last_conversation else None,
                'last_conversation_updated': last_conversation.updated_at.isoformat() if last_conversation else None,
                'recent_user_queries': [msg.text for msg in last_user_messages],
            })
        return Response(data)
