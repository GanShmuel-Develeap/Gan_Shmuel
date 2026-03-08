#!/usr/bin/env python3
"""
Standalone Test Runner for Weight API
Can be run as: python3 test_standalone.py
Requires: requests library
Install: pip install requests
"""

import subprocess
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class WeightAPITester:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results = []
        self.test_number = 0
        
    def run_test(self, name: str, endpoint: str, method: str = "POST", 
                 data: Optional[Dict] = None, expect_status: int = 201) -> Optional[Dict]:
        """Run a single test"""
        self.test_number += 1
        
        # Build curl command
        url = f"{self.base_url}{endpoint}"
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method, url]
        
        if method == "POST" and data:
            form_data = "&".join([f"{k}={v}" for k, v in data.items()])
            cmd.extend(["-d", form_data])
            cmd.extend(["-H", "Content-Type: application/x-www-form-urlencoded"])
        
        try:
            # Execute curl
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            # Parse response
            lines = result.stdout.strip().split('\n')
            status_code = int(lines[-1])
            response_text = '\n'.join(lines[:-1])
            
            try:
                response_json = json.loads(response_text)
            except:
                response_json = {"error": "Invalid JSON response", "raw": response_text}
            
            # Determine pass/fail
            passed = status_code == expect_status
            
            # Store result
            test_result = {
                "number": self.test_number,
                "name": name,
                "endpoint": endpoint,
                "passed": passed,
                "status_code": status_code,
                "expected_status": expect_status,
                "response": response_json
            }
            self.results.append(test_result)
            
            # Print result
            status_symbol = "✅" if passed else "❌"
            print(f"{status_symbol} [{self.test_number:02d}] {name}")
            if not passed:
                print(f"      Expected: {expect_status}, Got: {status_code}")
            if response_json.get('id'):
                print(f"      Transaction ID: {response_json['id']}")
                print(f"      Details: truck={response_json.get('truck')}, bruto={response_json.get('bruto')}, neto={response_json.get('neto')}")
            if not passed and response_json.get('message'):
                print(f"      Message: {response_json['message']}")
            
            return response_json if passed else None
            
        except subprocess.TimeoutExpired:
            print(f"❌ [{self.test_number:02d}] {name} - TIMEOUT")
            self.results.append({
                "number": self.test_number,
                "name": name,
                "endpoint": endpoint,
                "passed": False,
                "error": "timeout"
            })
            return None
        except Exception as e:
            print(f"❌ [{self.test_number:02d}] {name} - ERROR: {str(e)}")
            self.results.append({
                "number": self.test_number,
                "name": name,
                "endpoint": endpoint,
                "passed": False,
                "error": str(e)
            })
            return None
    
    def print_summary(self):
        """Print test summary"""
        passed = sum(1 for r in self.results if r.get('passed', False))
        total = len(self.results)
        failed = total - passed
        
        print(f"\n{'='*70}")
        print(f"TEST SUMMARY: {passed}/{total} passed, {failed} failed")
        print(f"{'='*70}\n")
        
        if failed > 0:
            print("Failed Tests:")
            for r in self.results:
                if not r.get('passed', False):
                    print(f"  [{r['number']:02d}] {r['name']}")
                    if r.get('error'):
                        print(f"      Error: {r['error']}")
                    else:
                        print(f"      Expected status {r.get('expected_status')}, got {r.get('status_code')}")

def test_suite_1_basic() -> List[Tuple[str, Dict, int]]:
    """Basic direction tests - Success cases"""
    return [
        ("Basic IN: truck + containers", 
         {'direction': 'in', 'truck': 'TR-B1', 'containers': 'C-B1-01,C-B1-02', 'bruto': '15000', 'produce': 'tomato'}, 
         201),
        
        ("Basic OUT: truck only",
         {'direction': 'out', 'truck': 'TR-B1', 'bruto': '5200', 'produce': 'tomato'},
         201),
        
        ("Basic NONE: containers only",
         {'direction': 'none', 'containers': 'C-B1-03', 'bruto': '3000', 'produce': 'lettuce'},
         201),
        
        ("IN: truck defaults to 'na'",
         {'direction': 'in', 'truck': '', 'containers': 'C-B1-04', 'bruto': '8500', 'produce': 'pepper'},
         201),
        
        ("IN: produce defaults to 'na'",
         {'direction': 'in', 'truck': 'TR-B2', 'containers': 'C-B2-01', 'bruto': '12000'},
         201),
    ]

