#!/bin/bash
# Manual test script for Weight API
# Run individual curl commands to test endpoints

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

API="http://localhost:5000"

echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}WEIGHT API - CURL TEST SCRIPT${NC}"
echo -e "${YELLOW}Run individual curl commands below manually${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}\n"

# ============================================================================
# SECTION 1: BASIC TESTS
# ============================================================================

echo -e "${YELLOW}SECTION 1: BASIC DIRECTION TESTS${NC}\n"

echo -e "${GREEN}Test 1.1: IN with truck and containers${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=in&truck=TR-101&containers=C-001,C-002&bruto=15000&produce=tomato' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

echo -e "${GREEN}Test 1.2: OUT with truck, no containers${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=out&truck=TR-101&bruto=5200&produce=tomato' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

echo -e "${GREEN}Test 1.3: NONE with containers, no truck${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=none&containers=C-005&bruto=3000&produce=lettuce' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

echo -e "${GREEN}Test 1.4: IN with empty truck (should default to 'na')${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=in&truck=&containers=C-003&bruto=8500&produce=pepper' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

# ============================================================================
# SECTION 2: ERROR SCENARIOS
# ============================================================================

echo -e "\n${YELLOW}SECTION 2: ERROR SCENARIOS (Should return 400)${NC}\n"

echo -e "${GREEN}Test 2.1: IN missing containers (should fail)${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=in&truck=TR-103&bruto=10000&produce=carrot' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

echo -e "${GREEN}Test 2.2: NONE missing containers (should fail)${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=none&truck=TR-NONE&bruto=5000&produce=test' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

echo -e "${GREEN}Test 2.3: Missing direction (should fail)${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'truck=TR-104&containers=C-004&bruto=7000&produce=cucumber' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

echo -e "${GREEN}Test 2.4: Missing bruto (should fail)${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=out&truck=TR-104' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

# ============================================================================
# SECTION 3: TRUCK SCENARIO TESTS
# ============================================================================

echo -e "\n${YELLOW}SECTION 3: TRUCK SCENARIO - IN/OUT FLOW${NC}\n"

echo -e "${GREEN}Test 3.1: IN - Truck TR-SCENARIO-001 arrives${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=in&truck=TR-SCENARIO-001&containers=C-SC-01,C-SC-02&bruto=20000&produce=apple' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

echo -e "${GREEN}Test 3.2: OUT - Same truck departs (lighter = produce delivered)${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=out&truck=TR-SCENARIO-001&bruto=4500&produce=apple' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

echo -e "${GREEN}Expected analysis:${NC}"
echo "  IN: bruto=20000, truck=TR-SCENARIO-001, neto='na' (containers unknown)"
echo "  OUT: truckTara=4500, truck=TR-SCENARIO-001, neto='na' (OUT always 'na')"
echo "  Difference: 20000 - 4500 = 15500 kg delivered\n"

# ============================================================================
# SECTION 4: EDGE CASES
# ============================================================================

echo -e "\n${YELLOW}SECTION 4: EDGE CASES${NC}\n"

echo -e "${GREEN}Test 4.1: Zero weight${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=in&truck=TR-ZERO&containers=C-ZERO&bruto=0&produce=test' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

echo -e "${GREEN}Test 4.2: Very large weight (100 tons)${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=in&truck=TR-LARGE&containers=C-LARGE&bruto=100000&produce=watermelon' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

echo -e "${GREEN}Test 4.3: Many containers (10)${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=in&truck=TR-MANY&containers=C-MANY-01,C-MANY-02,C-MANY-03,C-MANY-04,C-MANY-05,C-MANY-06,C-MANY-07,C-MANY-08,C-MANY-09,C-MANY-10&bruto=25000&produce=multi' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

echo -e "${GREEN}Test 4.4: Container IDs with spaces${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=in&truck=TR-SPACES&containers=C-SPACE-01, C-SPACE-02 , C-SPACE-03&bruto=9000&produce=test' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

echo -e "${GREEN}Test 4.5: Missing produce (should default to 'na')${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=in&truck=TR-NO-PRODUCE&containers=C-NP&bruto=7000' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

# ============================================================================
# SECTION 5: NETO CALCULATION SCENARIOS
# ============================================================================

echo -e "\n${YELLOW}SECTION 5: NETO CALCULATION SCENARIOS${NC}\n"

echo -e "${GREEN}Test 5.1: IN with unknown containers -> neto='na'${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=in&truck=TR-NETO-1&containers=C-UNKNOWN-01&bruto=12000&produce=apple' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

echo -e "${GREEN}Test 5.2: OUT always returns neto='na'${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=out&truck=TR-NETO-2&bruto=5000&produce=test' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

