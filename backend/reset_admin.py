import os
import django
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# Chercher le superuser (Admin Central)
admins = User.objects.filter(is_superuser=True)

if admins.exists():
    admin = admins.first()
    # On réinitialise le mot de passe pour être sûr
    admin.set_password('admin123')
    admin.save()
    print("--- ADMIN CREDENTIALS ---")
    print(f"USERNAME: {admin.username}")
    print(f"PASSWORD: admin123")
    print("-------------------------")
else:
    print("Aucun administrateur trouvé dans la base de données.")
