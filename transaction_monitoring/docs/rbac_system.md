# Role-Based Access Control (RBAC) System

This document describes the role-based access control system implemented in the Transaction Monitoring and Fraud Detection System.

## Overview

The RBAC system is designed to control access to different parts of the application based on user roles. Each user is assigned a role, which determines what actions they can perform and what data they can access.

## User Roles

The system defines the following user roles:

1. **Compliance Officer**
   - Responsible for reviewing flagged transactions and alerts
   - Investigates suspicious activities
   - Files regulatory reports (SARs, CTRs)
   - Documents case management and resolution

2. **Fraud Analyst**
   - Monitors real-time transaction alerts
   - Investigates potential fraud cases
   - Configures and tunes fraud detection rules
   - Analyzes fraud patterns and trends

3. **Risk Manager**
   - Defines risk policies and thresholds
   - Reviews and approves rule changes
   - Monitors overall risk metrics
   - Generates risk reports for leadership

4. **System Administrator**
   - Manages user access
   - Configures system settings
   - Monitors system performance
   - Manages security settings

5. **Data Analyst**
   - Analyzes fraud and transaction data
   - Creates and refines ML models
   - Builds custom reports
   - Performs data exploration

6. **Executive**
   - Reviews high-level metrics and KPIs
   - Monitors system effectiveness
   - Makes strategic decisions

## Permissions

Permissions are assigned to roles based on the principle of least privilege. Each role has only the permissions necessary to perform its functions.

### Compliance Officer Permissions

- View transactions
- View and manage AML alerts
- Create and manage SARs (Suspicious Activity Reports)
- View customer profiles
- Access compliance dashboard

### Fraud Analyst Permissions

- View transactions
- View and manage fraud cases
- Configure fraud detection rules
- Access fraud analysis dashboard
- View fraud patterns and trends

### Risk Manager Permissions

- View transactions
- View fraud cases
- View AML alerts
- View SARs
- Access risk dashboard
- Configure risk thresholds

### System Administrator Permissions

- Manage users and roles
- Configure system settings
- View system logs
- Manage integrations
- Access admin dashboard

### Data Analyst Permissions

- View transactions
- Access data exploration tools
- Create and manage reports
- Train and evaluate ML models

### Executive Permissions

- View high-level dashboards
- Access executive reports
- View summary metrics

## Implementation

The RBAC system is implemented using Django's built-in authentication and permission system, with custom extensions for role-based access control.

### User Model

The custom User model includes a `role` field that stores the user's role:

```python
class User(AbstractUser):
    ROLE_CHOICES = (
        ('compliance_officer', _('Compliance Officer')),
        ('fraud_analyst', _('Fraud Analyst')),
        ('risk_manager', _('Risk Manager')),
        ('system_admin', _('System Administrator')),
        ('data_analyst', _('Data Analyst')),
        ('executive', _('Executive')),
    )
    
    role = models.CharField(_('Role'), max_length=20, choices=ROLE_CHOICES, null=True, blank=True)
    # ... other fields ...
```

### Permission Setup

Permissions are set up using Django's Group and Permission models. Each role is associated with a Group, and permissions are assigned to these groups.

The `setup_role_permissions()` function in `apps/accounts/permissions.py` creates the necessary groups and assigns permissions to them.

### Permission Checking

Permissions can be checked in several ways:

1. **In views using decorators**:

```python
from apps.accounts.decorators import role_required, permission_required

@role_required('compliance_officer')
def view_aml_alerts(request):
    # Only compliance officers can access this view
    # ...

@permission_required('aml.view_amlalert')
def view_alert_details(request, alert_id):
    # Only users with the 'aml.view_amlalert' permission can access this view
    # ...
```

2. **In templates using template tags**:

```html
{% load permission_tags %}

{% if user|has_role:'compliance_officer' %}
    <!-- Content for compliance officers -->
{% endif %}

{% if user|has_perm:'aml.view_amlalert' %}
    <!-- Content for users with permission to view AML alerts -->
{% endif %}
```

3. **In REST API views using DRF permissions**:

```python
from apps.accounts.permissions import IsComplianceOfficer, CanViewTransactions

class TransactionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanViewTransactions]
    # ...

class AMLAlertViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsComplianceOfficer]
    # ...
```

## Role-Based UI

The UI adapts based on the user's role:

1. **Navigation**: The sidebar menu shows only the items the user has permission to access.
2. **Dashboards**: Each role has a customized dashboard showing relevant information.
3. **Actions**: UI elements for actions (buttons, links, etc.) are only shown if the user has permission to perform the action.

## Managing Roles and Permissions

Roles and permissions can be managed through:

1. **Django Admin**: Administrators can assign roles and permissions through the Django admin interface.
2. **Management Command**: The `setup_permissions` management command can be used to set up or update role permissions.

```bash
python manage.py setup_permissions
```

3. **User Management UI**: A custom user management interface allows administrators to assign roles to users.

## Best Practices

1. **Principle of Least Privilege**: Users should only have the permissions necessary to perform their job functions.
2. **Role Separation**: Ensure proper separation of duties between roles.
3. **Regular Review**: Regularly review and audit user roles and permissions.
4. **Permission Granularity**: Define permissions at an appropriate level of granularity.
5. **Default Deny**: By default, deny access unless explicitly granted.

## Testing

The RBAC system includes comprehensive tests to ensure that permissions are correctly enforced:

1. **Unit Tests**: Test individual permission checks and role assignments.
2. **Integration Tests**: Test that views and API endpoints correctly enforce permissions.
3. **UI Tests**: Test that the UI adapts correctly based on the user's role.