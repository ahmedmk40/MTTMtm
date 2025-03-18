"""
Rule compiler service for the Rule Engine.

This service is responsible for compiling rule conditions into executable code.
"""

import logging
import ast
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


def compile_rule_condition(condition: str) -> Tuple[bool, str]:
    """
    Compile and validate a rule condition.
    
    Args:
        condition: The rule condition as a Python expression
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if the condition is empty
    if not condition or not condition.strip():
        return False, "Condition cannot be empty"
    
    # Parse the condition to check for syntax errors
    try:
        parsed = ast.parse(condition, mode='eval')
    except SyntaxError as e:
        return False, f"Syntax error: {str(e)}"
    
    # Check for potentially unsafe operations
    validator = RuleConditionValidator()
    try:
        validator.visit(parsed)
    except ValueError as e:
        return False, str(e)
    
    # If we got here, the condition is valid
    return True, ""


class RuleConditionValidator(ast.NodeVisitor):
    """
    AST visitor to validate rule conditions for safety.
    """
    
    def __init__(self):
        self.allowed_functions = {
            'abs', 'min', 'max', 'sum', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'round'
        }
    
    def visit_Call(self, node):
        """
        Check function calls to ensure they're allowed.
        """
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name not in self.allowed_functions:
                raise ValueError(f"Function '{func_name}' is not allowed in rule conditions")
        elif isinstance(node.func, ast.Attribute):
            # Allow some common string and list methods
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'str':
                # String methods are generally safe
                pass
            elif isinstance(node.func.value, ast.Name) and node.func.value.id == 'list':
                # List methods are generally safe
                pass
            else:
                # Check if we're accessing transaction attributes
                if not (isinstance(node.func.value, ast.Name) and node.func.value.id == 'transaction'):
                    if not (isinstance(node.func.value, ast.Attribute) and 
                            isinstance(node.func.value.value, ast.Name) and 
                            node.func.value.value.id == 'transaction'):
                        raise ValueError(f"Method call '{ast.unparse(node.func)}' is not allowed in rule conditions")
        else:
            raise ValueError(f"Complex function call '{ast.unparse(node)}' is not allowed in rule conditions")
        
        # Continue checking the arguments
        for arg in node.args:
            self.visit(arg)
        for keyword in node.keywords:
            self.visit(keyword.value)
    
    def visit_Attribute(self, node):
        """
        Check attribute access to ensure it's allowed.
        """
        # Allow accessing transaction attributes
        if isinstance(node.value, ast.Name) and node.value.id == 'transaction':
            return
        
        # Allow nested transaction attributes
        if isinstance(node.value, ast.Attribute):
            self.visit(node.value)
            return
        
        # Otherwise, visit the value
        self.visit(node.value)
    
    def visit_Name(self, node):
        """
        Check variable names to ensure they're allowed.
        """
        # Allow 'transaction' as the main variable
        if node.id == 'transaction':
            return
        
        # Allow built-in constants
        if node.id in ('True', 'False', 'None'):
            return
        
        # Disallow other variables
        if node.id not in self.allowed_functions:
            raise ValueError(f"Variable '{node.id}' is not allowed in rule conditions")
    
    def generic_visit(self, node):
        """
        Check other node types to ensure they're allowed.
        """
        # Disallow certain potentially unsafe operations
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.FunctionDef, 
                             ast.AsyncFunctionDef, ast.Await, ast.Yield, ast.YieldFrom)):
            raise ValueError(f"Operation '{type(node).__name__}' is not allowed in rule conditions")
        
        super().generic_visit(node)