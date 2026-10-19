
"""Gestion des permissions par rôle."""

from django.contrib.auth.models import Group, Permission
from django.db import transaction

from .models import Role, UserProfile


ROLE_CONFIG = {
    "admin_central": {
        "group": "Admin Central",
        "description": "Administrateur central avec tous les privilèges",
        "permissions": [
            "add_user", "change_user", "delete_user",
            "add_useradmin", "change_useradmin", "delete_useradmin",
            "add_admincentral", "change_admincentral", "delete_admincentral",
            "add_adminggestionnaire", "change_adminggestionnaire",
            "delete_adminggestionnaire",
            "add_role", "change_role", "delete_role",
            "add_userprofile", "change_userprofile", "delete_userprofile",
        ],
    },
    "admin_gestionnaire": {
        "group": "Admin Gestionnaire",
        "description": "Gère les secrétaires facultaires et les informations des facultés",
        "permissions": [
            "add_secretairefacultaire",
            "change_secretairefacultaire",
            "delete_secretairefacultaire",
            "add_professor", "change_professor", "delete_professor",
            "add_userprofile", "change_userprofile",
        ],
    },
    "professeur": {
        "group": "Professeur",
        "description": "Responsable des contenus pédagogiques",
        "permissions": [
            "add_course", "change_course", "delete_course",
            "add_coursenote", "change_coursenote", "delete_coursenote",
        ],
    },
    "secretaire_facultaire": {
        "group": "Secrétaire Facultaire",
        "description": "Gère les enseignants au niveau de la faculté",
        "permissions": [
            "add_professor", "change_professor", "delete_professor",
            "add_userprofile", "change_userprofile",
            "view_student",
        ],
    },
    "etudiant": {
        "group": "Étudiant",
        "description": "Utilisateur principal de l'assistant pédagogique",
        "permissions": [
            "view_course", "view_coursenote",
            "add_chatmessage", "add_conversation",
        ],
    },
}


@transaction.atomic
def init_roles():
    """
    Initialise les rôles et les groupes.
    Retourne les permissions manquantes pour faciliter le diagnostic.
    """

    missing_permissions = []

    for role_nom, config in ROLE_CONFIG.items():
        role, _ = Role.objects.get_or_create(
            nom=role_nom,
            defaults={"description": config["description"]},
        )

        # Synchroniser aussi la description des rôles déjà existants.
        if role.description != config["description"]:
            role.description = config["description"]
            role.save(update_fields=["description"])

        group, _ = Group.objects.get_or_create(
            name=config["group"]
        )

        # Recherche des permissions disponibles.
        # Remarque : un filtrage strict par application nécessite de
        # connaître l'app_label de chaque modèle du projet.
        permissions = Permission.objects.filter(
            codename__in=config["permissions"]
        )

        found_codenames = set(
            permissions.values_list("codename", flat=True)
        )

        missing = set(config["permissions"]) - found_codenames

        if missing:
            missing_permissions.append({
                "role": role_nom,
                "permissions": sorted(missing),
            })

        # Synchroniser les permissions du rôle et du groupe.
        role.permissions.set(permissions)
        group.permissions.set(permissions)

    return {
        "success": not missing_permissions,
        "missing_permissions": missing_permissions,
    }


@transaction.atomic
def assign_role_to_user(user, role_nom):
    """
    Attribue un rôle au profil d'un utilisateur.
    En cas d'erreur, lève une exception afin que la création du compte
    puisse être annulée par la transaction appelante.
    """

    if role_nom not in ROLE_CONFIG:
        raise ValueError(f"Rôle non reconnu : {role_nom}")

    config = ROLE_CONFIG[role_nom]

    # Créer le rôle s'il manque dans la base de données.
    # Cela évite qu'une absence de données initialisées laisse
    # silencieusement un utilisateur sans rôle.
    role, _ = Role.objects.get_or_create(
        nom=role_nom,
        defaults={"description": config["description"]},
    )

    # Garantir l'existence du groupe associé.
    group, _ = Group.objects.get_or_create(
        name=config["group"]
    )

    # Créer ou récupérer le profil de l'utilisateur.
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "nom_complet": user.get_full_name() or user.username,
        },
    )

    # Enregistrer le rôle sur le profil.
    profile.role = role

    if not profile.nom_complet:
        profile.nom_complet = (
            user.get_full_name() or user.username
        )

    profile.save()
    profile.refresh_from_db()

    # Vérification stricte de l'enregistrement.
    if profile.role_id != role.pk:
        raise ValueError(
            f"Le rôle '{role_nom}' n'a pas été enregistré correctement."
        )

    # Appliquer au groupe les permissions configurées sur le rôle.
    group.permissions.add(*role.permissions.all())

    # Ajouter l'utilisateur au groupe associé.
    user.groups.add(group)

    # Vérifier aussi que l'utilisateur appartient au groupe attendu.
    if not user.groups.filter(pk=group.pk).exists():
        raise ValueError(
            f"L'utilisateur n'a pas été ajouté au groupe '{group.name}'."
        )

    return True


def user_has_role(user, role_nom):
    """Vérifie si l'utilisateur possède le rôle demandé."""

    if not user or not user.is_authenticated:
        return False

    try:
        profile = user.profile
        return bool(profile.role and profile.role.nom == role_nom)
    except UserProfile.DoesNotExist:
        return user.is_superuser and role_nom == "admin_central"


def can_manage_users(user):
    """Vérifie si l'utilisateur peut gérer d'autres utilisateurs."""

    return (
        user_has_role(user, "admin_central")
        or user_has_role(user, "admin_gestionnaire")
        or user_has_role(user, "secretaire_facultaire")
        or user.is_superuser
    )


def can_manage_content(user):
    """Vérifie si l'utilisateur peut gérer les contenus pédagogiques."""

    return user_has_role(user, "professeur")
