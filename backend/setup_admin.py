"""
Script pour initialiser le système avec un administrateur central de test.
Exécuter avec: python manage.py shell < setup_admin.py
"""

from django.contrib.auth.models import User
from users.models import Role, UserProfile, AdminCentral
from users.permissions import init_roles

def setup_system():
    """Configure le système avec un admin central par défaut"""

    print("=" * 50)
    print("INITIALISATION DU SYSTEME")
    print("=" * 50)

    # 1. Initialiser les rôles et permissions
    print("\n[1/3] Initialisation des roles et permissions...")
    try:
        init_roles()
        print("[OK] Roles et permissions initialises")
    except Exception as e:
        print(f"[ERR] Erreur: {e}")
        return

    # 2. Créer l'administrateur central principal
    print("\n[2/3] Creation de l'administrateur central...")
    admin_username = "admin_central"
    admin_email = "admin@pedagogique.local"
    admin_password = "Admin@Pedagogique123"

    if User.objects.filter(username=admin_username).exists():
        print(f"[OK] L'utilisateur '{admin_username}' existe deja")
        admin_user = User.objects.get(username=admin_username)
    else:
        admin_user = User.objects.create_superuser(
            username=admin_username,
            email=admin_email,
            password=admin_password
        )
        print(f"[OK] Administrateur cree:")
        print(f"  - Utilisateur: {admin_username}")
        print(f"  - Email: {admin_email}")
        print(f"  - Mot de passe: {admin_password}")

    # 3. Créer le profil et le rôle administrateur
    print("\n[3/3] Configuration du profil administrateur...")
    try:
        profile, created = UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={
                'nom_complet': 'Administrateur Central',
                'est_actif': True
            }
        )

        # Assigner le rôle
        role = Role.objects.get(nom='admin_central')
        profile.role = role
        profile.save()

        # Créer la relation AdminCentral
        admin_central, created = AdminCentral.objects.get_or_create(
            user=admin_user,
            defaults={
                'profile': profile,
                'notes': 'Administrateur central du systeme'
            }
        )

        if created:
            print("[OK] Profil administrateur central configure")
        else:
            print("[OK] Profil administrateur central deja existant")

    except Exception as e:
        print(f"[ERR] Erreur lors de la configuration: {e}")
        return

    print("\n" + "=" * 50)
    print("[OK] INITIALISATION COMPLETE")
    print("=" * 50)
    print("\nIdentifiants de connexion:")
    print(f"  Utilisateur: {admin_username}")
    print(f"  Mot de passe: {admin_password}")
    print("\n[!] CHANGEZ LE MOT DE PASSE EN PRODUCTION!")
    print("=" * 50)


if __name__ == "__main__":
    setup_system()
