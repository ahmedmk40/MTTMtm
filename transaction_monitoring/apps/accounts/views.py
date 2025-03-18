"""
Views for the accounts app.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from .models import User
from .forms import (
    ProfileForm, SecuritySettingsForm, NotificationSettingsForm,
    UserCreateForm, UserEditForm, UserPasswordResetForm,
    RoleForm, RolePermissionsForm, UserFilterForm
)
from .decorators import system_admin_required


@login_required
def profile(request):
    """
    View for user profile.
    """
    return render(request, 'accounts/profile.html')


@login_required
def edit_profile(request):
    """
    View for editing user profile.
    """
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def settings(request):
    """
    View for user settings.
    """
    return render(request, 'accounts/settings.html')


@login_required
def security_settings(request):
    """
    View for security settings.
    """
    if request.method == 'POST':
        form = SecuritySettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Security settings updated successfully.')
            return redirect('accounts:settings')
    else:
        form = SecuritySettingsForm(instance=request.user)
    
    return render(request, 'accounts/security_settings.html', {'form': form})


@login_required
def notification_settings(request):
    """
    View for notification settings.
    """
    if request.method == 'POST':
        form = NotificationSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notification settings updated successfully.')
            return redirect('accounts:settings')
    else:
        form = NotificationSettingsForm(instance=request.user)
    
    return render(request, 'accounts/notification_settings.html', {'form': form})


# User Management Views
@login_required
@system_admin_required
def user_list(request):
    """
    View for listing users.
    """
    # Get filter parameters
    filter_form = UserFilterForm(request.GET)
    role = request.GET.get('role', '')
    is_active = request.GET.get('is_active', '')
    search = request.GET.get('search', '')
    
    # Start with all users
    users = User.objects.all().order_by('username')
    
    # Apply filters
    if role:
        users = users.filter(role=role)
    
    if is_active:
        is_active_bool = is_active.lower() == 'true'
        users = users.filter(is_active=is_active_bool)
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Paginate the results
    paginator = Paginator(users, 20)  # 20 users per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'filter_role': role,
        'filter_is_active': is_active,
        'search': search,
    }
    
    return render(request, 'accounts/user_list.html', context)


@login_required
@system_admin_required
def user_create(request):
    """
    View for creating a new user.
    """
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.created_by = request.user.username
            user.save()
            
            # Update role groups
            user.update_role_groups()
            
            messages.success(request, f'User {user.username} created successfully.')
            return redirect('accounts:user_list')
    else:
        form = UserCreateForm()
    
    return render(request, 'accounts/user_create.html', {'form': form})


@login_required
@system_admin_required
def user_edit(request, user_id):
    """
    View for editing a user.
    """
    user = get_object_or_404(User, id=user_id)
    
    # Prevent editing superusers unless you are a superuser
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to edit superusers.')
        return redirect('accounts:user_list')
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            
            # Update role groups
            user.update_role_groups()
            
            messages.success(request, f'User {user.username} updated successfully.')
            return redirect('accounts:user_list')
    else:
        form = UserEditForm(instance=user)
    
    return render(request, 'accounts/user_edit.html', {'form': form, 'user_obj': user})


@login_required
@system_admin_required
def user_delete(request, user_id):
    """
    View for deleting a user.
    """
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deleting superusers unless you are a superuser
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to delete superusers.')
        return redirect('accounts:user_list')
    
    # Prevent self-deletion
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('accounts:user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully.')
        return redirect('accounts:user_list')
    
    return render(request, 'accounts/user_delete.html', {'user_obj': user})


@login_required
@system_admin_required
def user_reset_password(request, user_id):
    """
    View for resetting a user's password.
    """
    user = get_object_or_404(User, id=user_id)
    
    # Prevent resetting superuser passwords unless you are a superuser
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to reset superuser passwords.')
        return redirect('accounts:user_list')
    
    if request.method == 'POST':
        form = UserPasswordResetForm(user, request.POST)
        if form.is_valid():
            form.save()
            user.last_password_change = timezone.now()
            user.save()
            messages.success(request, f'Password for {user.username} reset successfully.')
            return redirect('accounts:user_list')
    else:
        form = UserPasswordResetForm(user)
    
    return render(request, 'accounts/user_reset_password.html', {'form': form, 'user_obj': user})


@login_required
@system_admin_required
def user_activate(request, user_id):
    """
    View for activating a user.
    """
    user = get_object_or_404(User, id=user_id)
    
    if not user.is_active:
        user.is_active = True
        user.save()
        messages.success(request, f'User {user.username} activated successfully.')
    
    return redirect('accounts:user_list')


@login_required
@system_admin_required
def user_deactivate(request, user_id):
    """
    View for deactivating a user.
    """
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deactivating superusers unless you are a superuser
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to deactivate superusers.')
        return redirect('accounts:user_list')
    
    # Prevent self-deactivation
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('accounts:user_list')
    
    if user.is_active:
        user.is_active = False
        user.save()
        messages.success(request, f'User {user.username} deactivated successfully.')
    
    return redirect('accounts:user_list')


# Role Management Views
@login_required
@system_admin_required
def role_list(request):
    """
    View for listing roles.
    """
    # Get all groups (roles)
    roles = Group.objects.all().order_by('name')
    
    # Count users in each role
    for role in roles:
        role.user_count = User.objects.filter(groups=role).count()
    
    return render(request, 'accounts/role_list.html', {'roles': roles})


@login_required
@system_admin_required
def role_create(request):
    """
    View for creating a new role.
    """
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            messages.success(request, f'Role {role.name} created successfully.')
            return redirect('accounts:role_permissions', role_id=role.id)
    else:
        form = RoleForm()
    
    return render(request, 'accounts/role_create.html', {'form': form})


@login_required
@system_admin_required
def role_edit(request, role_id):
    """
    View for editing a role.
    """
    role = get_object_or_404(Group, id=role_id)
    
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            role = form.save()
            messages.success(request, f'Role {role.name} updated successfully.')
            return redirect('accounts:role_list')
    else:
        form = RoleForm(instance=role)
    
    return render(request, 'accounts/role_edit.html', {'form': form, 'role': role})


@login_required
@system_admin_required
def role_delete(request, role_id):
    """
    View for deleting a role.
    """
    role = get_object_or_404(Group, id=role_id)
    
    # Check if the role is being used by any users
    user_count = User.objects.filter(groups=role).count()
    
    if request.method == 'POST':
        if user_count > 0:
            messages.error(request, f'Cannot delete role {role.name} because it is assigned to {user_count} users.')
            return redirect('accounts:role_list')
        
        role_name = role.name
        role.delete()
        messages.success(request, f'Role {role_name} deleted successfully.')
        return redirect('accounts:role_list')
    
    return render(request, 'accounts/role_delete.html', {'role': role, 'user_count': user_count})


@login_required
@system_admin_required
def role_permissions(request, role_id):
    """
    View for managing role permissions.
    """
    role = get_object_or_404(Group, id=role_id)
    
    # Get all content types
    content_types = ContentType.objects.all().order_by('app_label', 'model')
    
    # Get current permissions for this role
    current_permissions = role.permissions.all()
    current_permission_ids = [p.id for p in current_permissions]
    
    if request.method == 'POST':
        form = RolePermissionsForm(request.POST, content_types=content_types)
        if form.is_valid():
            # Clear existing permissions
            role.permissions.clear()
            
            # Add selected permissions
            for field_name, value in form.cleaned_data.items():
                if field_name.startswith('perm_') and value:
                    permission_id = int(field_name.replace('perm_', ''))
                    permission = Permission.objects.get(id=permission_id)
                    role.permissions.add(permission)
            
            messages.success(request, f'Permissions for role {role.name} updated successfully.')
            return redirect('accounts:role_list')
    else:
        # Initialize form with current permissions
        initial_data = {f'perm_{p_id}': True for p_id in current_permission_ids}
        form = RolePermissionsForm(initial=initial_data, content_types=content_types)
    
    # Group content types by app for better organization in the template
    grouped_content_types = {}
    for ct in content_types:
        app_label = ct.app_label
        if app_label not in grouped_content_types:
            grouped_content_types[app_label] = []
        grouped_content_types[app_label].append(ct)
    
    context = {
        'role': role,
        'form': form,
        'grouped_content_types': grouped_content_types,
        'current_permission_ids': current_permission_ids,
    }
    
    return render(request, 'accounts/role_permissions.html', context)