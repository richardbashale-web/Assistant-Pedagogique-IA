from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User, Group, Permission
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from rest_framework.test import APIClient
from rest_framework import status
from .models import Role, UserProfile, AdminCentral, AdminGestionnaire, SecretaireFacultaire, Professor, Student, Faculty
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


class OptionalPostnomAccountTest(TestCase):
    def setUp(self):
        init_roles()
        self.admin = User.objects.create_user(
            'account_admin',
            'account_admin@test.com',
            'pass123',
            is_staff=True
        )
        self.faculty = Faculty.objects.create(code='droit', nom='Droit')
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_student_can_be_created_without_postnom(self):
        response = self.client.post('/api/students/', {
            'nom': 'Kabongo',
            'postnom': '',
            'prenom': 'Alice',
            'sexe': 'M',
            'email': 'alice@test.com',
            'niveau': 'L1',
            'matricule': 'STU-001',
            'faculte': self.faculty.code,
            'username': 'alice_student',
            'password': 'password123',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertEqual(Student.objects.get(matricule='STU-001').postnom, '')

    def test_professor_can_be_created_without_postnom(self):
        response = self.client.post('/api/professors/', {
            'nom': 'Bashale',
            'postnom': '',
            'prenom': 'Richard',
            'sexe': '',
            'email': 'richard@test.com',
            'specialite': 'Informatique',
            'faculte': self.faculty.code,
            'username': 'richard_professor',
            'password': 'password123',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        professor = Professor.objects.get(email='richard@test.com')
        self.assertEqual(professor.postnom, '')
        self.assertEqual(professor.sexe, 'M')


class RolePermissionsTableRepairTest(TransactionTestCase):
    def test_migration_recreates_missing_role_permissions_table(self):
        through_model = Role.permissions.through
        table_name = through_model._meta.db_table
        executor = MigrationExecutor(connection)
        executor.migrate([('users', '0014_alter_professor_postnom_alter_student_postnom')])

        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(through_model)

        executor = MigrationExecutor(connection)
        executor.migrate([('users', '0015_repair_role_permissions_table')])

        self.assertIn(table_name, connection.introspection.table_names())


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

    def test_admin_central_can_delete_gestionnaire_with_linked_secretaire(self):
        faculty = Faculty.objects.create(code='droit', nom='Droit')
        secretary_user = User.objects.create_user('secretaire', 'sec@test.com', 'pass123')
        assign_role_to_user(secretary_user, 'secretaire_facultaire')
        secretary = SecretaireFacultaire.objects.create(
            user=secretary_user,
            profile=secretary_user.profile,
            admin_gestionnaire=self.admin_gestionnaire,
            faculte=faculty
        )
        client = APIClient()
        client.force_authenticate(user=self.central_user)

        response = client.delete(
            f'/api/admin-gestionnaire/{self.gest_user.id}/delete/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertFalse(User.objects.filter(id=self.gest_user.id).exists())
        self.assertFalse(User.objects.filter(id=secretary_user.id).exists())
        self.assertFalse(SecretaireFacultaire.objects.filter(id=secretary.id).exists())

    def test_admin_central_can_manage_secretaire_account(self):
        faculty = Faculty.objects.create(code='droit', nom='Droit')
        secretary_user = User.objects.create_user('secretaire', 'sec@test.com', 'pass123')
        assign_role_to_user(secretary_user, 'secretaire_facultaire')
        secretary = SecretaireFacultaire.objects.create(
            user=secretary_user,
            profile=secretary_user.profile,
            admin_gestionnaire=self.admin_gestionnaire,
            faculte=faculty
        )
        client = APIClient()
        client.force_authenticate(user=self.central_user)

        update_response = client.patch(
            f'/api/secretaire/{secretary_user.id}/update/',
            {'nom_complet': 'Secrétaire Modifié', 'email': 'updated@test.com', 'faculte': 'droit'},
            format='json'
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK, update_response.content)
        secretary_user.refresh_from_db()
        secretary.profile.refresh_from_db()
        self.assertEqual(secretary_user.email, 'updated@test.com')
        self.assertEqual(secretary.profile.nom_complet, 'Secrétaire Modifié')

        toggle_response = client.patch(
            f'/api/secretaire/{secretary_user.id}/toggle-active/'
        )
        self.assertEqual(toggle_response.status_code, status.HTTP_200_OK, toggle_response.content)
        secretary.profile.refresh_from_db()
        self.assertFalse(secretary.profile.est_actif)

        delete_response = client.delete(
            f'/api/secretaire/{secretary_user.id}/delete/'
        )
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK, delete_response.content)
        self.assertFalse(User.objects.filter(id=secretary_user.id).exists())
