from django.contrib import admin
from .models import Role, UserProfile, AdminCentral, AdminGestionnaire, SecretaireFacultaire, Professor, Student, Faculty


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'doyen', 'email')
    search_fields = ('code', 'nom', 'doyen')
    readonly_fields = ('date_creation',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description', 'date_creation')
    search_fields = ('nom',)
    filter_horizontal = ('permissions',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'nom_complet', 'est_actif', 'date_creation')
    list_filter = ('role', 'est_actif', 'date_creation')
    search_fields = ('user__username', 'nom_complet')
    readonly_fields = ('date_creation', 'date_modification')


@admin.register(AdminCentral)
class AdminCentralAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_nomination')
    search_fields = ('user__username', 'notes')
    readonly_fields = ('date_nomination',)


@admin.register(AdminGestionnaire)
class AdminGestionnaireAdmin(admin.ModelAdmin):
    list_display = ('user', 'admin_central', 'date_nomination')
    list_filter = ('admin_central', 'date_nomination')
    search_fields = ('user__username', 'notes')
    readonly_fields = ('date_nomination',)


@admin.register(SecretaireFacultaire)
class SecretaireFacultaireAdmin(admin.ModelAdmin):
    list_display = ('user', 'faculte', 'admin_gestionnaire', 'date_nomination')
    list_filter = ('faculte', 'admin_gestionnaire', 'date_nomination')
    search_fields = ('user__username', 'faculte__nom', 'notes')
    readonly_fields = ('date_nomination',)


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('nom', 'specialite', 'faculte', 'enregistre_par', 'date_inscription')
    list_filter = ('faculte', 'date_inscription')
    search_fields = ('nom', 'email', 'specialite')
    readonly_fields = ('date_inscription',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('nom', 'email', 'niveau', 'faculte', 'matricule', 'date_inscription')
    list_filter = ('niveau', 'faculte', 'date_inscription')
    search_fields = ('nom', 'email', 'matricule')
    readonly_fields = ('date_inscription',)
