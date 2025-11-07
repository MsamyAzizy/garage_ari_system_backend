# auth_app/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User model extending Django's built-in AbstractUser.
    We set 'email' as the unique field for authentication.
    """
    
    email = models.EmailField(unique=True, blank=False, null=False)
    
    # Custom related names to avoid clash with default User model relations
    # This is required because we set AUTH_USER_MODEL in settings.py
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='ari_user_set',
        blank=True,
        help_text=('The groups this user belongs to.'),
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='ari_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    # Tell Django to use the email field for logging in
    USERNAME_FIELD = 'email'
    # Keep username required by Django, but it won't be used for login validation
    REQUIRED_FIELDS = ['username'] 

    def __str__(self):
        return self.email