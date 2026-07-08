from django.db import models
from django.contrib.auth.models import User, Permission
from django.core.exceptions import ValidationError


class Faculty(models.Model):
    """Modèle pour les facultés de l'université"""
    FACULTY_CHOICES = [
        ('droit', 'Droit'),
        ('sciences_economiques', 'Sciences Économiques'),
        ('sciences_informatique_ia', 'Sciences Informatique et Intelligence Artificielle'),
        ('sciences_info_comm', 'Sciences d\'Information et Communication'),
        ('theologie', 'Théologie'),
        ('medecine', 'Médecine'),
        ('istm', 'ISTM'),
    ]

    code = models.CharField(max_length=50, choices=FACULTY_CHOICES, unique=True, primary_key=True)
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    doyen = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Faculté"
        verbose_name_plural = "Facultés"
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Role(models.Model):
    """Modèle pour définir les rôles disponibles dans le système"""
    ROLE_CHOICES = [
        ('admin_central', 'Administrateur Central'),
        ('admin_gestionnaire', 'Administrateur Gestionnaire'),
        ('professeur', 'Professeur'),
        ('secretaire_facultaire', 'Secrétaire Facultaire'),
        ('etudiant', 'Étudiant'),
    ]

    nom = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField()
    permissions = models.ManyToManyField(Permission, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rôle"
        verbose_name_plural = "Rôles"

    def __str__(self):
        return self.get_nom_display()


class UserProfile(models.Model):
    """Profil utilisateur centralisé avec gestion des rôles"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='utilisateurs')
    nom_complet = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    est_actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Profil Utilisateur"
        verbose_name_plural = "Profils Utilisateurs"

    def __str__(self):
        return f"{self.user.username} - {self.role.get_nom_display() if self.role else 'Aucun rôle'}"


class AdminCentral(models.Model):
    """Administrateur Central - gère tout le système"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_central_profile')
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='admin_central')
    date_nomination = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Admin Central"
        verbose_name_plural = "Admins Centraux"
        permissions = [
            ("manage_system", "Peut gérer le système"),
            ("manage_admin_gestionnaires", "Peut créer/modifier les admins gestionnaires"),
            ("supervise_platform", "Peut superviser la plateforme"),
            ("manage_security", "Peut gérer la sécurité"),
            ("manage_settings", "Peut gérer les paramètres généraux"),
        ]

    def __str__(self):
        return f"Admin Central: {self.user.username}"


class AdminGestionnaire(models.Model):
    """Administrateur Gestionnaire - gère les secrétaires et facultés"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_gestionnaire_profile')
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='admin_gestionnaire')
    admin_central = models.ForeignKey(AdminCentral, on_delete=models.CASCADE, null=True, blank=True, related_name='gestionnaires_geres')
    date_nomination = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Admin Gestionnaire"
        verbose_name_plural = "Admins Gestionnaires"
        permissions = [
            ("manage_secretaires", "Peut créer/modifier/supprimer les secrétaires"),
            ("manage_faculty_info", "Peut gérer les informations des facultés"),
            ("manage_user_follow_up", "Peut gérer le suivi administratif"),
        ]

    def __str__(self):
        return f"Admin Gestionnaire: {self.user.username}"


class SecretaireFacultaire(models.Model):
    """Secrétaire Facultaire - gère les enseignants au niveau de la faculté"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='secretaire_profile')
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='secretaire')
    admin_gestionnaire = models.ForeignKey(AdminGestionnaire, on_delete=models.CASCADE, null=True, related_name='secretaires_geres')
    faculte = models.ForeignKey(Faculty, on_delete=models.PROTECT, related_name='secretaires')
    date_nomination = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Secrétaire Facultaire"
        verbose_name_plural = "Secrétaires Facultaires"
        permissions = [
            ("manage_professors", "Peut gérer les informations des professeurs"),
            ("register_professors", "Peut enregistrer les enseignants"),
            ("update_professor_data", "Peut mettre à jour les données des professeurs"),
            ("manage_academic_tasks", "Peut gérer les tâches administratives académiques"),
        ]

    def __str__(self):
        return f"Secrétaire: {self.user.username} ({self.faculte.nom})"


class Professor(models.Model):
    """Professeur - responsable des contenus pédagogiques"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='professor_profile', null=True, blank=True)
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='professor', null=True, blank=True)
    nom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    specialite = models.CharField(max_length=100)
    faculte = models.ForeignKey(Faculty, on_delete=models.PROTECT, related_name='professeurs', null=True)
    telephone = models.CharField(max_length=20, blank=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    enregistre_par = models.ForeignKey(SecretaireFacultaire, on_delete=models.SET_NULL, null=True, blank=True, related_name='professeurs_enregistres')
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Professeur"
        verbose_name_plural = "Professeurs"
        permissions = [
            ("add_course_content", "Peut ajouter les cours"),
            ("modify_academic_content", "Peut modifier les contenus académiques"),
            ("update_teaching_info", "Peut mettre à jour les informations d'enseignement"),
            ("enrich_knowledge_base", "Peut enrichir la base de connaissances"),
        ]

    def __str__(self):
        return f"Pr. {self.nom}"


class Student(models.Model):
    """Étudiant - utilisateur principal de l'assistant pédagogique"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile', null=True, blank=True)
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='student', null=True, blank=True)
    nom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    niveau = models.CharField(max_length=50)
    matricule = models.CharField(max_length=50, blank=True)
    faculte = models.ForeignKey(Faculty, on_delete=models.PROTECT, related_name='etudiants', null=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Étudiant"
        verbose_name_plural = "Étudiants"
        permissions = [
            ("interact_with_chatbot", "Peut interagir avec le chatbot"),
            ("ask_academic_questions", "Peut poser des questions académiques"),
            ("access_learning_resources", "Peut accéder aux ressources pédagogiques"),
            ("receive_automated_assistance", "Peut recevoir une assistance automatisée"),
        ]

    def __str__(self):
        return f"{self.nom} ({self.niveau})"
