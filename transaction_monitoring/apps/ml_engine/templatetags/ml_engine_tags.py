"""
Custom template tags and filters for ML Engine app.
"""

from django import template

register = template.Library()


@register.filter
def multiply(value, arg):
    """
    Multiply the value by the argument.
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def split_string(value, delimiter=','):
    """
    Split a string by the given delimiter.
    """
    if not value or not isinstance(value, str):
        return []
    return value.split(delimiter)


@register.filter
def abs(value):
    """
    Return the absolute value.
    """
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0