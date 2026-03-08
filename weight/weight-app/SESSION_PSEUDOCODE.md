# SESSION MANAGEMENT & NETO CALCULATION PSEUDOCODE
# Weight API Design Specification

"""
=============================================================================
PSEUDOCODE FOR SESSION MANAGEMENT & NETO CALCULATION
=============================================================================
"""

# ============================================================================
# 1. SESSION MANAGEMENT LOGIC
# ============================================================================
"""
CONCEPT:
- One session = one complete weighing cycle
- IN creates a new session for a truck (starts with produce arrival)
- OUT closes the session for that truck (ends with produce departure)
- A truck can have multiple sessions over time, but only one ACTIVE session
- The IN and OUT are linked via truck_id + session_id

DATA STRUCTURES:
1. transactions table (EXISTING):
   - id (transaction ID, primary key)
   - session_id (links IN/OUT pair, NULL if no session yet)
   - direction (in/out/none)
   - truck (truck license or 'na')
   - containers (comma-delimited list)
   - bruto (weight in kg)
   - truckTara (truck weight in kg)
   - neto (calculated weight or 'na')
   - produce (type of produce)
   - datetime (server timestamp)

2. sessions table (NEW):
   - id (session ID, primary key)
   - truck_id (truck license that owns this session)
   - in_transaction_id (reference to IN transaction)
   - out_transaction_id (reference to OUT transaction, NULL while open)
   - status (OPEN, CLOSED, FORCED)
   - created_at (when IN was submitted)
   - closed_at (when OUT was submitted, NULL if open)

3. containers_registered table (EXISTING):
   - container_id (container ID, primary key)
   - weight (tara weight in kg)
   - status (active/inactive/damaged)
   - registered_at (registration date)
"""

# ============================================================================
# 2. PSEUDOCODE: POST /weight (MAIN ENDPOINT)
# ============================================================================
"""
FUNCTION submit_weight_transaction(direction, truck, containers, bruto, produce, force=false):

  STEP 1: VALIDATE INPUT
  ─────────────────────
  IF direction NOT IN ['in', 'out', 'none']:
    RETURN error("Invalid direction")
  
  IF direction IN ['in', 'none'] AND containers IS EMPTY:
    RETURN error("Containers required for IN and NONE")
  
  IF bruto IS NOT NUMBER OR bruto < 0:
    RETURN error("Bruto must be non-negative number")
  
  SET truck = truck OR 'na'
  SET produce = produce OR 'na'

  
  STEP 2: CHECK SESSION STATE (TRUCK-RELATED LOGIC)
  ──────────────────────────────────────────────────
  IF truck != 'na':
    
    active_session = GET ACTIVE SESSION FOR truck
    
    IF direction == 'in':
      IF active_session EXISTS AND NOT force:
        RETURN error("Truck already has active IN session. Use force=true to override")
      
      IF active_session EXISTS AND force:
        CLOSE_SESSION(active_session, status='FORCED_OVERWRITE')
        UPDATE previous_in_transaction SET session_id = NULL
    
    ELSE IF direction == 'out':
      IF NOT active_session:
        RETURN error("No active IN session for this truck. Cannot submit OUT without IN")
      
      IF active_session.out_transaction_id EXISTS:
        RETURN error("Truck already has OUT for this session")
  
  ELSE:  // truck == 'na'
    IF direction == 'out':
      RETURN error("Cannot submit OUT without truck license")


  STEP 3: CALCULATE NETO
  ─────────────────────
  neto = CALCULATE_NETO(direction, bruto, containers)
  // See pseudocode SECTION 4 below


  STEP 4: STORE TRANSACTION
  ─────────────────────────
  transaction_id = INSERT INTO transactions (
    direction, truck, containers, bruto, truckTara, neto, produce, datetime
  )
  
  IF direction == 'in':
    session_id = CREATE NEW SESSION:
      INSERT INTO sessions (truck_id, in_transaction_id, status, created_at)
      VALUES (truck, transaction_id, 'OPEN', NOW())
    
    UPDATE transactions SET session_id = session_id WHERE id = transaction_id

  ELSE IF direction == 'out':
    UPDATE sessions SET out_transaction_id = transaction_id, status = 'CLOSED', closed_at = NOW()
      WHERE id = active_session.id
    
    UPDATE transactions SET session_id = active_session.id WHERE id = transaction_id

  ELSE IF direction == 'none':
    CREATE SINGLE-TRANSACTION SESSION:
      session_id = CREATE NEW SESSION:
        INSERT INTO sessions (truck_id, in_transaction_id, out_transaction_id, status, created_at, closed_at)
        VALUES (truck, transaction_id, transaction_id, 'CLOSED', NOW(), NOW())
      
      UPDATE transactions SET session_id = session_id WHERE id = transaction_id


  STEP 5: BUILD RESPONSE (API SPEC COMPLIANT)
  ────────────────────────────────────────────
  response = {
    id: str(transaction_id),
    truck: truck,
    bruto: bruto,
    neto: neto,
    message: "Transaction recorded successfully"
  }
  
  IF direction == 'out':
    ADD truckTara: bruto  // For OUT, bruto is actually the truckTara value
  
  RETURN response (201 CREATED)

END FUNCTION
"""

