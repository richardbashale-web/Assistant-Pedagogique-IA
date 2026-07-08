"""Gestion des permissions par rôle"""
from django.contrib.auth.models import Permission, Group
from .models import Role, UserProfile


def init_roles():
    """Initialise les rôles et permissions du système"""

    # Créer les groupes s'ils n'existent pas
    admin_central_group, _ = Group.objects.get_or_create(name='Admin Central')
    admin_gestionnaire_group, _ = Group.objects.get_or_create(name='Admin Gestionnaire')
    professeur_group, _ = Group.objects.get_or_create(name='Professeur')
    secretaire_group, _ = Group.objects.get_or_create(name='Secrétaire Facultaire')
    etudiant_group, _ = Group.objects.get_or_create(name='Étudiant')

    # Permissions pour Admin Central
    admin_central_perms = [
        'add_user', 'change_user', 'delete_user',
        'add_useradmin', 'change_useradmin', 'delete_useradmin',
        'add_admincentral', 'change_admincentral', 'delete_admincentral',
        'add_adminggestionnaire', 'change_adminggestionnaire', 'delete_adminggestionnaire',
        'add_role', 'change_role', 'delete_role',
        'add_userprofile', 'change_userprofile', 'delete_userprofile',
    ]

    # Permissions pour Admin Gestionnaire
    admin_gestionnaire_perms = [
        'add_secretairefacultaire', 'change_secretairefacultaire', 'delete_secretairefacultaire',
        'add_professor', 'change_professor', 'delete_professor',
        'add_userprofile', 'change_userprofile',
    ]

    # Permissions pour Professeur
    professeur_perms = [
        'add_course', 'change_course', 'delete_course',
        'add_coursenote', 'change_coursenote', 'delete_coursenote',
    ]

    # Permissions pour Secrétaire Facultaire
    secretaire_perms = [
        'add_professor', 'change_professor', 'delete_professor',
        'add_userprofile', 'change_userprofile',
        'view_student',
    ]

    # Permissions pour Étudiant
    etudiant_perms = [
        'view_course',
        'view_coursenote',
        'add_chatmessage', 'add_conversation',
    ]

    def add_perms_to_group(group, perm_names):
        for perm_name in perm_names:
            try:
                perms = Permission.objects.filter(codename=perm_name)
                for perm in perms:
                    group.permissions.add(perm)
            except Permission.DoesNotExist:
                pass


    add_perms_to_group(admin_central_group, admin_central_perms)
    add_perms_to_group(admin_gestionnaire_group, admin_gestionnaire_perms)
    add_perms_to_group(professeur_group, professeur_perms)
    add_perms_to_group(secretaire_group, secretaire_perms)
    add_perms_to_group(etudiant_group, etudiant_perms)

    # Créer les rôles s'ils n'existent pas
    Role.objects.get_or_create(
        nom='admin_central',
        defaults={'description': 'Administrateur central avec tous les privilèges'}
    )
    Role.objects.get_or_create(
        nom='admin_gestionnaire',
        defaults={'description': 'Gère les secrétaires facultaires et les informations des facultés'}
    )
    Role.objects.get_or_create(
        nom='professeur',
        defaults={'description': 'Responsable des contenus pédagogiques'}
    )
    Role.objects.get_or_create(
        nom='secretaire_facultaire',
        defaults={'description': 'Gère les enseignants au niveau de la faculté'}
    )
    Role.objects.get_or_create(
        nom='etudiant',
        defaults={'description': 'Utilisateur principal de l\'assistant pédagogique'}
    )


def assign_role_to_user(user, role_nom):
    """Assigne un rôle à un utilisateur"""
    try:
        role = Role.objects.get(nom=role_nom)
        group = Group.objects.get(name=role.get_nom_display())

        # Créer ou récupérer le profil
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={'nom_complet': user.get_full_name() or user.username}
            )

        profile.role = role
        profile.save()

        # Ajouter l'utilisateur au groupe
        user.groups.add(group)

        return True
    except (Role.DoesNotExist, Group.DoesNotExist):
        return False


def user_has_role(user, role_nom):
    """Vérifie si l'utilisateur a un rôle spécifique"""
    try:
        profile = user.profile
        return profile.role and profile.role.nom == role_nom
    except Exception:
        # Traiter le superuser Django comme Admin Central lorsqu'il n'a pas de profil
        return user.is_superuser and role_nom == 'admin_central'


def can_manage_users(user):
    """Vérifie si l'utilisateur peut gérer d'autres utilisateurs"""
    return (user_has_role(user, 'admin_central') or
            user_has_role(user, 'admin_gestionnaire') or
            user_has_role(user, 'secretaire_facultaire') or
            user.is_superuser)


def can_manage_content(user):
    """Vérifie si l'utilisateur peut gérer les contenus pédagogiques"""
    return user_has_role(user, 'professeur')
