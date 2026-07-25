from django.test import TestCase
from django.contrib.auth.models import User, Group, Permission
from rest_framework.test import APIClient
from rest_framework import status
from .models import Role, UserProfile, AdminCentral, AdminGestionnaire, SecretaireFacultaire, Professor, Student
from .permissions import init_roles, assign_role_to_user, user_has_role, can_manage_users


class RoleInitializationTest(TestCase):
    """Tests pour l'initialisation des rôles"""

    def test_init_roles_creates_all_roles(self):
        """Vérifie que init_roles crée tous les rôles"""
        init_roles()
        roles = Role.objects.all()
        self.assertEqual(roles.count(), 5)

    def test_init_roles_creates_groups(self):
        """Vérifie que les groupes Django sont créés"""
        init_roles()
        groups = Group.objects.all()
        self.assertGreater(groups.count(), 0)

    def test_roles_have_descriptions(self):
        """Vérifie que tous les rôles ont une description"""
        init_roles()
        for role in Role.objects.all():
            self.assertTrue(len(role.description) > 0)


class UserRoleAssignmentTest(TestCase):
    """Tests pour l'assignation des rôles"""

    def setUp(self):
        init_roles()
        self.user = User.objects.create_user('testuser', 'test@test.com', 'pass123')

    def test_assign_role_to_user(self):
        """Teste l'assignation d'un rôle à un utilisateur"""
        assign_role_to_user(self.user, 'etudiant')
        self.assertTrue(user_has_role(self.user, 'etudiant'))

    def test_user_has_role_returns_false_for_wrong_role(self):
        """Teste que has_role retourne False pour le mauvais rôle"""
        assign_role_to_user(self.user, 'etudiant')
        self.assertFalse(user_has_role(self.user, 'professeur'))

    def test_user_profile_created_with_role(self):
        """Teste que le profil utilisateur est créé avec le rôle"""
        assign_role_to_user(self.user, 'etudiant')
        profile = self.user.profile
        self.assertEqual(profile.role.nom, 'etudiant')


class AdminHierarchyTest(TestCase):
    """Tests pour la hiérarchie administrative"""

    def setUp(self):
        init_roles()
        self.admin_central_user = User.objects.create_user('admin_central', 'admin@test.com', 'pass123')
        assign_role_to_user(self.admin_central_user, 'admin_central')
        self.admin_central = AdminCentral.objects.create(
            user=self.admin_central_user,
            profile=self.admin_central_user.profile
        )

    def test_admin_central_can_manage_users(self):
        """Teste que Admin Central peut gérer les utilisateurs"""
        self.assertTrue(can_manage_users(self.admin_central_user))

    def test_admin_gestionnaire_relation(self):
        """Teste la relation entre Admin Central et Admin Gestionnaire"""
        gestionnaire_user = User.objects.create_user('gestionnaire', 'gest@test.com', 'pass123')
        profile = UserProfile.objects.create(user=gestionnaire_user)
        assign_role_to_user(gestionnaire_user, 'admin_gestionnaire')

        gestionnaire = AdminGestionnaire.objects.create(
            user=gestionnaire_user,
            profile=profile,
            admin_central=self.admin_central
        )

        self.assertEqual(gestionnaire.admin_central, self.admin_central)


class RolePermissionsTest(TestCase):
    """Tests pour les permissions liées aux rôles"""

    def setUp(self):
        init_roles()

    def test_professor_role_has_content_permissions(self):
        """Teste que le rôle Professeur a les permissions de contenu"""
        prof_role = Role.objects.get(nom='professeur')
        self.assertGreater(prof_role.permissions.count(), 0)

    def test_student_role_permissions_exist(self):
        """Teste que le rôle Étudiant a ses permissions"""
        student_role = Role.objects.get(nom='etudiant')
        self.assertGreater(student_role.permissions.count(), 0)


class UserProfileTest(TestCase):
    """Tests pour le modèle UserProfile"""

    def setUp(self):
        init_roles()
        self.user = User.objects.create_user('testuser', 'test@test.com', 'pass123')

    def test_user_profile_creation(self):
        """Teste la création d'un profil utilisateur"""
        profile = UserProfile.objects.create(
            user=self.user,
            nom_complet='Test User',
            est_actif=True
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.nom_complet, 'Test User')
        self.assertTrue(profile.est_actif)

    def test_user_profile_string_representation(self):
        """Teste la représentation en chaîne du profil"""
        profile = UserProfile.objects.create(user=self.user)
        assign_role_to_user(self.user, 'etudiant')
        self.assertIn('test user', str(profile).lower())
        self.assertIn('étudiant', str(profile).lower())


class CascadeDeleteTest(TestCase):
    """Tests pour valider la suppression en cascade complète des comptes et rôles"""

    def setUp(self):
        init_roles()
        self.central_user = User.objects.create_user('central', 'central@test.com', 'pass123')
        assign_role_to_user(self.central_user, 'admin_central')
        self.admin_central = AdminCentral.objects.create(
            user=self.central_user,
            profile=self.central_user.profile
        )

        self.gest_user = User.objects.create_user('gestionnaire', 'gest@test.com', 'pass123')
        assign_role_to_user(self.gest_user, 'admin_gestionnaire')
        self.admin_gestionnaire = AdminGestionnaire.objects.create(
            user=self.gest_user,
            profile=self.gest_user.profile,
            admin_central=self.admin_central
        )

    def test_delete_admin_central_deletes_all_linked_users(self):
        """Vérifie que la suppression d'un AdminCentral supprime le user central et le gestionnaire lié"""
        central_user_id = self.central_user.id
        gest_user_id = self.gest_user.id

        self.admin_central.delete()

        self.assertFalse(User.objects.filter(id=central_user_id).exists())
        self.assertFalse(User.objects.filter(id=gest_user_id).exists())
        self.assertFalse(AdminGestionnaire.objects.filter(id=self.admin_gestionnaire.id).exists())

