import unittest
import sys
import os
from unittest.mock import patch

# Add the weight-app directory to the path so we can import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../weight-app')))
from main import app

class TestPostWeight(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('main.submit_weight_transaction')
    def test_post_weight_success(self, mock_submit_weight):
        """Test successful weight submission."""
        mock_submit_weight.return_value = {
            'status': 'success',
            'message': 'Transaction recorded successfully',
            'id': '1',
            'truck': 'T-123',
            'bruto': 1000
        }

        payload = {
            'direction': 'in',
            'truck': 'T-123',
            'containers': 'C-1,C-2',
            'weight': 1000,
            'unit': 'kg',
            'produce': 'apples'
        }

        response = self.app.post('/weight', json=payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['status'], 'success')
        mock_submit_weight.assert_called_once_with(
            'in', 'T-123', 'C-1,C-2', 1000, 'kg', 'apples', False
        )

    def test_post_weight_missing_truck_for_in(self):
        """Test IN submission without truck."""
        payload = {
            'direction': 'in',
            'containers': 'C-1,C-2',
            'weight': 1000
        }

        response = self.app.post('/weight', json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['status'], 'error')

    def test_post_weight_invalid_weight(self):
        """Test submission with invalid weight."""
        payload = {
            'direction': 'in',
            'truck': 'T-123',
            'containers': 'C-1,C-2',
            'weight': 0
        }

        response = self.app.post('/weight', json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['status'], 'error')


if __name__ == '__main__':
    unittest.main()