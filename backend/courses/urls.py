from django.urls import path
from .views import CourseListView, CourseNoteListCreateView, ProfessorStudentProgressView

urlpatterns = [
    path('courses/', CourseListView.as_view(), name='courses'),
    path('course-notes/', CourseNoteListCreateView.as_view(), name='course_notes'),
    path('progress/students/', ProfessorStudentProgressView.as_view(), name='student_progress'),
]