# ============================================================================
# 3. PSEUDOCODE: SESSION LOOKUP
# ============================================================================
"""
FUNCTION GET_ACTIVE_SESSION_FOR_TRUCK(truck_id):
  // Returns the most recent OPEN session for this truck, or NULL
  
  session = QUERY:
    SELECT * FROM sessions 
    WHERE truck_id = truck_id AND status = 'OPEN'
    ORDER BY created_at DESC
    LIMIT 1
  
  RETURN session OR NULL

END FUNCTION


FUNCTION CLOSE_SESSION(session_id, status='CLOSED'):
  // Close a session and mark its status
  
  UPDATE sessions SET status = status, closed_at = NOW()
    WHERE id = session_id
  
  RETURN TRUE

END FUNCTION
"""

# ============================================================================
# 4. PSEUDOCODE: NETO CALCULATION
# ============================================================================
"""
FUNCTION CALCULATE_NETO(direction, bruto, containers_str):
  // Returns neto weight (int) or 'na' (string)
  // neto = bruto - truckTara - sum(container_taras)
  
  LOGIC:
  ──────
  IF direction == 'out':
    // For OUT: weight input is actually truckTara, not bruto
    // Neto cannot be calculated without the original IN weight
    RETURN 'na'
  
  ELSE IF direction IN ['in', 'none']:
    // Start with bruto weight, subtract container taras
    neto = bruto
    truckTara = 0  // For IN/NONE, weight input is bruto, truck tara is assumed 0
    
    IF containers_str IS EMPTY OR containers_str IS NULL:
      // No containers to deduct
      RETURN neto
    
    ELSE:
      // Parse container IDs
      container_ids = SPLIT(containers_str, ',')
      container_ids = [cid.STRIP() for cid in container_ids]  // Remove spaces
      
      // Look up each container's tara
      FOR EACH container_id IN container_ids:
        container_tara = GET_CONTAINER_TARA(container_id)
        
        IF container_tara IS NULL:
          // Unknown container: cannot calculate neto
          RETURN 'na'
        
        ELSE:
          neto -= container_tara
      
      // All containers found, return calculated neto
      RETURN neto

END FUNCTION


FUNCTION GET_CONTAINER_TARA(container_id):
  // Returns container tara weight (int) or NULL if not found
  
  container = QUERY:
    SELECT weight FROM containers_registered
    WHERE container_id = container_id AND status = 'active'
    LIMIT 1
  
  IF container EXISTS:
    RETURN container.weight
  ELSE:
    RETURN NULL

END FUNCTION
"""

