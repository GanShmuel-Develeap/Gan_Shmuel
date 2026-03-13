import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the weight-app directory to the path so we can import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../weight-app')))
from main import app

class TestGetUnknown(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('main.get_conn')
    def test_get_unknown_containers(self, mock_get_conn):
        """Test retrieving unknown containers successfully."""
        # Mock DB connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock return values: list of tuples (container_id,)
        mock_cursor.fetchall.return_value = [("C-123",), ("C-456",)]

        response = self.app.get('/unknown')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, ["C-123", "C-456"])
        
        mock_cursor.execute.assert_called_once_with("SELECT container_id FROM containers_registered WHERE weight IS NULL")

    @patch('main.get_conn')
    def test_get_unknown_empty(self, mock_get_conn):
        """Test retrieving unknown containers when none exist."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = []

        response = self.app.get('/unknown')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])

if __name__ == '__main__':
    unittest.main()