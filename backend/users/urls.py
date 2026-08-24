from django.urls import path
from .views import (
    StudentListCreateView, StudentDetailView,
    StudentImportView, StudentToggleActiveView,
    ProfessorListCreateView, ProfessorDetailView, ProfessorToggleActiveView,
    CurrentUserView, initialize_roles, list_roles, user_role, assign_role,
    list_users_by_role, create_admin_gestionnaire, create_secretaire,
    update_admin_gestionnaire, delete_admin_gestionnaire, toggle_admin_gestionnaire_active,
    update_secretaire, delete_secretaire, toggle_secretaire_active,
    list_professors, list_students, list_faculties, get_faculty,
    get_faculty_professors, get_faculty_students, update_faculty,
    dashboard_stats
)

urlpatterns = [
    # --- \u00c9tudiants ---
    # IMPORTANT : students/import/ et students/<id>/toggle-active/ AVANT students/<int:pk>/
    path('students/import/', StudentImportView.as_view(), name='student-import'),
    path('students/', StudentListCreateView.as_view(), name='student-list'),
    path('students/<int:pk>/', StudentDetailView.as_view(), name='student-detail'),
    path('students/<int:pk>/toggle-active/', StudentToggleActiveView.as_view(), name='student-toggle-active'),

    # --- Professeurs ---
    path('professors/', ProfessorListCreateView.as_view(), name='professor-list'),
    path('professors/<int:pk>/', ProfessorDetailView.as_view(), name='professor-detail'),
    path('professors/<int:pk>/toggle-active/', ProfessorToggleActiveView.as_view(), name='professor-toggle-active'),

    # --- Utilisateur courant ---
    path('me/', CurrentUserView.as_view(), name='current_user'),

    # --- Gestion des r\u00f4les ---
    path('roles/initialize/', initialize_roles, name='initialize_roles'),
    path('roles/', list_roles, name='list_roles'),
    path('roles/my-role/', user_role, name='user_role'),
    path('roles/assign/', assign_role, name='assign_role'),
    path('roles/users/', list_users_by_role, name='list_users_by_role'),

    # --- Cr\u00e9ation des utilisateurs par r\u00f4le ---
    path('admin-gestionnaire/create/', create_admin_gestionnaire, name='create_admin_gestionnaire'),
    path('secretaire/create/', create_secretaire, name='create_secretaire'),

    # --- Modifier / Supprimer / Activer-D\u00e9sactiver un Admin Gestionnaire ---
    path('admin-gestionnaire/<int:user_id>/update/', update_admin_gestionnaire, name='update_admin_gestionnaire'),
    path('admin-gestionnaire/<int:user_id>/delete/', delete_admin_gestionnaire, name='delete_admin_gestionnaire'),
    path('admin-gestionnaire/<int:user_id>/toggle-active/', toggle_admin_gestionnaire_active, name='toggle_admin_gestionnaire_active'),

    # --- Modifier / Supprimer / Activer-D\u00e9sactiver un Secr\u00e9taire Facultaire ---
    path('secretaire/<int:user_id>/update/', update_secretaire, name='update_secretaire'),
    path('secretaire/<int:user_id>/delete/', delete_secretaire, name='delete_secretaire'),
    path('secretaire/<int:user_id>/toggle-active/', toggle_secretaire_active, name='toggle_secretaire_active'),

    # --- Lister les utilisateurs ---
    path('professors/list/', list_professors, name='list_professors_admin'),
    path('students/list/', list_students, name='list_students_admin'),

    # --- Facult\u00e9s ---
    path('faculties/', list_faculties, name='list_faculties'),
    path('faculties/<str:faculty_code>/', get_faculty, name='get_faculty'),
    path('faculties/<str:faculty_code>/update/', update_faculty, name='update_faculty'),
    path('faculties/<str:faculty_code>/professors/', get_faculty_professors, name='get_faculty_professors'),
    path('faculties/<str:faculty_code>/students/', get_faculty_students, name='get_faculty_students'),

    # --- Dashboard ---
    path('dashboard/stats/', dashboard_stats, name='dashboard_stats'),
]