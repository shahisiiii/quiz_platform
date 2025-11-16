"""
Serializers for user registration, login, and profile management.
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Handles password validation and hashing.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    is_admin = serializers.BooleanField(
        write_only=True,
        required=False,
        default=False,
        help_text="Set to true to create admin user"
    )
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password2', 
                  'first_name', 'last_name', 'is_admin')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs
    
    def validate_email(self, value):
        """Ensure email is unique"""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Email already exists.")
        return value.lower()
    
    def validate_username(self, value):
        value = value.strip().lower()

        if '@' in value:
            raise serializers.ValidationError("Username cannot contain '@'.")

        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")

        return value
    
    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password2')
        is_admin = validated_data.pop('is_admin', False)
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_staff=is_admin,  # Set admin role
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile display.
    """
    role = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 
                  'last_name', 'role', 'created_at')
        read_only_fields = ('id', 'created_at')
    
    def get_role(self, obj):
        """Return user role as string"""
        return 'admin' if obj.is_staff else 'user'


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Accepts username or email with password.
    """
    username_or_email = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )