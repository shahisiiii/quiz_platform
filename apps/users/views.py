"""
Views for user authentication and profile management.
Uses JWT tokens for authentication.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.cache import cache

from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    LoginSerializer
)
from .permissions import IsAdminUser


class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet for user authentication operations.
    Handles registration and login without requiring authentication.
    """
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        """
        Register a new user (admin or normal user).
        
        Body:
        {
            "username": "string",
            "email": "string",
            "password": "string",
            "password2": "string",
            "first_name": "string" (optional),
            "last_name": "string" (optional),
            "is_admin": boolean (optional, default: false)
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens for the new user
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'User registered successfully',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """
        Login user with username/email and password.
        Returns JWT access and refresh tokens.
        
        Body:
        {
            "username_or_email": "string",
            "password": "string"
        }
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username_or_email = serializer.validated_data['username_or_email']
        password = serializer.validated_data['password']
        
        # Try to find user by username or email
        user = None
        if '@' in username_or_email:
            # It's an email
            try:
                user_obj = User.objects.get(email=username_or_email.lower())
                user = authenticate(
                    request,
                    username=user_obj.username,
                    password=password
                )
            except User.DoesNotExist:
                pass
        else:
            # It's a username
            user = authenticate(
                request,
                username=username_or_email,
                password=password
            )
        
        if user is None:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'error': 'User account is disabled'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user management.
    - Normal users can only view their own profile
    - Admin users can view all users
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter queryset based on user role.
        Normal users only see themselves, admins see everyone.
        """
        user = self.request.user
        if user.is_staff:
            # Admin can see all users
            return User.objects.all()
        else:
            # Normal users only see themselves
            return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'], url_path='me')
    def current_user(self, request):
        """
        Get current authenticated user's profile.
        Cached for 5 minutes to reduce database queries.
        """
        cache_key = f'user_profile_{request.user.id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        serializer = self.get_serializer(request.user)
        cache.set(cache_key, serializer.data, timeout=300)  # 5 minutes
        
        return Response(serializer.data)