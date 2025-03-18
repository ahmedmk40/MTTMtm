"""
Test views for the transactions app.
"""

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required


@login_required
def test_view(request):
    """
    Test view.
    """
    return HttpResponse("Test view works!")