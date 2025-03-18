"""
Forms for the cases app.
"""

from django import forms
from django.contrib.auth import get_user_model

from .models import Case, CaseNote, CaseAttachment

User = get_user_model()


class CaseForm(forms.ModelForm):
    """
    Form for creating and updating cases.
    """
    class Meta:
        model = Case
        fields = ['title', 'description', 'priority', 'status', 'resolution', 'assigned_to']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limit assigned_to choices to active users
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
        
        # Make resolution required only if status is 'closed'
        self.fields['resolution'].required = False
        
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class CaseNoteForm(forms.ModelForm):
    """
    Form for adding notes to a case.
    """
    class Meta:
        model = CaseNote
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add a note...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget.attrs['class'] = 'form-control'


class CaseAttachmentForm(forms.ModelForm):
    """
    Form for adding attachments to a case.
    """
    class Meta:
        model = CaseAttachment
        fields = ['file']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs['class'] = 'form-control'
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Set filename, file_type, and file_size
            self.instance.filename = file.name
            self.instance.file_type = file.content_type
            self.instance.file_size = file.size
        return file


class CaseFilterForm(forms.Form):
    """
    Form for filtering cases.
    """
    STATUS_CHOICES = [('', 'All')] + list(Case.STATUS_CHOICES)
    PRIORITY_CHOICES = [('', 'All')] + list(Case.PRIORITY_CHOICES)
    
    case_id = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Case ID'}))
    title = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Title'}))
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    priority = forms.ChoiceField(choices=PRIORITY_CHOICES, required=False)
    assigned_to = forms.ModelChoiceField(queryset=User.objects.filter(is_active=True), required=False)
    created_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    created_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class AddTransactionForm(forms.Form):
    """
    Form for adding transactions to a case.
    """
    transaction_ids = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter transaction IDs, one per line'}),
        help_text='Enter one transaction ID per line'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['transaction_ids'].widget.attrs['class'] = 'form-control'
    
    def clean_transaction_ids(self):
        transaction_ids = self.cleaned_data.get('transaction_ids', '')
        # Split by newline and remove empty lines
        transaction_ids = [tid.strip() for tid in transaction_ids.split('\n') if tid.strip()]
        return transaction_ids