# auth_app/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model

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
            raise serializers.ValidationError({"email": "This email address is already in use."})
            
        return data

    def create(self, validated_data):
        # The password2 field must be removed before creating the user object.
        validated_data.pop('password2')
        
        # Create the user using the validated data
        user = User.objects.create_user(
            # FIX: Pass the email value as the missing 'username' argument
            username=validated_data['email'], 
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user


# 🚀 NEW: Serializer for returning user details after login or on reload
class UserSerializer(serializers.ModelSerializer):
    """
    Serializes the user model fields needed by the frontend for display (e.g., in the navbar).
    """
    class Meta:
        model = User
        # These are the fields your frontend will receive when it calls /api/auth/user/
        fields = ['email', 'first_name', 'last_name']