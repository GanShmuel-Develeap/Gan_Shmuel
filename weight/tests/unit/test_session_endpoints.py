import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# add path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../weight-app')))
from main import app

class TestSessionEndpoints(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('main.get_conn')
    def test_abandoned_sessions_default_timeout(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # simulate one row returned
        mock_cursor.fetchall.return_value = [
            {'session_id': 'T-001_20260309120000', 'first_in': '2026-03-09 12:00:00', 'truck': 'T-001'}
        ]

        resp = self.app.get('/sessions/abandoned')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]['session_id'], 'T-001_20260309120000')

        # ensure query executed with default timeout
        mock_cursor.execute.assert_called()
        args = mock_cursor.execute.call_args[0][1]
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], 86400)

    @patch('main.get_conn')
    def test_abandoned_sessions_custom_timeout(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        resp = self.app.get('/sessions/abandoned?timeout=3600')
        self.assertEqual(resp.status_code, 200)
        mock_cursor.execute.assert_called()
        args = mock_cursor.execute.call_args[0][1]
        self.assertEqual(args[0], 3600)

    @patch('main.get_conn')
    def test_session_audit(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            {'event_id': 1, 'transaction_id': 5, 'action': 'insert', 'details': None, 'performed_by': None, 'timestamp': '2026-03-10 12:00:00'}
        ]

        resp = self.app.get('/sessions/TESTSESSION/audit')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['action'], 'insert')
        mock_cursor.execute.assert_called()
        # ensure session id passed both as param and in details wildcard
        params = mock_cursor.execute.call_args[0][1]
        self.assertEqual(params[0], 'TESTSESSION')
        self.assertIn('TESTSESSION', params[1])

if __name__ == '__main__':
    unittest.main()