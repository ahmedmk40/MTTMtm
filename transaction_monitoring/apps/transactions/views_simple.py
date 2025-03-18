"""
Simple views for the transactions app.
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


@login_required
def simple_network(request):
    """
    Simple network view.
    """
    return JsonResponse({
        'message': 'Simple network view works!',
        'status': 'success'
    })