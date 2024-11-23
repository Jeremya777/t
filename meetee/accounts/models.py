from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)

    # Caratteristiche per l'app di incontri
    bio = models.TextField(max_length=500, blank=True)
    interests = models.CharField(max_length=200, blank=True)
    gender = models.CharField(max_length=20, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ], blank=True)
    looking_for = models.CharField(max_length=50, choices=[
        ('friendship', 'Friendship'),
        ('relationship', 'Relationship'),
        ('both', 'Both'),
    ], blank=True)
    location = models.CharField(max_length=100, blank=True)

    # Campo per verificare se il profilo è stato completato
    is_profile_complete = models.BooleanField(default=False)
    status = models.CharField(max_length=10, default='offline')  # 'online' o 'offline'
    is_busy = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.user.username}'s Profile - {self.status}"

    @property
    def username(self):
        return self.user.username

    @property
    def email(self):
        return self.user.email

    def set_password(self, raw_password):
        self.user.set_password(raw_password)
        self.user.save()

    @property
    def password(self):
        # This is just a placeholder to avoid AttributeError
        # Note: NEVER return the actual password; it should be handled securely.
        raise AttributeError("Password is write-only.")