echo -e "${YELLOW}NOTE: To test neto calculation with KNOWN containers:${NC}"
echo "  1. First register containers in database:"
echo "     INSERT INTO containers_registered (container_id, weight, status) VALUES"
echo "       ('C-REG-01', 500, 'active'),"
echo "       ('C-REG-02', 450, 'active');"
echo "  2. Then submit IN with those containers:"
echo "     direction=in&truck=TR-NETO-3&containers=C-REG-01,C-REG-02&bruto=13000&produce=tomato"
echo "     Expected neto = 13000 - 500 - 450 = 12050\n"

# ============================================================================
# SECTION 6: DUPLICATE TRUCK SCENARIOS (FUTURE - require session logic)
# ============================================================================

echo -e "\n${YELLOW}SECTION 6: DUPLICATE TRUCK SCENARIOS (Once session logic added)${NC}\n"

echo -e "${GREEN}Test 6.1: First IN for truck${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=in&truck=TR-DUP&containers=C-DUP-01&bruto=15000&produce=apple' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

echo -e "${GREEN}Test 6.2: Second IN immediately (currently: 201, should be: 400 without force flag)${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=in&truck=TR-DUP&containers=C-DUP-02&bruto=16000&produce=apple' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

echo -e "${GREEN}Test 6.3: OUT for truck${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=out&truck=TR-DUP&bruto=4500&produce=apple' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

echo -e "${GREEN}Test 6.4: Second OUT immediately (should fail: 400)${NC}"
echo "curl -X POST $API/weight-form \\"
echo "  -d 'direction=out&truck=TR-DUP&bruto=4500&produce=apple' \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded'\n"

# ============================================================================
# SECTION 7: BULK TEST WITH JQ (Optional)
# ============================================================================

echo -e "\n${YELLOW}SECTION 7: HELPFUL CURL PATTERNS${NC}\n"

echo -e "${GREEN}Format output as JSON with jq:${NC}"
echo "curl -s -X POST $API/weight-form -d '...' -H 'Content-Type: application/x-www-form-urlencoded' | jq .\n"

echo -e "${GREEN}Pretty print JSON with indentation:${NC}"
echo "curl -s -X POST $API/weight-form -d '...' -H 'Content-Type: application/x-www-form-urlencoded' | jq '.'\n"

echo -e "${GREEN}Extract only specific fields:${NC}"
echo "curl -s -X POST $API/weight-form -d '...' -H 'Content-Type: application/x-www-form-urlencoded' | jq '{id, truck, bruto, neto}'\n"

echo -e "${GREEN}Check HTTP status code:${NC}"
echo "curl -s -w '\\nStatus: %{http_code}\\n' -X POST $API/weight-form -d '...' -H 'Content-Type: application/x-www-form-urlencoded'\n"

# ============================================================================
# SECTION 8: DATABASE QUERIES FOR VERIFICATION
# ============================================================================

echo -e "\n${YELLOW}SECTION 8: DATABASE QUERIES FOR VERIFICATION${NC}\n"

echo -e "${GREEN}View transactions (recent)${NC}"
echo "docker exec weight-mysql mysql -u appuser -papppass appdb -e \"SELECT id, direction, truck, bruto, truckTara, neto, produce FROM transactions ORDER BY id DESC LIMIT 10;\"\n"

echo -e "${GREEN}View containers registered${NC}"
echo "docker exec weight-mysql mysql -u appuser -papppass appdb -e \"SELECT container_id, weight, status FROM containers_registered;\"\n"

echo -e "${GREEN}Count transactions by direction${NC}"
echo "docker exec weight-mysql mysql -u appuser -papppass appdb -e \"SELECT direction, COUNT(*) as count FROM transactions GROUP BY direction;\"\n"

echo -e "${GREEN}Find transactions for a specific truck${NC}"
echo "docker exec weight-mysql mysql -u appuser -papppass appdb -e \"SELECT * FROM transactions WHERE truck='TR-SCENARIO-001';\"\n"

# ============================================================================
# TIPS
# ============================================================================

echo -e "\n${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}TIPS FOR MANUAL TESTING:${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}\n"

echo -e "1. Save test commands to a file and run them:"
echo -e "   ${GREEN}bash test_commands.sh > test_output.txt 2>&1${NC}\n"

echo -e "2. Use curl with -v flag for verbose output:"
echo -e "   ${GREEN}curl -v -X POST ...${NC}\n"

echo -e "3. Test response headers:"
echo -e "   ${GREEN}curl -i -X POST ...${NC}\n"

echo -e "4. Time the requests:"
echo -e "   ${GREEN}time curl -X POST ...${NC}\n"

echo -e "5. Test with different user agents (for debugging):"
echo -e "   ${GREEN}curl -A 'TestBot/1.0' -X POST ...${NC}\n"

echo -e "6. Save response to file:"
echo -e "   ${GREEN}curl -o response.json -X POST ...${NC}\n"

echo -e "7. Compare responses between runs:"
echo -e "   ${GREEN}curl -s ... | jq '.' > run1.json && curl -s ... | jq '.' > run2.json && diff run1.json run2.json${NC}\n"

echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}\n"
