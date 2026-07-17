from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIRequestFactory

from chatbot import ml_model
from chatbot.views import find_course_notes_for_message, format_notes_response
from courses.models import Course, CourseNote
from courses.views import CourseNoteListCreateView
from users.models import Faculty, Professor, Role, UserProfile


class GeminiModelSelectionTests(SimpleTestCase):
    @patch("chatbot.ml_model.requests.post")
    def test_uses_supported_gemini_model_first(self, mock_post):
        class FakeResponse:
            status_code = 200
            text = ""

            def json(self):
                return {
                    "candidates": [
                        {"content": {"parts": [{"text": "Bonjour depuis Gemini"}]}}
                    ]
                }

        mock_post.return_value = FakeResponse()

        with self.settings(GEMINI_API_KEY="fake-key"):
            result = ml_model._gemini_generate_text([{"text": "Bonjour"}])

        self.assertEqual(result, "Bonjour depuis Gemini")
        called_url = mock_post.call_args.args[0]
        self.assertIn("gemini-2.5-flash", called_url)
        self.assertNotIn("gemini-2.0-flash", called_url)


class CourseNoteRetrievalTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.faculty = Faculty.objects.create(
            code="sciences_informatique_ia",
            nom="Sciences Informatique",
            description="",
        )
        self.role = Role.objects.create(nom="professeur", description="Professeur")
        self.user_profile = UserProfile.objects.create(
            user=User.objects.create_user(username="prof1", email="prof1@example.com", password="1234"),
            role=self.role,
            nom_complet="Prof Test",
        )
        self.user = self.user_profile.user
        self.professor = Professor.objects.create(
            user=self.user,
            profile=self.user_profile,
            nom="Prof Test",
            email="prof1@example.com",
            specialite="Informatique",
            faculte=self.faculty,
        )
        self.course = Course.objects.create(
            titre="Programmation Python",
            description="Cours de Python",
            professeur="Prof Test",
        )
        self.note = CourseNote.objects.create(
            course=self.course,
            professor=self.professor,
            title="Récursivité",
            content="La récursivité est un concept central en programmation.",
        )

    def test_finds_relevant_notes_for_topic_question(self):
        notes = find_course_notes_for_message("Explique moi la récursivité en python")

        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].title, "Récursivité")

    def test_professor_can_create_note(self):
        request = self.factory.post(
            "/api/course-notes/",
            {"course": self.course.id, "title": "Variables", "content": "Les variables stockent des valeurs."},
            format="json",
        )
        request.user = self.user
        view = CourseNoteListCreateView()
        view.request = request
        view.format_kwarg = None
        serializer = view.get_serializer(
            data={"course": self.course.id, "title": "Variables", "content": "Les variables stockent des valeurs."},
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        view.perform_create(serializer)
        self.assertEqual(CourseNote.objects.filter(title="Variables").count(), 1)
        self.assertEqual(serializer.instance.professor, self.professor)

    def test_notes_response_mentions_professor_and_course(self):
        notes = find_course_notes_for_message("Peux-tu m'expliquer la récursivité ?")
        reply = format_notes_response(notes)
        self.assertIn("D’après les notes", reply)
        self.assertIn("Prof Test", reply)
        self.assertIn("Programmation Python", reply)

    def test_finds_notes_for_general_definition_question(self):
        note = CourseNote.objects.create(
            course=self.course,
            professor=self.professor,
            title="Système d'information",
            content="Un système d'information est un ensemble de personnes, de processus et de technologies qui collectent et traitent des données.",
        )

        notes = find_course_notes_for_message("C'est quoi un système d'information ?")

        self.assertTrue(notes)
        self.assertIn(note, notes)
