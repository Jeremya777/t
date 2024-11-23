# accounts/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.signals import user_logged_in, user_logged_out

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Crea il profilo se non esiste
    Profile.objects.get_or_create(user=instance)
    instance.profile.save()


@receiver(user_logged_in)
def set_user_online(sender, user, request, **kwargs):
    profile = Profile.objects.get(user=user)
    profile.status = 'online'
    profile.save()

@receiver(user_logged_out)
def set_user_offline(sender, user, request, **kwargs):
    profile = Profile.objects.get(user=user)
    profile.status = 'offline'
    profile.save()