def test_suite_2_errors() -> List[Tuple[str, Dict, int]]:
    """Error scenarios - Should fail with 400"""
    return [
        ("Error: IN missing containers",
         {'direction': 'in', 'truck': 'TR-E1', 'bruto': '10000', 'produce': 'carrot'},
         400),
        
        ("Error: NONE missing containers",
         {'direction': 'none', 'truck': 'TR-E2', 'bruto': '5000', 'produce': 'test'},
         400),
        
        ("Error: Missing direction",
         {'truck': 'TR-E3', 'containers': 'C-E3', 'bruto': '7000'},
         400),
        
        ("Error: Invalid bruto (non-numeric)",
         {'direction': 'in', 'truck': 'TR-E4', 'containers': 'C-E4', 'bruto': 'abc'},
         400),
    ]

def test_suite_3_truck_scenario() -> List[Tuple[str, Dict, int]]:
    """Truck in/out scenario"""
    return [
        ("Scenario: IN - Truck arrives loaded",
         {'direction': 'in', 'truck': 'TR-SCENARIO-A', 'containers': 'C-SC-A1,C-SC-A2', 'bruto': '20000', 'produce': 'apple'},
         201),
        
        ("Scenario: OUT - Same truck leaves",
         {'direction': 'out', 'truck': 'TR-SCENARIO-A', 'bruto': '4500', 'produce': 'apple'},
         201),
    ]

def test_suite_4_edge_cases() -> List[Tuple[str, Dict, int]]:
    """Edge cases"""
    return [
        ("Edge: Zero weight",
         {'direction': 'in', 'truck': 'TR-EDGE-1', 'containers': 'C-EDGE-1', 'bruto': '0', 'produce': 'test'},
         201),
        
        ("Edge: Very large weight (100 tons)",
         {'direction': 'in', 'truck': 'TR-EDGE-2', 'containers': 'C-EDGE-2', 'bruto': '100000', 'produce': 'watermelon'},
         201),
        
        ("Edge: Many containers (10)",
         {'direction': 'in', 'truck': 'TR-EDGE-3', 'containers': 'C-E3-1,C-E3-2,C-E3-3,C-E3-4,C-E3-5,C-E3-6,C-E3-7,C-E3-8,C-E3-9,C-E3-10', 'bruto': '25000', 'produce': 'multi'},
         201),
        
        ("Edge: Containers with spaces",
         {'direction': 'in', 'truck': 'TR-EDGE-4', 'containers': 'C-EDGE-4 , C-EDGE-5 , C-EDGE-6', 'bruto': '9000', 'produce': 'test'},
         201),
        
        ("Edge: Special characters in produce",
         {'direction': 'in', 'truck': 'TR-EDGE-5', 'containers': 'C-EDGE-7', 'bruto': '5000', 'produce': 'עגבניה'},
         201),
    ]

def test_suite_5_neto() -> List[Tuple[str, Dict, int]]:
    """Neto calculation scenarios"""
    return [
        ("Neto: Unknown containers -> 'na'",
         {'direction': 'in', 'truck': 'TR-NETO-1', 'containers': 'C-UNK-99', 'bruto': '12000', 'produce': 'apple'},
         201),
        
        ("Neto: OUT always 'na'",
         {'direction': 'out', 'truck': 'TR-NETO-2', 'bruto': '5000', 'produce': 'test'},
         201),
    ]

def main():
    print("\n" + "="*70)
    print("WEIGHT API - COMPREHENSIVE TEST SUITE")
    print("="*70 + "\n")
    
    tester = WeightAPITester()
    
    # Run all test suites
    test_suites = [
        ("BASIC DIRECTION TESTS", test_suite_1_basic()),
        ("ERROR SCENARIOS", test_suite_2_errors()),
        ("TRUCK IN/OUT SCENARIO", test_suite_3_truck_scenario()),
        ("EDGE CASES", test_suite_4_edge_cases()),
        ("NETO CALCULATION", test_suite_5_neto()),
    ]
    
    for suite_name, tests in test_suites:
        print(f"\n{suite_name}:")
        print("-" * 70)
        
        for test_name, test_data, expected_status in tests:
            tester.run_test(test_name, '/weight-form', 'POST', test_data, expected_status)
            time.sleep(0.1)  # Small delay between tests
    
    # Print summary
    tester.print_summary()
    
    # Return exit code based on results
    passed = sum(1 for r in tester.results if r.get('passed', False))
    total = len(tester.results)
    
    if passed == total:
        print(f"✅ All {total} tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
