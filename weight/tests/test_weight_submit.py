import unittest
import sys
import os
from unittest.mock import patch

# Add the weight-app directory to the path so we can import main
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../weight-app')))
from main import app

class TestWeightSubmit(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('main.submit_weight_transaction')
    def test_weight_submit_success(self, mock_submit):
        """Test successful submission of weight transaction."""
        # Mock successful response from service
        mock_submit.return_value = {
            'status': 'success',
            'message': 'Transaction recorded successfully',
            'id': '100',
            'truck': 'T-123',
            'bruto': 5000
        }

        form_data = {
            'direction': 'in',
            'truck': 'T-123',
            'containers': 'C-1,C-2',
            'bruto': '5000',
            'unit': 'kg',
            'produce': 'Apples'
        }

        response = self.app.post('/weight-form', data=form_data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['status'], 'success')
        self.assertEqual(response.json['id'], '100')
        
        # Verify service was called with correct args
        mock_submit.assert_called_once_with('in', 'T-123', 'C-1,C-2', '5000', 'kg', 'Apples')

    @patch('main.submit_weight_transaction')
    def test_weight_submit_failure(self, mock_submit):
        """Test failed submission of weight transaction."""
        # Mock error response from service
        mock_submit.return_value = {
            'status': 'error',
            'message': 'Missing required fields'
        }

        response = self.app.post('/weight-form', data={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['status'], 'error')

if __name__ == '__main__':
    unittest.main()