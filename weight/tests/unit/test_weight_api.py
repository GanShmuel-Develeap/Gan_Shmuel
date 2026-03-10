import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the weight-app directory to the path so we can import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../weight-app')))
from main import app

class TestWeightAPIPost(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('main.submit_weight_transaction')
    def test_weight_api_post_json_success_in(self, mock_submit):
        """Test successful POST /weight with JSON for IN direction."""
        mock_submit.return_value = {
            'status': 'success',
            'message': 'Transaction recorded successfully',
            'id': '101',
            'truck': 'T-001',
            'bruto': 5000
        }

        payload = {
            'direction': 'in',
            'truck': 'T-001',
            'containers': 'C-1,C-2',
            'weight': 5000,
            'unit': 'kg',
            'produce': 'Apples'
        }

        response = self.app.post('/weight', 
                                 json=payload,
                                 content_type='application/json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['status'], 'success')
        self.assertEqual(response.json['id'], '101')
        self.assertEqual(response.json['truck'], 'T-001')
        
        # Verify service was called with correct args (note: force defaults to False)
        mock_submit.assert_called_once_with('in', 'T-001', 'C-1,C-2', 5000, 'kg', 'Apples', False)

    @patch('main.submit_weight_transaction')
    def test_weight_api_post_form_success_out(self, mock_submit):
        """Test successful POST /weight with form data for OUT direction."""
        mock_submit.return_value = {
            'status': 'success',
            'message': 'Transaction recorded successfully',
            'id': '102',
            'truck': 'T-001',
            'bruto': 5000,
            'truckTara': 4800,
            'neto': 200
        }

        form_data = {
            'direction': 'out',
            'truck': 'T-001',
            'weight': 4800,
            'unit': 'kg'
        }

        response = self.app.post('/weight', data=form_data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['status'], 'success')
        self.assertEqual(response.json['id'], '102')
        self.assertEqual(response.json['truckTara'], 4800)

    @patch('main.submit_weight_transaction')
    def test_weight_api_truck_defaults_to_na(self, mock_submit):
        """Test that truck defaults to 'na' when not provided."""
        mock_submit.return_value = {
            'status': 'success',
            'message': 'Transaction recorded successfully',
            'id': '103',
            'truck': 'na',
            'bruto': 1000
        }

        payload = {
            'direction': 'none',
            'containers': 'C-5',
            'weight': 1000,
            'unit': 'kg'
        }

        response = self.app.post('/weight', json=payload)

        self.assertEqual(response.status_code, 201)
        # Verify truck was set to 'na'
        mock_submit.assert_called_once_with('none', 'na', 'C-5', 1000, 'kg', 'na', False)

    @patch('main.submit_weight_transaction')
    def test_weight_api_force_true(self, mock_submit):
        """Test POST /weight with force=true."""
        mock_submit.return_value = {
            'status': 'success',
            'message': 'Transaction recorded successfully',
            'id': '104',
            'truck': 'T-002',
            'bruto': 3000
        }

        payload = {
            'direction': 'in',
            'truck': 'T-002',
            'containers': 'C-3',
            'weight': 3000,
            'unit': 'kg',
            'force': True
        }

        response = self.app.post('/weight', json=payload)

        self.assertEqual(response.status_code, 201)
        # Verify force was passed as True
        mock_submit.assert_called_once_with('in', 'T-002', 'C-3', 3000, 'kg', 'na', True)

    @patch('main.submit_weight_transaction')
    def test_weight_api_force_string_true(self, mock_submit):
        """Test POST /weight with force='true' (string)."""
        mock_submit.return_value = {
            'status': 'success',
            'message': 'Transaction recorded successfully',
            'id': '105',
            'truck': 'T-003',
            'bruto': 2000
        }

        payload = {
            'direction': 'in',
            'truck': 'T-003',
            'containers': 'C-4',
            'weight': 2000,
            'unit': 'kg',
            'force': 'true'
        }

        response = self.app.post('/weight', json=payload)

        self.assertEqual(response.status_code, 201)
        # Verify force was converted to True
        mock_submit.assert_called_once_with('in', 'T-003', 'C-4', 2000, 'kg', 'na', True)

    @patch('main.submit_weight_transaction')
    def test_weight_api_force_false(self, mock_submit):
        """Test POST /weight with force=false."""
        mock_submit.return_value = {
            'status': 'success',
            'message': 'Transaction recorded successfully',
            'id': '106',
            'truck': 'T-004',
            'bruto': 1500
        }

        payload = {
            'direction': 'in',
            'truck': 'T-004',
            'containers': 'C-6',
            'weight': 1500,
            'unit': 'kg',
            'force': 'false'
        }

        response = self.app.post('/weight', json=payload)

        self.assertEqual(response.status_code, 201)
        # Verify force was converted to False
        mock_submit.assert_called_once_with('in', 'T-004', 'C-6', 1500, 'kg', 'na', False)

    @patch('main.submit_weight_transaction')
    def test_weight_api_missing_direction(self, mock_submit):
        """Test POST /weight with missing direction."""
        payload = {
            'truck': 'T-001',
            'weight': 5000,
            'unit': 'kg'
        }

        response = self.app.post('/weight', json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['status'], 'error')
        self.assertIn('direction', response.json['message'].lower())

    @patch('main.submit_weight_transaction')
    def test_weight_api_missing_weight(self, mock_submit):
        """Test POST /weight with missing weight."""
        payload = {
            'direction': 'in',
            'truck': 'T-001',
            'containers': 'C-1',
            'unit': 'kg'
        }

        response = self.app.post('/weight', json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['status'], 'error')
        self.assertIn('weight', response.json['message'].lower())

    @patch('main.submit_weight_transaction')
    def test_weight_api_invalid_weight(self, mock_submit):
        """Test POST /weight with non-numeric weight."""
        payload = {
            'direction': 'in',
            'truck': 'T-001',
            'containers': 'C-1',
            'weight': 'invalid',
            'unit': 'kg'
        }

        response = self.app.post('/weight', json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['status'], 'error')
        self.assertIn('number', response.json['message'].lower())

    @patch('main.submit_weight_transaction')
    def test_weight_api_service_error(self, mock_submit):
        """Test POST /weight when service returns error."""
        mock_submit.return_value = {
            'status': 'error',
            'message': 'No prior IN transaction found for this truck'
        }

        payload = {
            'direction': 'out',
            'truck': 'T-999',
            'weight': 4500,
            'unit': 'kg'
        }

        response = self.app.post('/weight', json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['status'], 'error')

    @patch('main.submit_weight_transaction')
    def test_weight_api_default_unit(self, mock_submit):
        """Test POST /weight defaults unit to 'kg' when not provided."""
        mock_submit.return_value = {
            'status': 'success',
            'message': 'Transaction recorded successfully',
            'id': '107',
            'truck': 'T-005',
            'bruto': 2500
        }

        payload = {
            'direction': 'in',
            'truck': 'T-005',
            'containers': 'C-7',
            'weight': 2500
        }

        response = self.app.post('/weight', json=payload)

        self.assertEqual(response.status_code, 201)
        # Verify unit defaults to 'kg'
        mock_submit.assert_called_once()
        call_args = mock_submit.call_args[0]
        self.assertEqual(call_args[4], 'kg')  # unit parameter

    @patch('main.submit_weight_transaction')
    def test_weight_api_produce_defaults_to_na(self, mock_submit):
        """Test POST /weight defaults produce to 'na' when not provided."""
        mock_submit.return_value = {
            'status': 'success',
            'message': 'Transaction recorded successfully',
            'id': '108',
            'truck': 'T-006',
            'bruto': 3500
        }

        payload = {
            'direction': 'in',
            'truck': 'T-006',
            'containers': 'C-8',
            'weight': 3500,
            'unit': 'kg'
        }

        response = self.app.post('/weight', json=payload)

        self.assertEqual(response.status_code, 201)
        # Verify produce defaults to 'na'
        mock_submit.assert_called_once()
        call_args = mock_submit.call_args[0]
        self.assertEqual(call_args[5], 'na')  # produce parameter


if __name__ == '__main__':
    unittest.main()
