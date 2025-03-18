"""
Tests for the cases app.
"""

import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Case, CaseTransaction, CaseNote, CaseAttachment, CaseActivity
from apps.transactions.models import Transaction

User = get_user_model()


class CaseModelTests(TestCase):
    """
    Tests for the Case model.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        self.case = Case.objects.create(
            case_id=f'CASE-{uuid.uuid4().hex[:8].upper()}',
            title='Test Case',
            description='This is a test case',
            priority='medium',
            status='open',
            created_by=self.user
        )
    
    def test_case_creation(self):
        """
        Test that a case can be created.
        """
        self.assertEqual(Case.objects.count(), 1)
        self.assertEqual(self.case.title, 'Test Case')
        self.assertEqual(self.case.status, 'open')
        self.assertEqual(self.case.created_by, self.user)
    
    def test_case_str(self):
        """
        Test the string representation of a case.
        """
        self.assertEqual(str(self.case), f"{self.case.case_id} - Test Case")
    
    def test_close_case(self):
        """
        Test closing a case.
        """
        self.case.close_case('false_positive', self.user)
        self.assertEqual(self.case.status, 'closed')
        self.assertEqual(self.case.resolution, 'false_positive')
        self.assertIsNotNone(self.case.closed_at)


class CaseViewTests(TestCase):
    """
    Tests for the case views.
    """
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.client.login(username='testuser', password='testpassword')
        
        self.case = Case.objects.create(
            case_id=f'CASE-{uuid.uuid4().hex[:8].upper()}',
            title='Test Case',
            description='This is a test case',
            priority='medium',
            status='open',
            created_by=self.user
        )
        
        # Create a test transaction
        self.transaction = Transaction.objects.create(
            transaction_id='tx_test_123',
            transaction_type='acquiring',
            channel='pos',
            amount=100.0,
            currency='USD',
            user_id='user_123',
            merchant_id='merchant_456',
            timestamp=timezone.now().timestamp()
        )
    
    def test_case_list_view(self):
        """
        Test the case list view.
        """
        response = self.client.get(reverse('cases:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Case')
        self.assertTemplateUsed(response, 'cases/list.html')
    
    def test_case_detail_view(self):
        """
        Test the case detail view.
        """
        response = self.client.get(reverse('cases:detail', args=[self.case.case_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Case')
        self.assertTemplateUsed(response, 'cases/detail.html')
    
    def test_case_create_view(self):
        """
        Test creating a case.
        """
        response = self.client.post(reverse('cases:create'), {
            'title': 'New Test Case',
            'description': 'This is a new test case',
            'priority': 'high',
            'status': 'open'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertEqual(Case.objects.count(), 2)
        new_case = Case.objects.get(title='New Test Case')
        self.assertEqual(new_case.priority, 'high')
    
    def test_add_transaction_to_case(self):
        """
        Test adding a transaction to a case.
        """
        response = self.client.post(reverse('cases:detail', args=[self.case.case_id]), {
            'transaction_ids': 'tx_test_123',
            'form_type': 'add_transaction'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful addition
        self.assertEqual(CaseTransaction.objects.count(), 1)
        case_transaction = CaseTransaction.objects.first()
        self.assertEqual(case_transaction.case, self.case)
        self.assertEqual(case_transaction.transaction_id, 'tx_test_123')
    
    def test_add_note_to_case(self):
        """
        Test adding a note to a case.
        """
        response = self.client.post(reverse('cases:detail', args=[self.case.case_id]), {
            'content': 'This is a test note',
            'form_type': 'add_note'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful addition
        self.assertEqual(CaseNote.objects.count(), 1)
        note = CaseNote.objects.first()
        self.assertEqual(note.case, self.case)
        self.assertEqual(note.content, 'This is a test note')