# ============================================================================
# 5. PSEUDOCODE: SESSION QUERIES
# ============================================================================
"""
FUNCTION GET_SESSION_BY_ID(session_id):
  // Retrieve complete session information
  
  session = QUERY:
    SELECT 
      s.id,
      s.truck_id,
      s.in_transaction_id,
      s.out_transaction_id,
      s.status,
      s.created_at,
      s.closed_at,
      tin.bruto AS in_bruto,
      tin.neto AS in_neto,
      tin.produce,
      tin.containers,
      tout.bruto AS out_bruto,
      tout.truckTara
    FROM sessions s
    LEFT JOIN transactions tin ON s.in_transaction_id = tin.id
    LEFT JOIN transactions tout ON s.out_transaction_id = tout.id
    WHERE s.id = session_id
  
  RETURN session

END FUNCTION


FUNCTION GET_SESSIONS_FOR_TRUCK(truck_id, from_date=NULL, to_date=NULL):
  // Retrieve all sessions for a truck in a date range
  
  FROM_DATE = from_date OR TODAY AT 00:00:00
  TO_DATE = to_date OR NOW()
  
  sessions = QUERY:
    SELECT * FROM sessions
    WHERE truck_id = truck_id
    AND created_at >= FROM_DATE
    AND created_at <= TO_DATE
    ORDER BY created_at DESC
  
  RETURN sessions

END FUNCTION


FUNCTION GET_OPEN_SESSIONS():
  // Retrieve all currently open sessions (for monitoring/debugging)
  
  sessions = QUERY:
    SELECT * FROM sessions
    WHERE status = 'OPEN'
    ORDER BY created_at ASC
  
  RETURN sessions

END FUNCTION
"""

# ============================================================================
# 6. NEW DATABASE SCHEMA
# ============================================================================
"""
ALTER TABLE transactions ADD COLUMN session_id INT DEFAULT NULL;
ALTER TABLE transactions ADD FOREIGN KEY (session_id) REFERENCES sessions(id);

CREATE TABLE sessions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  truck_id VARCHAR(50) NOT NULL,  -- 'na' for non-truck sessions
  in_transaction_id INT NOT NULL,
  out_transaction_id INT DEFAULT NULL,
  status ENUM('OPEN', 'CLOSED', 'FORCED_OVERWRITE') DEFAULT 'OPEN',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  closed_at DATETIME DEFAULT NULL,
  
  FOREIGN KEY (in_transaction_id) REFERENCES transactions(id),
  FOREIGN KEY (out_transaction_id) REFERENCES transactions(id),
  
  INDEX idx_truck_id (truck_id),
  INDEX idx_status (status),
  INDEX idx_created_at (created_at)
);

-- Update containers_registered to include status
ALTER TABLE containers_registered ADD COLUMN status ENUM('active', 'inactive', 'damaged') DEFAULT 'active';
"""

# ============================================================================
# 7. ERROR HANDLING MATRIX
# ============================================================================
"""
ERROR SCENARIO HANDLING:

┌─────────────────────────────────────────────┬──────────┬─────────────┐
│ SCENARIO                                    │ STATUS   │ ACTION      │
├─────────────────────────────────────────────┼──────────┼─────────────┤
│ IN when active session exists               │ 400 ERR  │ Reject      │
│ IN when active session exists + force=true  │ 201 OK   │ Overwrite   │
│ OUT without active IN session               │ 400 ERR  │ Reject      │
│ OUT with truck='na'                         │ 400 ERR  │ Reject      │
│ OUT when OUT already exists for session     │ 400 ERR  │ Reject      │
│ OUT with different weight than IN           │ 201 OK   │ Record      │
│ NONE always creates closed session          │ 201 OK   │ Record      │
│ Container tara unknown                      │ 201 OK   │ neto='na'   │
└─────────────────────────────────────────────┴──────────┴─────────────┘
"""

