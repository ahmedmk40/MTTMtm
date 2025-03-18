"""
Custom template filters for the accounts app.
"""

from django import template

register = template.Library()

@register.filter
def get_attr(obj, attr):
    """
    Gets an attribute of an object dynamically from a string name.
    
    Usage: {{ form|get_attr:field_name }}
    """
    if hasattr(obj, attr):
        return getattr(obj, attr)
    elif hasattr(obj, 'get'):
        return obj.get(attr)
    else:
        return None