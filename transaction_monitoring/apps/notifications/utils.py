"""
Utility functions for the notifications app.
"""

from django.contrib import messages
from django.utils.safestring import mark_safe


def add_success_message(request, message, title=None, dismissible=True, timeout=None):
    """
    Add a success message to the request.
    
    Args:
        request: The HTTP request object.
        message: The message text.
        title: Optional title for the message.
        dismissible: Whether the message can be dismissed by the user.
        timeout: Optional timeout in milliseconds after which the message will be automatically dismissed.
    """
    _add_message(request, messages.SUCCESS, message, title, dismissible, timeout)


def add_info_message(request, message, title=None, dismissible=True, timeout=None):
    """
    Add an info message to the request.
    
    Args:
        request: The HTTP request object.
        message: The message text.
        title: Optional title for the message.
        dismissible: Whether the message can be dismissed by the user.
        timeout: Optional timeout in milliseconds after which the message will be automatically dismissed.
    """
    _add_message(request, messages.INFO, message, title, dismissible, timeout)


def add_warning_message(request, message, title=None, dismissible=True, timeout=None):
    """
    Add a warning message to the request.
    
    Args:
        request: The HTTP request object.
        message: The message text.
        title: Optional title for the message.
        dismissible: Whether the message can be dismissed by the user.
        timeout: Optional timeout in milliseconds after which the message will be automatically dismissed.
    """
    _add_message(request, messages.WARNING, message, title, dismissible, timeout)


def add_error_message(request, message, title=None, dismissible=True, timeout=None):
    """
    Add an error message to the request.
    
    Args:
        request: The HTTP request object.
        message: The message text.
        title: Optional title for the message.
        dismissible: Whether the message can be dismissed by the user.
        timeout: Optional timeout in milliseconds after which the message will be automatically dismissed.
    """
    _add_message(request, messages.ERROR, message, title, dismissible, timeout)


def _add_message(request, level, message, title=None, dismissible=True, timeout=None):
    """
    Add a message to the request with the given level.
    
    Args:
        request: The HTTP request object.
        level: The message level (e.g., messages.SUCCESS).
        message: The message text.
        title: Optional title for the message.
        dismissible: Whether the message can be dismissed by the user.
        timeout: Optional timeout in milliseconds after which the message will be automatically dismissed.
    """
    # Create the message HTML
    message_html = ""
    
    if title:
        message_html += f"<strong>{title}</strong> "
    
    message_html += message
    
    # Add the message to the request
    message_obj = messages.add_message(request, level, mark_safe(message_html))
    
    # Add extra attributes to the message
    message_obj.dismissible = dismissible
    message_obj.timeout = timeout


def add_notification_badge(request, count):
    """
    Add a notification badge count to the request.
    
    Args:
        request: The HTTP request object.
        count: The number of notifications.
    """
    request.session['notification_count'] = count