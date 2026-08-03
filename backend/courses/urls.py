from django.urls import path
from .views import CourseListView, CourseNoteListCreateView, CourseNoteRetrieveUpdateDestroyView, ProfessorStudentProgressView, CourseRetrieveUpdateDestroyView

urlpatterns = [
    path('courses/', CourseListView.as_view(), name='courses'),
    path('courses/<int:pk>/', CourseRetrieveUpdateDestroyView.as_view(), name='course_detail'),
    path('course-notes/', CourseNoteListCreateView.as_view(), name='course_notes'),
    path('course-notes/<int:pk>/', CourseNoteRetrieveUpdateDestroyView.as_view(), name='course_notes_detail'),
    path('progress/students/', ProfessorStudentProgressView.as_view(), name='student_progress'),
]