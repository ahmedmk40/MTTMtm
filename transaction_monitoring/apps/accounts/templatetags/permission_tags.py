"""
Template tags for checking permissions.
"""

from django import template
from django.contrib.auth.models import Group

register = template.Library()


@register.filter
def has_role(user, role):
    """
    Check if a user has a specific role.
    
    Usage:
        {% if user|has_role:'compliance_officer' %}
            <!-- Content for compliance officers -->
        {% endif %}
    """
    if not user.is_authenticated:
        return False
    
    return user.role == role


@register.filter
def has_group(user, group_name):
    """
    Check if a user belongs to a specific group.
    
    Usage:
        {% if user|has_group:'Compliance Officer' %}
            <!-- Content for compliance officers -->
        {% endif %}
    """
    if not user.is_authenticated:
        return False
    
    try:
        group = Group.objects.get(name=group_name)
        return group in user.groups.all()
    except Group.DoesNotExist:
        return False


@register.filter
def has_perm(user, permission):
    """
    Check if a user has a specific permission.
    
    Usage:
        {% if user|has_perm:'transactions.view_transaction' %}
            <!-- Content for users with permission to view transactions -->
        {% endif %}
    """
    if not user.is_authenticated:
        return False
    
    return user.has_perm(permission)


@register.simple_tag
def role_display(user):
    """
    Return the display name of a user's role.
    
    Usage:
        {% role_display user %}
    """
    if not user.is_authenticated or not user.role:
        return ''
    
    role_choices_dict = dict(user.ROLE_CHOICES)
    return role_choices_dict.get(user.role, '')


@register.simple_tag(takes_context=True)
def can_access_section(context, section_name):
    """
    Check if the current user can access a specific section.
    
    Usage:
        {% can_access_section 'transactions' as can_access %}
        {% if can_access %}
            <!-- Content for users who can access the transactions section -->
        {% endif %}
    """
    user = context['user']
    
    if not user.is_authenticated:
        return False
    
    # Define section access rules
    section_access = {
        'transactions': lambda u: u.has_perm('transactions.view_transaction'),
        'fraud_cases': lambda u: u.has_perm('fraud_engine.view_fraudcase'),
        'aml_alerts': lambda u: u.has_perm('aml.view_amlalert'),
        'reports': lambda u: u.has_perm('reporting.view_report'),
        'rules': lambda u: u.has_perm('rule_engine.view_rule'),
        'users': lambda u: u.is_staff or u.is_superuser,
        'settings': lambda u: u.is_staff or u.is_superuser,
    }
    
    # Check if the section exists in the access rules
    if section_name not in section_access:
        return False
    
    # Check if the user has access to the section
    return section_access[section_name](user)


@register.filter
def getattr(obj, attr):
    """
    Get an attribute of an object dynamically.
    
    Usage:
        {{ form|getattr:field_name }}
    """
    return getattr(obj, attr)