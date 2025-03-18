"""
URL patterns for the cases app.
"""

from django.urls import path
from . import views

app_name = 'cases'

urlpatterns = [
    path('', views.case_list, name='list'),
    path('create/', views.case_create, name='create'),
    path('reports/', views.case_reports, name='reports'),
    path('export/csv/', views.export_cases_csv, name='export_csv'),
    path('<str:case_id>/', views.case_detail, name='detail'),
    path('<str:case_id>/edit/', views.case_edit, name='edit'),
    path('<str:case_id>/close/', views.case_close, name='close'),
    path('<str:case_id>/reopen/', views.case_reopen, name='reopen'),
    path('<str:case_id>/assign/', views.assign_case, name='assign'),
    path('<str:case_id>/transaction/<str:transaction_id>/remove/', views.remove_transaction, name='remove_transaction'),
    path('<str:case_id>/note/<int:note_id>/delete/', views.delete_note, name='delete_note'),
    path('<str:case_id>/attachment/<int:attachment_id>/delete/', views.delete_attachment, name='delete_attachment'),
    path('search/transactions/', views.search_transactions, name='search_transactions'),
]