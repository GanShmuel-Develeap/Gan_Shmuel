import unittest
import sys
import os
from unittest.mock import patch, MagicMock, call
from datetime import datetime

# Add the weight-app directory to the path so we can import services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../weight-app')))
from weight_service import submit_weight_transaction

class TestWeightForceLogic(unittest.TestCase):

    @patch('weight_service.get_conn')
    def test_force_false_with_open_session_in_direction(self, mock_get_conn):
        """Test force=false fails when truck has open IN/NONE session."""
        # Setup mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        
        # Simulate existing open session
        mock_cursor.fetchone.side_effect = [
            {'session_id': 'T-001_20260310120000'},  # open session check
            None,  # out check (shouldn't reach here)
        ]

        result = submit_weight_transaction(
            direction='in',
            truck='T-001',
            containers='C-1',
            bruto=5000,
            unit='kg',
            produce='Apples',
            force=False
        )

        self.assertEqual(result['status'], 'error')
        self.assertIn('open session', result['message'].lower())
        mock_cursor.close.assert_called()
        mock_conn.close.assert_called()

    @patch('weight_service.log_event')
    @patch('weight_service.get_conn')
    def test_force_true_overwrites_open_session(self, mock_get_conn, mock_log):
        """Test force=true overwrites existing open IN/NONE session."""
        # Setup mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        
        # Simulate existing open session
        mock_cursor.fetchone.side_effect = [
            {'session_id': 'T-001_20260310120000'},  # open session check
        ]
        mock_cursor.lastrowid = 101

        result = submit_weight_transaction(
            direction='in',
            truck='T-001',
            containers='C-1',
            bruto=5000,
            unit='kg',
            produce='Apples',
            force=True
        )

        # Should delete old session and insert new one
        self.assertEqual(result['status'], 'success')
        # Verify DELETE was called
        delete_calls = [c for c in mock_cursor.execute.call_args_list 
                       if 'DELETE' in str(c)]
        self.assertGreater(len(delete_calls), 0)
        # audit log should have been invoked once
        mock_log.assert_called_once()
        args = mock_log.call_args[0]
        self.assertIn('delete_session', args)

    @patch('weight_service.get_conn')
    def test_force_false_with_existing_out_transaction(self, mock_get_conn):
        """Test force=false fails when session already has OUT transaction."""
        # Setup mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        
        # Simulate OUT transaction exists when trying to submit OUT
        # First call: no open IN/NONE session (for force check on IN)
        # But we're testing OUT direction, so:
        # First call: lookup session_id for OUT
        # Second call: check if OUT already exists
        mock_cursor.fetchone.side_effect = [
            {'session_id': 'T-001_20260310120000'},  # session lookup for OUT
            {'id': 102},  # OUT transaction exists
        ]

        result = submit_weight_transaction(
            direction='out',
            truck='T-001',
            containers='',
            bruto=4800,
            unit='kg',
            produce='na',
            force=False
        )

        self.assertEqual(result['status'], 'error')
        self.assertIn('OUT', result['message'])
        mock_cursor.close.assert_called()
        mock_conn.close.assert_called()

    @patch('weight_service.log_event')
    @patch('weight_service.get_conn')
    def test_force_true_overwrites_out_transaction(self, mock_get_conn, mock_log):
        """Test force=true overwrites existing OUT transaction."""
        # Setup mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        
        # Simulate OUT transaction exists
        mock_cursor.fetchone.side_effect = [
            {'session_id': 'T-001_20260310120000'},  # session lookup for OUT
            {'id': 102},  # OUT transaction exists
        ]
        mock_cursor.lastrowid = 103

        result = submit_weight_transaction(
            direction='out',
            truck='T-001',
            containers='',
            bruto=4800,
            unit='kg',
            produce='na',
            force=True
        )

        # Should delete old OUT and insert new one
        self.assertEqual(result['status'], 'success')
        # Verify DELETE was called for OUT transaction
        delete_calls = [c for c in mock_cursor.execute.call_args_list 
                       if 'DELETE' in str(c)]
        self.assertGreater(len(delete_calls), 0)
        mock_log.assert_called_once()
        self.assertIn('delete_out', mock_log.call_args[0])

    @patch('weight_service.get_conn')
    def test_no_force_logic_for_na_truck_in_direction(self, mock_get_conn):
        """Test that force logic doesn't apply when truck is 'na' for IN/NONE."""
        # Setup mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        
        mock_cursor.lastrowid = 104

        result = submit_weight_transaction(
            direction='in',
            truck='na',
            containers='C-1',
            bruto=5000,
            unit='kg',
            produce='Apples',
            force=False
        )

        self.assertEqual(result['status'], 'success')
        # Should not check for open sessions since truck is 'na'
        # Only one fetch for the INSERT operation
        execute_calls = [c for c in mock_cursor.execute.call_args_list 
                        if 'INSERT' in str(c) or 'SELECT' in str(c)]
        self.assertIsNotNone(result['id'])

    @patch('weight_service.get_session_info')
    @patch('weight_service.get_conn')
    def test_out_transaction_with_session_summary(self, mock_get_conn, mock_get_session):
        """Test OUT transaction retrieves session summary for neto calculation."""
        # Setup mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        
        # Setup session info mock
        mock_get_session.return_value = {
            'status': 'success',
            'data': {
                'session_id': 'T-001_20260310120000',
                'session_summary': {
                    'in_weight': 5000,
                    'out_weight': 4800,
                    'calculated_neto': 200
                }
            }
        }
        
        mock_cursor.fetchone.side_effect = [
            {'session_id': 'T-001_20260310120000'},  # session lookup
            None,  # no existing OUT
        ]
        mock_cursor.lastrowid = 105

        result = submit_weight_transaction(
            direction='out',
            truck='T-001',
            containers='',
            bruto=4800,
            unit='kg',
            produce='na',
            force=False
        )

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['bruto'], 5000)  # IN weight
        self.assertEqual(result['truckTara'], 4800)  # OUT weight
        self.assertEqual(result['neto'], 200)

    @patch('weight_service.get_conn')
    def test_in_direction_with_no_truck_specified(self, mock_get_conn):
        """Test IN transaction defaults truck to 'na' when empty string provided."""
        # Setup mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        
        mock_cursor.lastrowid = 106

        result = submit_weight_transaction(
            direction='in',
            truck='',
            containers='C-1',
            bruto=5000,
            unit='kg',
            produce='Apples',
            force=False
        )

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['truck'], 'na')


if __name__ == '__main__':
    unittest.main()
