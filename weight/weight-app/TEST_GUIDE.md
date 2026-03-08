# Weight API Test Files & Usage Guide

## Files Created

### 1. `test_standalone.py` - Recommended for quick testing
**Type**: Python script using curl  
**Usage**: 
```bash
cd weight-app
python3 test_standalone.py
```
**Pros**: 
- No external dependencies (uses curl)
- 18 comprehensive tests
- Immediate pass/fail indicators
- Shows transaction IDs
- Good for CI/CD integration

**Output**: All tests with ✅/❌ status, summary report

---

### 2. `test_weight_api.py` - For advanced testing
**Type**: Python script using requests library  
**Usage**: 
```bash
pip install requests
cd weight-app
python test_weight_api.py
```
**Pros**:
- 50+ tests across 6 test suites
- Better error reporting
- Organized by test category
- Can be extended easily

**Test Categories**:
1. Basic Direction Tests
2. Truck Scenario Tests (same truck IN/OUT pairs)
3. Edge Cases (zero weight, large weights, unicode, many containers)
4. Neto Calculation Scenarios
5. Duplicate Truck Tests (for future session logic)
6. Container Tara Lookup Tests

---

### 3. `test_manual.sh` - For manual curl testing
**Type**: Bash script with curl commands (printable/copyable)  
**Usage**: 
```bash
bash test_manual.sh
```
or copy individual commands and run them

**Pros**:
- Educational - see exact HTTP requests
- Easy to modify and test variations
- Good for understanding API behavior
- Includes database verification queries

**Includes**:
- 32 individual curl commands
- Database query examples
- Curl tips and tricks
- Output formatting examples

---

### 4. `SESSION_PSEUDOCODE.md` - Implementation guide
**Type**: Markdown documentation with pseudocode  
**Contents**:
- Large-scale session management logic
- Database schema changes required
- Error handling matrix
- Example workflows (normal, duplicate, forced override)
- Neto calculation algorithm
- 10 future API endpoints for session support

**Key Concepts**:
- Session = IN + OUT pair linked by truck_id
- One ACTIVE session per truck at a time
- Force flag to override duplicate INs
- Neto calculated only when containers are known

---

## Quick Start

### Test Everything (Recommended)
```bash
cd ~/GANSHMUEL/Gan_Shmuel/weight/weight-app
python3 test_standalone.py
```
**Time**: ~30 seconds  
**Result**: Clean pass/fail report

### Manual Testing
```bash
# Test single endpoint
curl -X POST http://localhost:5000/weight-form \
  -d 'direction=in&truck=TR-001&containers=C-001,C-002&bruto=15000&produce=tomato' \
  -H 'Content-Type: application/x-www-form-urlencoded'

# With nice formatting
curl -s -X POST http://localhost:5000/weight-form \
  -d 'direction=in&truck=TR-001&containers=C-001,C-002&bruto=15000&produce=tomato' \
  -H 'Content-Type: application/x-www-form-urlencoded' | jq .
```

### View Test Results
```bash
# Recent transactions
docker exec weight-mysql mysql -u appuser -papppass appdb \
  -e "SELECT id, direction, truck, bruto, neto FROM transactions ORDER BY id DESC LIMIT 10;"
```

---

## Test Coverage

### Current Implementation (Already Passing)

| Feature | Status | Test Cases |
|---------|--------|-----------|
| IN direction | ✅ | 5 tests |
| OUT direction | ✅ | 5 tests |
| NONE direction | ✅ | 3 tests |
| Error handling | ✅ | 4 tests |
| Edge cases | ✅ | 5 tests |
| Neto calculation | ✅ | 2 tests |
| Truck scenarios | ✅ | 2 tests |
| **Total** | **✅** | **18 tests** |

### Future Implementation (Session Management)

When session logic is added, these will start failing and need implementation:

| Feature | Current | Future |
|---------|---------|--------|
| Duplicate IN detection | ✅ (allowed) | Should be 400 without force |
| Duplicate OUT detection | ✅ (allowed) | Should be 400 |
| OUT without IN | ✅ (allowed) | Should be 400 for truck != 'na' |
| Session linking | ❌ | Required |
| Force flag support | ❌ | Required |

