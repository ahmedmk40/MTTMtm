"""
Context processors for the accounts app.
"""

def user_roles(request):
    """
    Add user role information to the template context.
    
    This context processor adds the following variables to the template context:
    - is_compliance_officer: True if the user is a compliance officer
    - is_fraud_analyst: True if the user is a fraud analyst
    - is_risk_manager: True if the user is a risk manager
    - is_system_admin: True if the user is a system administrator
    - is_data_analyst: True if the user is a data analyst
    - is_executive: True if the user is an executive
    - user_role: The user's role
    - user_role_display: The display name of the user's role
    """
    context = {
        'is_compliance_officer': False,
        'is_fraud_analyst': False,
        'is_risk_manager': False,
        'is_system_admin': False,
        'is_data_analyst': False,
        'is_executive': False,
        'user_role': None,
        'user_role_display': None,
    }
    
    if request.user.is_authenticated:
        # Add role information
        context['is_compliance_officer'] = request.user.is_compliance_officer()
        context['is_fraud_analyst'] = request.user.is_fraud_analyst()
        context['is_risk_manager'] = request.user.is_risk_manager()
        context['is_system_admin'] = request.user.is_system_admin()
        context['is_data_analyst'] = request.user.is_data_analyst()
        context['is_executive'] = request.user.is_executive()
        
        # Add role name and display name
        context['user_role'] = request.user.role
        
        if request.user.role:
            role_choices_dict = dict(request.user.ROLE_CHOICES)
            context['user_role_display'] = role_choices_dict.get(request.user.role)
    
    return context