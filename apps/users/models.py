"""
User models with custom User model extending Django's AbstractUser.
Supports admin and normal user roles.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model with role-based access.
    - is_staff field determines if user is admin (inherited from AbstractUser)
    - Regular users have is_staff=False
    """
    email = models.EmailField(unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email'], name='users_email_idx'),
            models.Index(fields=['username'], name='users_username_idx'),
            models.Index(fields=['is_staff'], name='users_is_staff_idx'),
            models.Index(fields=['-created_at'], name='users_created_at_idx'),
        ]
    
    def __str__(self):
        return f"{self.username} ({'Admin' if self.is_staff else 'User'})"
    
    @property
    def is_admin(self):
        """Helper property to check if user is admin"""
        return self.is_staff