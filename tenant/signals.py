from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not instance.is_superuser:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not instance.is_superuser:
        # Ensure the user profile is saved for non-superusers whenever the User instance is saved
        try:
            instance.tenant_profile.save()
        except UserProfile.DoesNotExist:
            # If no profile exists (it may not be created yet), handle it by creating it
            UserProfile.objects.create(user=instance)