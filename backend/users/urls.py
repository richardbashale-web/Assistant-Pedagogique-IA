from django.urls import path
from .views import (
    StudentListCreateView, StudentDetailView,
    ProfessorListCreateView, ProfessorDetailView,
    CurrentUserView, initialize_roles, list_roles, user_role, assign_role,
    list_users_by_role, create_admin_gestionnaire, create_secretaire,
    list_professors, list_students, list_faculties, get_faculty,
    get_faculty_professors, get_faculty_students, update_faculty,
    dashboard_stats
)

urlpatterns = [
    # Vues existantes
    path('students/', StudentListCreateView.as_view(), name='student-list'),
    path('students/<int:pk>/', StudentDetailView.as_view(), name='student-detail'),
    path('professors/', ProfessorListCreateView.as_view(), name='professor-list'),
    path('professors/<int:pk>/', ProfessorDetailView.as_view(), name='professor-detail'),
    path('me/', CurrentUserView.as_view(), name='current_user'),

    # Vues pour la gestion des rôles
    path('roles/initialize/', initialize_roles, name='initialize_roles'),
    path('roles/', list_roles, name='list_roles'),
    path('roles/my-role/', user_role, name='user_role'),
    path('roles/assign/', assign_role, name='assign_role'),
    path('roles/users/', list_users_by_role, name='list_users_by_role'),

    # Vues pour la création des utilisateurs par rôle
    path('admin-gestionnaire/create/', create_admin_gestionnaire, name='create_admin_gestionnaire'),
    path('secretaire/create/', create_secretaire, name='create_secretaire'),

    # Vues pour lister les utilisateurs
    path('professors/list/', list_professors, name='list_professors_admin'),
    path('students/list/', list_students, name='list_students_admin'),

    # Vues pour les facultés
    path('faculties/', list_faculties, name='list_faculties'),
    path('faculties/<str:faculty_code>/', get_faculty, name='get_faculty'),
    path('faculties/<str:faculty_code>/update/', update_faculty, name='update_faculty'),
    path('faculties/<str:faculty_code>/professors/', get_faculty_professors, name='get_faculty_professors'),
    path('faculties/<str:faculty_code>/students/', get_faculty_students, name='get_faculty_students'),

    # Dashboard stats (basé sur le rôle)
    path('dashboard/stats/', dashboard_stats, name='dashboard_stats'),
]

