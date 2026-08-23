from django.urls import path
from .views import CourseListView, CourseNoteListCreateView, CourseNoteRetrieveUpdateDestroyView, ProfessorStudentProgressView, CourseRetrieveUpdateDestroyView, CourseAssignmentView

urlpatterns = [
    path('courses/', CourseListView.as_view(), name='courses'),
    path('courses/<int:pk>/', CourseRetrieveUpdateDestroyView.as_view(), name='course_detail'),
    path('courses/<int:pk>/assignments/', CourseAssignmentView.as_view(), name='course_assignments'),
    path('course-notes/', CourseNoteListCreateView.as_view(), name='course_notes'),
    path('course-notes/<int:pk>/', CourseNoteRetrieveUpdateDestroyView.as_view(), name='course_notes_detail'),
    path('progress/students/', ProfessorStudentProgressView.as_view(), name='student_progress'),
]
