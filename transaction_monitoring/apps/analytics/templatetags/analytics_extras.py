"""
Custom template tags and filters for the analytics app.
"""

from django import template
import random

register = template.Library()


@register.filter
def random_color(value):
    """Return a random color based on the value."""
    colors = [
        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
        '#858796', '#5a5c69', '#2e59d9', '#17a673', '#2c9faf'
    ]
    # Use the value as a seed to get consistent colors for the same value
    random.seed(value)
    return random.choice(colors)


@register.filter
def random_rgb(value):
    """Return random RGB values based on the value."""
    # Use the value as a seed to get consistent colors for the same value
    random.seed(value)
    r = random.randint(50, 220)
    g = random.randint(50, 220)
    b = random.randint(50, 220)
    return f"{r}, {g}, {b}"


@register.filter
def random_rgb_dark(value):
    """Return darker random RGB values based on the value."""
    # Use the value as a seed to get consistent colors for the same value
    random.seed(value)
    r = random.randint(30, 180)
    g = random.randint(30, 180)
    b = random.randint(30, 180)
    return f"{r}, {g}, {b}"