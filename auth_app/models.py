# auth_app/models.py

# 🏆 NEW IMPORT: Import BaseUserManager
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


# ====================================================================
# 1. Custom Manager for Email Authentication (CRITICAL FIX)
# ====================================================================
class CustomUserManager(BaseUserManager):
    """
    Manager that supports creating users and superusers using 'email' 
    as the unique identifier instead of 'username'.
    """
    def create_user(self, email, password=None, **extra_fields): 
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # Call the new create_user method
        return self.create_user(email, password, **extra_fields)


# ====================================================================
# 2. Custom User Model
# ====================================================================
class User(AbstractUser):
    """
    Custom User model extending Django's built-in AbstractUser.
    We set 'email' as the unique field for authentication.
    """
    
    # 🏆 FIX 1: Explicitly disable the username field inherited from AbstractUser
    username = None 
    
    # 2. Define email as the unique required field
    email = models.EmailField(unique=True, blank=False, null=False)
    
    # ⭐ NEW FIELD: User Profile Avatar Image ⭐
    avatar = models.ImageField(
        upload_to='avatars/', # Stores files in media/avatars/
        null=True, 
        blank=True,
        verbose_name='Profile Picture'
    )
    # ⭐ END NEW FIELD ⭐
    
    # 🏆 CRITICAL FIX: Tell Django to use the CustomUserManager
    objects = CustomUserManager() 

    # 🏆 FIX 3: Tell Django to use the email field for logging in
    USERNAME_FIELD = 'email'
    
    # 4. REQUIRED_FIELDS lists fields required for createsuperuser command
    REQUIRED_FIELDS = ['first_name', 'last_name'] 
    
    # Custom related names (necessary when replacing AbstractUser)
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
    
    def __str__(self):
        return self.email