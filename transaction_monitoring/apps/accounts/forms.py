"""
Forms for the accounts app.
"""

from django import forms
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from .models import User


class ProfileForm(forms.ModelForm):
    """
    Form for editing user profile.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'profile_picture', 'bio', 'phone_number', 'department']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
        }


class SecuritySettingsForm(forms.ModelForm):
    """
    Form for security settings.
    """
    class Meta:
        model = User
        fields = ['two_factor_enabled']
        widgets = {
            'two_factor_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class NotificationSettingsForm(forms.ModelForm):
    """
    Form for notification settings.
    """
    class Meta:
        model = User
        fields = ['email_notifications', 'sms_notifications']
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserCreateForm(UserCreationForm):
    """
    Form for creating a new user.
    """
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    is_active = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    is_staff = forms.BooleanField(
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'role', 'department', 'phone_number',
            'is_active', 'is_staff'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class UserEditForm(forms.ModelForm):
    """
    Form for editing a user.
    """
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    is_staff = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'role', 'department', 'phone_number',
            'is_active', 'is_staff'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class UserPasswordResetForm(SetPasswordForm):
    """
    Form for resetting a user's password.
    """
    class Meta:
        model = User
        fields = ['new_password1', 'new_password2']


class RoleForm(forms.ModelForm):
    """
    Form for creating and editing roles (groups).
    """
    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    class Meta:
        model = Group
        fields = ['name']


class RolePermissionsForm(forms.Form):
    """
    Form for managing role permissions.
    """
    def __init__(self, *args, **kwargs):
        content_types = kwargs.pop('content_types', None)
        super().__init__(*args, **kwargs)
        
        if content_types:
            # Group permissions by app and model
            for ct in content_types:
                app_label = ct.app_label
                model_name = ct.model
                
                # Get all permissions for this content type
                permissions = Permission.objects.filter(content_type=ct)
                
                for permission in permissions:
                    field_name = f"perm_{permission.id}"
                    self.fields[field_name] = forms.BooleanField(
                        label=permission.name,
                        required=False,
                        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                    )
                    
                    # Store content type info in the field's widget attrs for template rendering
                    self.fields[field_name].widget.attrs.update({
                        'data_app': app_label,
                        'data_model': model_name,
                        'data_codename': permission.codename,
                    })


class UserFilterForm(forms.Form):
    """
    Form for filtering users.
    """
    role = forms.ChoiceField(
        choices=[('', 'All Roles')] + list(User.ROLE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_active = forms.ChoiceField(
        choices=[
            ('', 'All Status'),
            ('true', 'Active'),
            ('false', 'Inactive')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by username, name, or email'
        })
    )