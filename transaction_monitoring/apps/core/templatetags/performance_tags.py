"""
Template tags for performance optimization.
"""

import time
from django import template
from django.utils.safestring import mark_safe
from django.conf import settings

register = template.Library()


@register.simple_tag
def render_time():
    """
    Return the current timestamp for measuring template rendering time.
    
    Usage:
        {% load performance_tags %}
        {% render_time as start_time %}
        <!-- Content to measure -->
        {% render_time as end_time %}
        <!-- Render time: {{ end_time|subtract:start_time }} ms -->
    """
    return time.time() * 1000  # Return time in milliseconds


@register.filter
def subtract(value, arg):
    """
    Subtract the arg from the value.
    
    Usage:
        {{ value|subtract:arg }}
    """
    return value - arg


@register.simple_tag
def debug_info():
    """
    Return debug information if DEBUG is True.
    
    Usage:
        {% load performance_tags %}
        {% debug_info %}
    """
    if not settings.DEBUG:
        return ''
    
    html = """
    <div class="debug-info" style="position: fixed; bottom: 0; right: 0; background: #f8f9fa; 
                                  border: 1px solid #dee2e6; padding: 10px; font-size: 12px; 
                                  z-index: 9999; max-width: 300px;">
        <h6>Debug Info</h6>
        <p>Django Debug Toolbar is enabled. Click the DjDT button in the corner to view detailed debug information.</p>
        <p>Performance monitoring is active. Check the logs for detailed performance metrics.</p>
    </div>
    """
    return mark_safe(html)


@register.simple_tag(takes_context=True)
def query_count(context):
    """
    Return the number of database queries for the current request.
    
    Usage:
        {% load performance_tags %}
        {% query_count %}
    """
    if not settings.DEBUG:
        return ''
    
    try:
        from django.db import connection
        query_count = len(connection.queries)
        
        if query_count > 50:
            color = 'danger'
        elif query_count > 20:
            color = 'warning'
        else:
            color = 'success'
        
        html = f"""
        <span class="badge bg-{color}">
            {query_count} queries
        </span>
        """
        return mark_safe(html)
    except Exception:
        return ''


@register.filter
def format_sql(sql):
    """
    Format SQL query for better readability.
    
    Usage:
        {{ sql_query|format_sql }}
    """
    if not sql:
        return ''
    
    # Replace multiple spaces with a single space
    sql = ' '.join(sql.split())
    
    # Add line breaks after common SQL keywords
    keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 
                'INNER JOIN', 'ORDER BY', 'GROUP BY', 'HAVING', 'LIMIT', 
                'OFFSET', 'UNION', 'ON', 'AND', 'OR']
    
    for keyword in keywords:
        sql = sql.replace(f' {keyword} ', f'\n{keyword} ')
    
    # Add indentation
    lines = sql.split('\n')
    indented_lines = []
    indent_level = 0
    
    for line in lines:
        if any(line.startswith(k) for k in ['FROM', 'WHERE', 'JOIN', 'LEFT JOIN', 
                                           'RIGHT JOIN', 'INNER JOIN', 'ORDER BY', 
                                           'GROUP BY', 'HAVING', 'LIMIT', 'OFFSET', 
                                           'UNION']):
            indent_level = 1
        elif any(line.startswith(k) for k in ['AND', 'OR', 'ON']):
            indent_level = 2
        
        indented_lines.append('    ' * indent_level + line)
    
    return mark_safe('<pre>' + '\n'.join(indented_lines) + '</pre>')