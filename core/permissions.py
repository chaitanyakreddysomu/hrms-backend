# permissions.py
from rest_framework import permissions
from django.contrib.auth.models import Group

class ClientProfilePermission(permissions.BasePermission):
    """
    Custom permission to ensure users can only access data 
    for their assigned client profile
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have access to all profiles
        if request.user.is_superuser:
            return True
            
        # Check if client_id is provided in query params or data
        client_id = request.query_params.get('client_id') or request.data.get('client_id')
        
        if not client_id:
            return False
            
        # Here you would implement logic to check if user has access to this client
        # This could be based on user groups, user profile, etc.
        return True
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
            
        # Check if the object belongs to user's assigned client
        # Implementation depends on your user-client relationship model
        return True

class SupervisorPermission(permissions.BasePermission):
    """Permission for supervisor role"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Check if user is in supervisor group
        return request.user.groups.filter(name='Supervisor').exists()

class HRPermission(permissions.BasePermission):
    """Permission for HR role"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        return request.user.groups.filter(name='HR').exists()

class AdminPermission(permissions.BasePermission):
    """Permission for admin role"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        return request.user.is_superuser or request.user.groups.filter(name='Admin').exists()

class ReadOnlyOrCreatePermission(permissions.BasePermission):
    """
    Permission that allows read operations for all users,
    but only allows create/update/delete for specific roles
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions only for HR and Admin
        return (request.user.is_superuser or 
                request.user.groups.filter(name__in=['HR', 'Admin']).exists())

class DocumentAccessPermission(permissions.BasePermission):
    """Permission for document access"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        return True
    
    def has_object_permission(self, request, view, obj):
        # Users can only access documents of employees in their client profile
        # or if they are admin/HR
        if request.user.is_superuser:
            return True
            
        # Check if document belongs to user's accessible employees
        return True  # Implement based on your user-client relationship


class IsHROnly(permissions.BasePermission):
    """
    Custom permission for HR role ONLY
    Only employees with HR role can access
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        from django.db.models import Q
        from .models import Employee
        
        try:
            employee = Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
            return employee.role == 'HR'
        except Employee.DoesNotExist:
            return False


class IsHROrAdminOrSupervisor(permissions.BasePermission):
    """
    Custom permission for HR, Admin, Supervisor, Manager, Sub-Manager roles
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        from django.db.models import Q
        from .models import Employee
        
        try:
            employee = Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
            return employee.role in ['Admin', 'Manager', 'Sub-Manager', 'HR', 'Supervisor']
        except Employee.DoesNotExist:
            return False