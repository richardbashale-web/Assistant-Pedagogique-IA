from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, AdminCentral, AdminGestionnaire, SecretaireFacultaire, Professor, Student


@receiver(post_delete, sender=AdminCentral)
@receiver(post_delete, sender=AdminGestionnaire)
@receiver(post_delete, sender=SecretaireFacultaire)
@receiver(post_delete, sender=Professor)
@receiver(post_delete, sender=Student)
@receiver(post_delete, sender=UserProfile)
def delete_associated_user(sender, instance, **kwargs):
    """
    Lorsque l'un des modèles de profil ou de rôle est supprimé, 
    supprime automatiquement le compte User Django associé.
    """
    user_id = getattr(instance, 'user_id', None)
    if user_id is None:
        return

    user = User.objects.filter(pk=user_id).first()
    if user is not None:
        user.delete()
