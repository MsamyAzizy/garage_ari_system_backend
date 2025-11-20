# auth_app/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
# 🚀 NEW IMPORT: Import reverse for building URLs (though not strictly needed with get_full_url, good practice)
from django.urls import reverse 

User = get_user_model() # Gets the 'auth_app.User' model defined in settings.py

class RegistrationSerializer(serializers.ModelSerializer):
    # Add password confirmation field for frontend validation
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        # Fields expected from the frontend's register function
        fields = ['email', 'first_name', 'last_name', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        # 1. Basic password match validation
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # 2. Check if email already exists
        if User.objects.filter(email=data['email']).exists():
            # Ensure case-insensitive check if necessary, but default unique=True handles exact match
            raise serializers.ValidationError({"email": "This email address is already in use."})
            
        return data

    def create(self, validated_data):
        # The password2 field must be removed before creating the user object.
        validated_data.pop('password2')
        
        # The CustomUserManager now correctly uses 'email' as the first positional argument.
        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user


# 🚀 NEW: Serializer for returning/updating user details (Djoser's 'current_user')
class CustomUserSerializer(serializers.ModelSerializer): 
    """
    Serializes and handles updates for the user profile (/users/me/).
    """
    # ⭐ CRITICAL FIX: Replace the avatar ImageField with a SerializerMethodField
    # to ensure a full, absolute URL is returned to the frontend.
    avatar = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        # IMPORTANT: Use the SerializerMethodField 'avatar' instead of the model field
        fields = ['id', 'email', 'first_name', 'last_name', 'avatar'] 
        read_only_fields = ['id', 'email'] 
        
    # ⭐ CRITICAL METHOD: Generates the absolute URL for the avatar
    def get_avatar(self, obj):
        # Check if an avatar file actually exists
        if not obj.avatar:
            return None
            
        # 1. Get the request object from the serializer context
        request = self.context.get('request')
        
        # 2. Use the request object to build the full, absolute URI
        # This will prepend the scheme (http/https) and domain (127.0.0.1:8000)
        # to the relative URL provided by obj.avatar.url (/media/avatars/...)
        if request:
            return request.build_absolute_uri(obj.avatar.url)
        
        # Fallback to relative URL if request object is missing (shouldn't happen with DRF views)
        return obj.avatar.url
        
    # CRITICAL FIX: Add the update method to handle PUT/PATCH requests from Djoser
    # This is necessary because we overrode the avatar field above, but the update
    # logic itself remains mostly the same for handling file uploads.
    def update(self, instance, validated_data):
        # The DRF handles incoming file data for the model instance field,
        # even though we are using a SerializerMethodField for output.
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        instance.save()
        return instance