import unittest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../weight-app')))
from main import app

class TestBatchWeight(unittest.TestCase):

    def setUp(self):
        # Create a test client for the Flask app
        self.app = app.test_client()
        self.app.testing = True

    @patch('main.get_conn')
    @patch('main.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='[{"id":"C1","weight":100,"unit":"kg"}]')
    def test_batch_weight_json_success(self, mock_file, mock_exists, mock_get_conn):
        """Test successful processing of a JSON file."""
        # Mock that the file exists
        mock_exists.return_value = True
        
        # Mock the database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Send POST request
        response = self.app.post('/batch-weight', data={'file': 'test_data.json'})

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Batch processed", response.data)
        
        # Verify that executemany was called with correct data
        mock_cursor.executemany.assert_called_once()
        args = mock_cursor.executemany.call_args[0]
        self.assertIn("INSERT INTO containers_registered", args[0])
        # JSON loads numbers as ints/floats
        self.assertEqual(args[1], [('C1', 100, 'kg')])

    @patch('main.get_conn')
    @patch('main.os.path.exists')
    def test_batch_weight_csv_success(self, mock_exists, mock_get_conn):
        """Test successful processing of a CSV file."""
        mock_exists.return_value = True
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock CSV content
        csv_content = "id,weight,unit\nC2,200,kg"
        
        # We patch open specifically for this test to return the CSV content
        with patch('builtins.open', mock_open(read_data=csv_content)):
            response = self.app.post('/batch-weight', data={'file': 'test_data.csv'})

        self.assertEqual(response.status_code, 200)
        
        # Verify data. Note: csv module reads values as strings
        expected_data = [('C2', '200', 'kg')]
        mock_cursor.executemany.assert_called_once()
        self.assertEqual(mock_cursor.executemany.call_args[0][1], expected_data)

    def test_batch_weight_no_filename(self):
        """Test error when no filename is provided."""
        response = self.app.post('/batch-weight', data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Filename not provided", response.data)

    @patch('main.os.path.exists')
    def test_batch_weight_file_not_found(self, mock_exists):
        """Test error when the file does not exist."""
        mock_exists.return_value = False
        response = self.app.post('/batch-weight', data={'file': 'missing.json'})
        self.assertEqual(response.status_code, 704)
        self.assertIn(b"File not found", response.data)

    @patch('main.os.path.exists')
    def test_batch_weight_invalid_format(self, mock_exists):
        """Test error when file extension is not supported."""
        mock_exists.return_value = True
        response = self.app.post('/batch-weight', data={'file': 'data.txt'})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid file format", response.data)

    @patch('main.get_conn')
    @patch('main.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='[]')
    def test_batch_weight_db_error(self, mock_file, mock_exists, mock_get_conn):
        """Test handling of database errors."""
        mock_exists.return_value = True
        
        # Simulate an exception during DB connection
        mock_get_conn.side_effect = Exception("DB Connection Failed")

        response = self.app.post('/batch-weight', data={'file': 'data.json'})
        
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"DB Connection Failed", response.data)

if __name__ == '__main__':
    unittest.main()
