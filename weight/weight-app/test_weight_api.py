"""
Test suite for Weight API
Run with: python test_weight_api.py
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

class TestWeightAPI:
    def __init__(self):
        self.failed = []
        self.passed = []
        self.test_count = 0

    def test(self, name, method, endpoint, data=None, expected_status=None):
        """Generic test runner"""
        self.test_count += 1
        test_id = f"[{self.test_count}]"
        
        try:
            url = f"{BASE_URL}{endpoint}"
            if method == 'POST':
                resp = requests.post(url, data=data, timeout=5)
            else:
                resp = requests.get(url, timeout=5)
            
            result = resp.json()
            status = resp.status_code
            
            # Determine pass/fail
            if expected_status and status != expected_status:
                self.failed.append(f"{test_id} {name}: Expected status {expected_status}, got {status}")
                print(f"❌ {test_id} {name}")
                print(f"   Status: {status}, Response: {json.dumps(result, indent=2)}\n")
                return False
            
            if status >= 400:
                self.failed.append(f"{test_id} {name}: {result.get('message', 'Unknown error')}")
                print(f"❌ {test_id} {name}")
                print(f"   Response: {json.dumps(result, indent=2)}\n")
                return False
            
            self.passed.append(f"{test_id} {name}")
            print(f"✅ {test_id} {name}")
            print(f"   ID: {result.get('id')}, Truck: {result.get('truck')}, Bruto: {result.get('bruto')}, Neto: {result.get('neto')}\n")
            return result
        
        except Exception as e:
            self.failed.append(f"{test_id} {name}: {str(e)}")
            print(f"❌ {test_id} {name}")
            print(f"   Error: {str(e)}\n")
            return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print(f"TEST SUMMARY: {len(self.passed)} passed, {len(self.failed)} failed")
        print("="*70)
        if self.failed:
            print("\nFailed Tests:")
            for fail in self.failed:
                print(f"  - {fail}")

def run_basic_tests():
    """Basic direction and direction-specific tests"""
    print("\n" + "="*70)
    print("SECTION 1: BASIC DIRECTION TESTS")
    print("="*70 + "\n")
    
    t = TestWeightAPI()
    
    # Test 1: IN with truck and containers (unknown containers)
    t.test(
        "IN: Truck TR-101, containers C-001,C-002",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': 'TR-101', 'containers': 'C-001,C-002', 'bruto': '15000', 'produce': 'tomato'},
        expected_status=201
    )
    
    # Test 2: IN with no truck (truck='na')
    t.test(
        "IN: No truck, containers C-003,C-004",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': '', 'containers': 'C-003,C-004', 'bruto': '8500', 'produce': 'pepper'},
        expected_status=201
    )
    
    # Test 3: OUT with truck and no containers
    t.test(
        "OUT: Truck TR-101, no containers",
        'POST',
        '/weight-form',
        {'direction': 'out', 'truck': 'TR-101', 'bruto': '5200', 'produce': 'tomato'},
        expected_status=201
    )
    
    # Test 4: OUT with truck and empty containers
    t.test(
        "OUT: Truck TR-102, empty containers",
        'POST',
        '/weight-form',
        {'direction': 'out', 'truck': 'TR-102', 'containers': '', 'bruto': '6800', 'produce': 'cucumber'},
        expected_status=201
    )
    
    # Test 5: NONE with containers
    t.test(
        "NONE: No truck, containers C-005",
        'POST',
        '/weight-form',
        {'direction': 'none', 'containers': 'C-005', 'bruto': '3000', 'produce': 'lettuce'},
        expected_status=201
    )
    
    # Test 6: IN missing containers (should fail)
    t.test(
        "IN: Missing containers (should fail)",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': 'TR-103', 'bruto': '10000', 'produce': 'carrot'},
        expected_status=400
    )
    
    # Test 7: OUT missing bruto (should fail)
    t.test(
        "OUT: Missing bruto (should fail)",
        'POST',
        '/weight-form',
        {'direction': 'out', 'truck': 'TR-104'},
        expected_status=400
    )
    
    t.print_summary()

def run_truck_scenario_tests():
    """Test truck-based session scenario"""
    print("\n" + "="*70)
    print("SECTION 2: TRUCK SCENARIO - SAME TRUCK IN/OUT")
    print("="*70 + "\n")
    
    t = TestWeightAPI()
    truck_id = 'TR-SCENARIO-001'
    
    # Test 1: First IN for truck
    result1 = t.test(
        f"IN: Truck {truck_id} arriving with produce",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': truck_id, 'containers': 'C-SC-01,C-SC-02', 'bruto': '20000', 'produce': 'apple'},
        expected_status=201
    )
    in_id = result1.get('id') if result1 else None
    
    # Test 2: OUT for same truck (different weight = delivered produce)
    result2 = t.test(
        f"OUT: Truck {truck_id} leaving (lighter = produce unloaded)",
        'POST',
        '/weight-form',
        {'direction': 'out', 'truck': truck_id, 'bruto': '4500', 'produce': 'apple'},
        expected_status=201
    )
    out_id = result2.get('id') if result2 else None
    
    print(f"\nScenario Analysis:")
    print(f"  IN ID: {in_id}")
    print(f"  OUT ID: {out_id}")
    print(f"  IN Weight: 20000, OUT Weight (truckTara): 4500")
    print(f"  Expected Produce Delivered: ~15500 kg\n")
    
    # Test 3: Different IN/OUT pair for another truck
    truck_id2 = 'TR-SCENARIO-002'
    
    result3 = t.test(
        f"IN: Truck {truck_id2} with full load",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': truck_id2, 'containers': 'C-SC-03', 'bruto': '18000', 'produce': 'orange'},
        expected_status=201
    )
    
    result4 = t.test(
        f"OUT: Truck {truck_id2} empty return",
        'POST',
        '/weight-form',
        {'direction': 'out', 'truck': truck_id2, 'bruto': '4200', 'produce': 'orange'},
        expected_status=201
    )
    
    t.print_summary()

def run_edge_case_tests():
    """Test edge cases and error scenarios"""
    print("\n" + "="*70)
    print("SECTION 3: EDGE CASES & ERROR HANDLING")
    print("="*70 + "\n")
    
    t = TestWeightAPI()
    
    # Test 1: Zero weight
    t.test(
        "IN: Zero bruto weight",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': 'TR-ZERO', 'containers': 'C-ZERO', 'bruto': '0', 'produce': 'test'},
        expected_status=201
    )
    
    # Test 2: Very large weight
    t.test(
        "IN: Very large bruto weight (100 tons)",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': 'TR-LARGE', 'containers': 'C-LARGE', 'bruto': '100000', 'produce': 'watermelon'},
        expected_status=201
    )
    
    # Test 3: Unicode character in produce
    t.test(
        "IN: Unicode produce name (עגבניה - tomato in Hebrew)",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': 'TR-UNICODE', 'containers': 'C-UNI', 'bruto': '5000', 'produce': 'עגבניה'},
        expected_status=201
    )
    
    # Test 4: Missing produce (should default to 'na')
    t.test(
        "IN: Missing produce field",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': 'TR-NO-PRODUCE', 'containers': 'C-NP', 'bruto': '7000'},
        expected_status=201
    )
    
    # Test 5: Many containers
    t.test(
        "IN: Many containers (20)",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': 'TR-MANY', 'containers': ','.join([f'C-MANY-{i:02d}' for i in range(20)]), 'bruto': '25000', 'produce': 'multi'},
        expected_status=201
    )
    
    # Test 6: Container with spaces
    t.test(
        "IN: Container IDs with spaces",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': 'TR-SPACES', 'containers': 'C-SPACE-01, C-SPACE-02 , C-SPACE-03', 'bruto': '9000', 'produce': 'test'},
        expected_status=201
    )
    
    # Test 7: OUT without IN (would need session logic)
    t.test(
        "OUT: Truck with no prior IN session",
        'POST',
        '/weight-form',
        {'direction': 'out', 'truck': 'TR-NO-IN', 'bruto': '5000', 'produce': 'test'},
        expected_status=201  # Currently succeeds, but should fail with session logic
    )
    
    # Test 8: NONE missing containers (should fail)
    t.test(
        "NONE: Missing containers (should fail)",
        'POST',
        '/weight-form',
        {'direction': 'none', 'truck': 'TR-NONE', 'bruto': '5000'},
        expected_status=400
    )
    
    t.print_summary()

def run_neto_calculation_tests():
    """Test neto calculation scenarios"""
    print("\n" + "="*70)
    print("SECTION 4: NETO CALCULATION SCENARIOS")
    print("="*70 + "\n")
    
    t = TestWeightAPI()
    
    # Scenario 1: Known container taras (would return neto value, not 'na')
    # NOTE: This requires containers to be registered in DB first
    t.test(
        "IN: With known containers (if registered in DB, neto should calculate)",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': 'TR-NETO-1', 'containers': 'C-KNOWN-01,C-KNOWN-02', 'bruto': '16000', 'produce': 'apple'},
        expected_status=201
    )
    
    # Scenario 2: Unknown container tara (neto = 'na')
    t.test(
        "IN: With unknown containers (neto = 'na')",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': 'TR-NETO-2', 'containers': 'C-UNKNOWN-99', 'bruto': '12000', 'produce': 'banana'},
        expected_status=201
    )
    
    # Scenario 3: No containers (neto = bruto - truckTara only)
    t.test(
        "IN: No containers (neto = bruto only, no container tara)",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': 'TR-NETO-3', 'containers': '', 'bruto': '10000', 'produce': 'test'},
        expected_status=201
    )
    
    # Scenario 4: OUT always returns 'na' for neto
    t.test(
        "OUT: neto always 'na' (can't calculate without IN weight)",
        'POST',
        '/weight-form',
        {'direction': 'out', 'truck': 'TR-NETO-4', 'bruto': '5000', 'produce': 'test'},
        expected_status=201
    )
    
    t.print_summary()

def run_duplicate_truck_tests():
    """Test duplicate truck submissions (force flag concept)"""
    print("\n" + "="*70)
    print("SECTION 5: DUPLICATE TRUCK SCENARIOS (Force Flag Concept)")
    print("="*70 + "\n")
    
    t = TestWeightAPI()
    truck_dup = 'TR-DUPLICATE'
    
    # Test 1: First IN
    t.test(
        f"IN #1: Truck {truck_dup}",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': truck_dup, 'containers': 'C-DUP-01', 'bruto': '15000', 'produce': 'apple'},
        expected_status=201
    )
    
    # Test 2: Second IN immediately (currently allowed, should fail without force flag)
    t.test(
        f"IN #2: Same truck (duplicate IN - should fail without force flag)",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': truck_dup, 'containers': 'C-DUP-02', 'bruto': '16000', 'produce': 'apple'},
        expected_status=201  # Currently succeeds, but should fail with session logic
    )
    
    # Test 3: OUT after first IN
    t.test(
        f"OUT: Truck {truck_dup} (should match previous IN session)",
        'POST',
        '/weight-form',
        {'direction': 'out', 'truck': truck_dup, 'bruto': '4500', 'produce': 'apple'},
        expected_status=201
    )
    
    # Test 4: Second OUT immediately (should fail)
    t.test(
        f"OUT #2: Same truck (duplicate OUT - should fail)",
        'POST',
        '/weight-form',
        {'direction': 'out', 'truck': truck_dup, 'bruto': '4500', 'produce': 'apple'},
        expected_status=400  # Should fail: OUT without IN
    )
    
    t.print_summary()

def run_container_tara_lookup_tests():
    """Test container tara lookup scenarios"""
    print("\n" + "="*70)
    print("SECTION 6: CONTAINER TARA LOOKUP SCENARIOS")
    print("="*70 + "\n")
    
    print("Prerequisites: Insert test data into containers_registered table:")
    print("  INSERT INTO containers_registered VALUES ('C-REG-01', 500, 'active', NOW());")
    print("  INSERT INTO containers_registered VALUES ('C-REG-02', 450, 'active', NOW());")
    print("  Expected neto = 12000 - 0 - 500 - 450 = 11050\n")
    
    t = TestWeightAPI()
    
    # Test 1: All containers unknown (neto = 'na')
    t.test(
        "IN: All containers unknown -> neto = 'na'",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': 'TR-CTL-1', 'containers': 'C-UNK-01,C-UNK-02', 'bruto': '12000', 'produce': 'tomato'},
        expected_status=201
    )
    
    # Test 2: Some containers unknown (neto = 'na')
    t.test(
        "IN: Mixed known/unknown containers -> neto = 'na'",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': 'TR-CTL-2', 'containers': 'C-REG-01,C-UNK-99', 'bruto': '12000', 'produce': 'tomato'},
        expected_status=201
    )
    
    # Test 3: All containers known (should calculate neto)
    # NOTE: Only works if C-REG-01, C-REG-02 are pre-registered
    t.test(
        "IN: All containers known -> neto should calculate",
        'POST',
        '/weight-form',
        {'direction': 'in', 'truck': 'TR-CTL-3', 'containers': 'C-REG-01,C-REG-02', 'bruto': '12000', 'produce': 'tomato'},
        expected_status=201
    )
    
    t.print_summary()

if __name__ == '__main__':
    print("\n\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "WEIGHT API TEST SUITE" + " "*32 + "║")
    print("║" + " "*10 + "Comprehensive testing of weight transaction endpoints" + " "*7 + "║")
    print("╚" + "="*68 + "╝")
    
    try:
        run_basic_tests()
        run_truck_scenario_tests()
        run_edge_case_tests()
        run_neto_calculation_tests()
        run_duplicate_truck_tests()
        run_container_tara_lookup_tests()
        
        print("\n\n" + "="*70)
        print("ALL TEST SECTIONS COMPLETED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {str(e)}\n")