# ============================================================================
# 8. EXAMPLE SESSIONS & FLOWS
# ============================================================================
"""
EXAMPLE 1: Normal IN/OUT FLOW
─────────────────────────────

T1: POST /weight {direction:'in', truck:'TR-001', containers:'C-01,C-02', bruto:20000}
    → Session-1 created (OPEN)
    → Transaction-1 created (IN)
    → Response: {id:1, truck:TR-001, bruto:20000, neto:'na'}

T2: POST /weight {direction:'out', truck:'TR-001', bruto:4500}
    → Updates Session-1 (CLOSED)
    → Transaction-2 created (OUT)
    → Response: {id:2, truck:TR-001, bruto:0, truckTara:4500, neto:'na'}

DB State:
  sessions[1] = {truck_id:TR-001, in_transaction_id:1, out_transaction_id:2, status:CLOSED}
  transactions[1] = {id:1, session_id:1, direction:in, truck:TR-001, bruto:20000, neto:'na'}
  transactions[2] = {id:2, session_id:1, direction:out, truck:TR-001, bruto:0, truckTara:4500}


EXAMPLE 2: DUPLICATE IN (ERROR) - without force flag
──────────────────────────────────────────────────────

T1: POST /weight {direction:'in', truck:'TR-002', containers:'C-03', bruto:15000}
    → Session-2 created (OPEN)
    → Transaction-3 created (IN)
    → Response: {id:3, truck:TR-002, bruto:15000}

T2: POST /weight {direction:'in', truck:'TR-002', containers:'C-04', bruto:16000}
    → ERROR: "Truck already has active IN session. Use force=true"
    → Status: 400 BAD REQUEST


EXAMPLE 3: DUPLICATE IN (FORCED OVERRIDE)
───────────────────────────────────────────

T1: POST /weight {direction:'in', truck:'TR-003', containers:'C-05', bruto:18000}
    → Session-3 created (OPEN)
    → Transaction-4 created (IN)

T2: POST /weight {direction:'in', truck:'TR-003', containers:'C-06', bruto:19000, force:true}
    → Session-3 becomes FORCED_OVERWRITE
    → Session-4 created (OPEN)
    → Transaction-5 created (IN)
    → Previous transaction-4 becomes orphaned


EXAMPLE 4: UNKNOWN CONTAINER (NETO = 'na')
────────────────────────────────────────────

DB: containers_registered is empty for C-99

POST /weight {direction:'in', truck:'TR-004', containers:'C-99', bruto:12000}
  → CALCULATE_NETO('in', 12000, 'C-99')
    → container_tara = GET_CONTAINER_TARA('C-99')
    → container_tara = NULL (not found)
    → RETURN 'na'
  → neto = 'na'
  → Response: {id:6, truck:TR-004, bruto:12000, neto:'na'}


EXAMPLE 5: KNOWN CONTAINERS (NETO CALCULATED)
───────────────────────────────────────────────

DB: 
  containers_registered[C-10] = {weight:500}
  containers_registered[C-11] = {weight:450}

POST /weight {direction:'in', truck:'TR-005', containers:'C-10,C-11', bruto:13000}
  → CALCULATE_NETO('in', 13000, 'C-10,C-11')
    → neto = 13000
    → container_tara(C-10) = 500 → neto = 12500
    → container_tara(C-11) = 450 → neto = 12050
    → RETURN 12050
  → neto = 12050
  → Response: {id:7, truck:TR-005, bruto:13000, neto:12050}
"""

# ============================================================================
# 9. API ENDPOINTS UPDATED FOR SESSION SUPPORT
# ============================================================================
"""
POST /weight
  Existing implementation updated with session logic (see SECTION 2)

GET /session/<session_id>
  Retrieve session details with IN and OUT transactions
  Response:
  {
    id: <session_id>,
    truck: <truck_id>,
    status: OPEN|CLOSED|FORCED_OVERWRITE,
    in: {
      id: <transaction_id>,
      bruto: <int>,
      neto: <int> or 'na',
      containers: [id1, id2, ...],
      produce: <str>,
      timestamp: <iso8601>
    },
    out: {
      id: <transaction_id>,
      truckTara: <int>,
      timestamp: <iso8601>
    } or null if OPEN,
    duration: <seconds> or null if OPEN,
    deliverySize: <neto if calculated> or 'na'
  }

GET /truck/<truck_id>/sessions?from=<date>&to=<date>&status=<OPEN|CLOSED>
  Retrieve all sessions for a truck
  Response: Array of session objects

GET /sessions/open
  Retrieve all currently open sessions for monitoring/debugging
  Response: Array of open session objects
"""

# ============================================================================
# 10. VALIDATION CHECKLIST
# ============================================================================
"""
Before committing changes:

□ Session creation on IN direction
□ Session closure on OUT direction
□ Error when OUT without IN
□ Error when IN without container for IN direction
□ Neto calculation with known containers
□ Neto = 'na' with unknown containers
□ Neto = 'na' for OUT direction
□ truckTara included in response only for OUT
□ Truck license or 'na' always present in response
□ Force flag overwrite logic
□ Transaction.session_id properly linked
□ Sessions table properly indexed
□ Old transactions without session_id remain accessible
"""
