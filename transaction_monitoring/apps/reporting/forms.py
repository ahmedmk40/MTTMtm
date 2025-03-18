"""
Forms for the reporting app.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from apps.transactions.models import Transaction


class ReportFilterForm(forms.Form):
    """
    Form for filtering reports.
    """
    start_date = forms.DateTimeField(
        label=_('Start Date'),
        required=False,
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'}
        )
    )
    end_date = forms.DateTimeField(
        label=_('End Date'),
        required=False,
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'}
        )
    )
    transaction_type = forms.ChoiceField(
        label=_('Transaction Type'),
        choices=[('', '---')] + list(Transaction.TRANSACTION_TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    channel = forms.ChoiceField(
        label=_('Channel'),
        choices=[('', '---')] + list(Transaction.CHANNEL_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        label=_('Status'),
        choices=[('', '---')] + list(Transaction.TRANSACTION_STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_flagged = forms.NullBooleanField(
        label=_('Flagged'),
        required=False,
        widget=forms.Select(
            attrs={'class': 'form-select'},
            choices=[
                ('', '---'),
                ('true', _('Yes')),
                ('false', _('No')),
            ]
        )
    )