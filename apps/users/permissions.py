"""
Custom permission classes for role-based access control.
"""
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permission class to allow only admin users.
    Admin users have is_staff=True.
    """
    message = "Only admin users can perform this action."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission class to allow owners of objects or admin users.
    Useful for allowing users to access their own data.
    """
    message = "You don't have permission to access this resource."
    
    def has_object_permission(self, request, view, obj):
        # Admin users can access everything
        if request.user.is_staff:
            return True
        
        # Check if object has 'user' attribute and matches request user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # If object is the user itself
        if hasattr(obj, 'id') and obj == request.user:
            return True
        
        return False


class IsNormalUser(permissions.BasePermission):
    """
    Permission class to allow only normal (non-admin) users.
    Used for endpoints that should only be accessible to regular users.
    """
    message = "This action is only available to normal users."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            not request.user.is_staff
        )