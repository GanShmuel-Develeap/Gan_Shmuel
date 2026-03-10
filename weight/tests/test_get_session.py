import unittest
import sys
import os
from unittest.mock import patch

# Add the weight-app directory to the path so we can import main
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../weight-app')))
from main import app

class TestGetSession(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('main.get_session_info')
    def test_get_session_found(self, mock_get_session):
        """Test retrieving an existing session."""
        mock_data = {
            'session_id': 'S-100',
            'truck': 'T-123',
            'transactions': []
        }
        mock_get_session.return_value = {
            'status': 'success',
            'data': mock_data
        }

        response = self.app.get('/session/S-100')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, mock_data)
        mock_get_session.assert_called_once_with('S-100')

    @patch('main.get_session_info')
    def test_get_session_not_found(self, mock_get_session):
        """Test retrieving a non-existent session."""
        mock_get_session.return_value = {
            'status': 'error',
            'message': 'Session not found'
        }

        response = self.app.get('/session/UNKNOWN')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['status'], 'error')

if __name__ == '__main__':
    unittest.main()