"""
Template tags for rendering notifications.
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def notification_count(context):
    """
    Return the number of unread notifications for the current user.
    
    Usage:
        {% notification_count %}
    """
    request = context['request']
    count = request.session.get('notification_count', 0)
    return count


@register.simple_tag(takes_context=True)
def notification_badge(context):
    """
    Render a notification badge with the number of unread notifications.
    
    Usage:
        {% notification_badge %}
    """
    count = notification_count(context)
    
    if count > 0:
        return mark_safe(f'<span class="badge bg-danger">{count}</span>')
    
    return ''


@register.filter
def message_bootstrap_class(message):
    """
    Convert Django message level to Bootstrap alert class.
    
    Usage:
        <div class="alert alert-{{ message|message_bootstrap_class }}">
            {{ message }}
        </div>
    """
    level_map = {
        'debug': 'info',
        'info': 'info',
        'success': 'success',
        'warning': 'warning',
        'error': 'danger',
    }
    
    return level_map.get(message.level_tag, 'info')


@register.filter
def message_icon_class(message):
    """
    Return the appropriate Font Awesome icon class for a message level.
    
    Usage:
        <i class="fas {{ message|message_icon_class }}"></i>
    """
    level_map = {
        'debug': 'fa-info-circle',
        'info': 'fa-info-circle',
        'success': 'fa-check-circle',
        'warning': 'fa-exclamation-triangle',
        'error': 'fa-times-circle',
    }
    
    return level_map.get(message.level_tag, 'fa-info-circle')


@register.inclusion_tag('notifications/includes/messages.html', takes_context=True)
def render_messages(context):
    """
    Render all messages in the context.
    
    Usage:
        {% render_messages %}
    """
    return {
        'messages': context.get('messages'),
    }