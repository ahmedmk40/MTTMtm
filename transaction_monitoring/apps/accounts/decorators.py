"""
Decorators for the accounts app.
"""

from functools import wraps
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse


def role_required(roles):
    """
    Decorator for views that checks if the user has the required role.
    
    Args:
        roles: A string or list of strings representing the required roles.
    
    Returns:
        A decorator function.
    """
    if isinstance(roles, str):
        roles = [roles]
    
    def check_role(user):
        if not user.is_authenticated:
            return False
        
        # Check if the user has any of the required roles
        return user.role in roles
    
    return user_passes_test(check_role, login_url='accounts:login')


def permission_required(perm):
    """
    Decorator for views that checks if the user has the required permission.
    
    Args:
        perm: A string representing the required permission.
    
    Returns:
        A decorator function.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"{reverse('accounts:login')}?next={request.path}")
            
            if not request.user.has_perm(perm):
                raise PermissionDenied("You don't have permission to access this page.")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def compliance_officer_required(view_func):
    """
    Decorator for views that checks if the user is a compliance officer.
    """
    return role_required('compliance_officer')(view_func)


def fraud_analyst_required(view_func):
    """
    Decorator for views that checks if the user is a fraud analyst.
    """
    return role_required('fraud_analyst')(view_func)


def risk_manager_required(view_func):
    """
    Decorator for views that checks if the user is a risk manager.
    """
    return role_required('risk_manager')(view_func)


def system_admin_required(view_func):
    """
    Decorator for views that checks if the user is a system administrator.
    """
    return role_required('system_admin')(view_func)


def data_analyst_required(view_func):
    """
    Decorator for views that checks if the user is a data analyst.
    """
    return role_required('data_analyst')(view_func)


def executive_required(view_func):
    """
    Decorator for views that checks if the user is an executive.
    """
    return role_required('executive')(view_func)