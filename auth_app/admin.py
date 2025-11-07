# auth_app/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Custom Admin interface for the User model.
    Overrides Django's default UserAdmin to use 'email' as the main identifier.
    """
    # Fields to display in the list view
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff')
    
    # Fields to use for searching
    search_fields = ('email', 'username', 'first_name', 'last_name')
    
    # Custom field sets for the detail view
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Ensures 'email' is used as the login field in the admin form
    ordering = ('email',)
    
    # These two lines remove the default username field from display/editing, 
    # but the model still requires it due to AbstractUser inheritance.
    filter_horizontal = ('groups', 'user_permissions',)