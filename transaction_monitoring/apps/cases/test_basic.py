"""
Basic tests for the cases app.
"""

from django.test import TestCase


class BasicCaseTests(TestCase):
    """
    Basic tests for the cases app.
    """
    
    def test_basic(self):
        """
        Basic test to ensure the test runner works.
        """
        self.assertEqual(1 + 1, 2)