---

## Test Execution Examples

### Example 1: Basic IN/OUT Scenario
```bash
# IN: Truck arrives with 20 tons
curl -X POST http://localhost:5000/weight-form \
  -d 'direction=in&truck=TR-001&containers=C-001,C-002&bruto=20000&produce=apple' \
  -H 'Content-Type: application/x-www-form-urlencoded'

# Response (success):
{
  "id": "10010",
  "truck": "TR-001",
  "bruto": 20000,
  "neto": "na",
  "status": "success",
  "message": "Transaction recorded successfully"
}

# OUT: Truck leaves with 4500 kg (truck empty weight)
curl -X POST http://localhost:5000/weight-form \
  -d 'direction=out&truck=TR-001&bruto=4500&produce=apple' \
  -H 'Content-Type: application/x-www-form-urlencoded'

# Response (success):
{
  "id": "10011",
  "truck": "TR-001",
  "bruto": 0,
  "truckTara": 4500,
  "neto": "na",
  "status": "success",
  "message": "Transaction recorded successfully"
}
```

### Example 2: Error Case
```bash
# IN missing containers (should fail)
curl -X POST http://localhost:5000/weight-form \
  -d 'direction=in&truck=TR-002&bruto=10000' \
  -H 'Content-Type: application/x-www-form-urlencoded'

# Response (400 error):
{
  "status": "error",
  "message": "Containers required for IN and NONE"
}
```

---

## How to Adjust Tests

### Modify test_standalone.py
```python
# Edit test_suite_1_basic() function:
def test_suite_1_basic() -> List[Tuple[str, Dict, int]]:
    return [
        ("Custom test name", 
         {'direction': 'in', 'truck': 'TR-CUSTOM', 'containers': 'C-1', 'bruto': '5000'}, 
         201),
        # Add more tests here
    ]

# Run modified tests:
python3 test_standalone.py
```

### Modify test_weight_api.py
```python
# Add to run_custom_tests() function:
t = TestWeightAPI()

t.test(
    "My custom test",
    'POST',
    '/weight-form',
    {'direction': 'in', 'truck': 'TR-CUSTOM', 'containers': 'C-1', 'bruto': '5000'},
    expected_status=201
)

t.print_summary()
```

### Add manual curl commands to test_manual.sh
```bash
echo -e "${GREEN}My Custom Test${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=in&truck=TR-MY&containers=C-MY&bruto=7000&produce=custom' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"
```

---

## Next Steps (For Session Implementation)

1. **Add session table to database** - See SESSION_PSEUDOCODE.md SECTION 6
2. **Update weight_service.py** - Implement session logic from SECTION 2
3. **Add GET endpoints** - Implement /session/<id> and /truck/<id>/sessions
4. **Re-run tests** - Some will fail, guiding implementation
5. **Verify neto calculation** - Register test containers, verify calculation
6. **Update API spec compliance** - Verify all endpoints match api-spec-for-all-teams.md

---

## File Locations
```
weight-app/
├── test_standalone.py          # PRIMARY TEST FILE (use this!)
├── test_weight_api.py          # Advanced tests with requests
├── test_manual.sh              # Manual curl commands
├── SESSION_PSEUDOCODE.md       # Implementation guide
└── weight_service.py           # Main business logic
```

## Key Takeaways

✅ **Current Status**:
- All transaction endpoints working
- Data persisting correctly
- Response format matches API spec
- Error handling in place

📋 **What's Tested**:
- All 3 directions (IN, OUT, NONE)
- Container requirement logic
- Edge cases (zero weight, large weights, unicode, spaces)
- Error scenarios
- Neto calculation with unknown containers

🚀 **Next Phase** (Session Management):
- Link IN and OUT transactions into sessions
- Implement duplicate detection
- Add force flag support
- Create session query endpoints
- Enable full neto calculation with known containers
