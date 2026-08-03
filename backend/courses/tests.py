import os

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .models import Course, CourseNote
from .serializers import CourseSerializer
from .views import CourseNoteListCreateView
from users.models import Faculty, Professor, Role, UserProfile


class CourseSerializerTests(TestCase):
    def test_course_requires_at_least_one_promotion(self):
        faculty = Faculty.objects.create(code='droit', nom='Droit')
        role = Role.objects.create(nom='professeur', description='Professeur')
        user = User.objects.create_user(username='prof_test', password='secret123')
        profile = UserProfile.objects.create(user=user, role=role, nom_complet='Prof Test')
        professor = Professor.objects.create(
            user=user,
            profile=profile,
            nom='Prof Test',
            email='prof.test@example.com',
            specialite='Informatique',
            faculte=faculty,
        )

        serializer = CourseSerializer(data={
            'titre': 'Introduction à l’IA',
            'description': 'Cours de base',
            'professeur': professor.id,
            'promotions': [],
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('promotions', serializer.errors)


class CourseNoteViewTests(TestCase):
    def test_uploaded_attachment_text_is_stored_for_chatbot_retrieval(self):
        faculty = Faculty.objects.create(code='sciences_info_comm', nom='Sciences de l’Information et Communication')
        role = Role.objects.create(nom='professeur', description='Professeur')

        user = User.objects.create_user(username='prof_file', password='secret123')
        profile = UserProfile.objects.create(user=user, role=role, nom_complet='Prof File')
        professor = Professor.objects.create(
            user=user,
            profile=profile,
            nom='Prof File',
            email='prof.file@example.com',
            specialite='Informatique',
            faculte=faculty,
        )

        course = Course.objects.create(
            titre='Python avancé',
            description='Cours',
            professeur=professor,
            faculte=faculty,
            promotions=['L2'],
        )

        uploaded_file = SimpleUploadedFile(
            'notes.txt',
            b'Chapitre 1\nLes variables en Python sont essentielles.',
            content_type='text/plain'
        )
        request = APIRequestFactory().post('/api/course-notes/', {
            'course': course.id,
            'title': 'Note test',
            'content': '',
            'attachment': uploaded_file,
        }, format='multipart')
        force_authenticate(request, user=user)

        response = CourseNoteListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        note = CourseNote.objects.get(id=response.data['id'])
        self.assertIn('variables en Python', note.content)

    def test_professor_cannot_create_note_for_another_professor_course(self):
        faculty = Faculty.objects.create(code='sciences_informatique_ia', nom='Sciences Informatique et IA')
        role = Role.objects.create(nom='professeur', description='Professeur')

        user_one = User.objects.create_user(username='prof_one', password='secret123')
        profile_one = UserProfile.objects.create(user=user_one, role=role, nom_complet='Prof One')
        professor_one = Professor.objects.create(
            user=user_one,
            profile=profile_one,
            nom='Prof One',
            email='prof.one@example.com',
            specialite='Informatique',
            faculte=faculty,
        )

        user_two = User.objects.create_user(username='prof_two', password='secret123')
        profile_two = UserProfile.objects.create(user=user_two, role=role, nom_complet='Prof Two')
        professor_two = Professor.objects.create(
            user=user_two,
            profile=profile_two,
            nom='Prof Two',
            email='prof.two@example.com',
            specialite='Maths',
            faculte=faculty,
        )

        own_course = Course.objects.create(
            titre='Algorithmes',
            description='Cours',
            professeur=professor_one,
            faculte=faculty,
            promotions=['L1'],
        )
        other_course = Course.objects.create(
            titre='Base de données',
            description='Cours',
            professeur=professor_two,
            faculte=faculty,
            promotions=['L2'],
        )

        request = APIRequestFactory().post('/api/course-notes/', {
            'course': other_course.id,
            'title': 'Note test',
            'content': 'Contenu',
        })
        force_authenticate(request, user=user_one)

        response = CourseNoteListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn('course', response.data)
        self.assertEqual(Course.objects.filter(notes__isnull=False).count(), 0)

        self.assertTrue(own_course.id)

    def test_deleting_course_note_removes_attachment_file(self):
        faculty = Faculty.objects.create(code='sciences_info_comm', nom='Sciences de l’Information et Communication')
        role = Role.objects.create(nom='professeur', description='Professeur')

        user = User.objects.create_user(username='prof_delete', password='secret123')
        profile = UserProfile.objects.create(user=user, role=role, nom_complet='Prof Delete')
        professor = Professor.objects.create(
            user=user,
            profile=profile,
            nom='Prof Delete',
            email='prof.delete@example.com',
            specialite='Informatique',
            faculte=faculty,
        )

        course = Course.objects.create(
            titre='Suppression fichiers',
            description='Cours',
            professeur=professor,
            faculte=faculty,
            promotions=['L1'],
        )

        uploaded_file = SimpleUploadedFile(
            'note.pdf',
            b'%PDF-1.4 dummy pdf content',
            content_type='application/pdf'
        )
        note = CourseNote.objects.create(
            course=course,
            professor=professor,
            title='Note suppression',
            content='Test de suppression',
            attachment=uploaded_file,
        )

        attachment_path = note.attachment.path
        self.assertTrue(os.path.exists(attachment_path))

        note.delete()
        self.assertFalse(os.path.exists(attachment_path))
