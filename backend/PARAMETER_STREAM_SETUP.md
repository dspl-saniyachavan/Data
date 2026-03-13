# Parameter Stream Table Setup Guide

## Objective
Ensure the PostgreSQL `parameter_stream` table in the backend matches the SQLite `parameter_stream` table in the desktop app exactly.

## Expected Schema

Both tables should have the exact same structure:

```sql
CREATE TABLE parameter_stream (
    id INTEGER PRIMARY KEY,
    parameter_id INTEGER NOT NULL,
    value FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced BOOLEAN DEFAULT FALSE
)
```

### Indexes
```sql
CREATE INDEX idx_parameter_stream_param_id ON parameter_stream(parameter_id)
CREATE INDEX idx_parameter_stream_timestamp ON parameter_stream(timestamp)
CREATE INDEX idx_parameter_stream_synced ON parameter_stream(synced)
```

## Setup Steps

### Step 1: Compare Current Schemas
```bash
cd /home/saniyachavani/Documents/Precision_Pulse/backend
python compare_schemas.py
```

This will show:
- SQLite schema from desktop app
- PostgreSQL schema from backend
- Whether they match

### Step 2: If Schemas Don't Match - Migrate
```bash
python migrate_parameter_stream.py
```

This will:
1. Drop the existing PostgreSQL table
2. Create a new table with the exact SQLite schema
3. Create all required indexes
4. Verify the table structure
5. Test insert/query operations

### Step 3: Verify Migration Success
```bash
python compare_schemas.py
```

Should show: `✓ SCHEMAS MATCH - Tables are compatible`

### Step 4: Test Data Flow

**Test 1: Direct Insert**
```bash
curl -X POST http://localhost:5000/api/telemetry/test-insert
```

Expected response:
```json
{
  "message": "Test record inserted successfully",
  "total_records": 1
}
```

**Test 2: Stream Data**
```bash
curl -X POST http://localhost:5000/api/telemetry/stream \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test-device",
    "timestamp": "2024-01-01T12:00:00",
    "parameters": [
      {
        "id": 1,
        "parameter_id": 1,
        "name": "Temperature",
        "value": 25.5,
        "unit": "°C"
      }
    ]
  }'
```

Expected response:
```json
{
  "message": "Telemetry received",
  "count": 1
}
```

**Test 3: Check Data**
```bash
curl http://localhost:5000/api/telemetry/debug
```

Should return recent records.

## Verification Checklist

- [ ] SQLite table exists at `~/.precision_pulse/precision_pulse.db`
- [ ] PostgreSQL table exists in `precision_pulse` database
- [ ] Both tables have 5 columns: id, parameter_id, value, timestamp, synced
- [ ] All indexes are created
- [ ] Test insert succeeds
- [ ] Test stream succeeds
- [ ] Data appears in `/api/telemetry/debug`

## Files Involved

### Backend
- **Model:** `/backend/app/models/parameter_stream.py`
- **Routes:** `/backend/app/routes/telemetry_routes.py`
- **Migration:** `/backend/migrate_parameter_stream.py`
- **Comparison:** `/backend/compare_schemas.py`

### Desktop
- **Database:** `/dspl-precision-pulse-desktop/src/core/database.py`
- **Service:** `/dspl-precision-pulse-desktop/src/services/telemetry_service.py`

## Troubleshooting

### Issue: "Table does not exist"
```bash
python migrate_parameter_stream.py
```

### Issue: "Column mismatch"
```bash
python compare_schemas.py
# Then run migration if needed
python migrate_parameter_stream.py
```

### Issue: "Insert fails"
1. Check PostgreSQL is running
2. Check database connection
3. Check logs for detailed error
4. Run `python migrate_parameter_stream.py` to recreate table

### Issue: "Data not appearing"
1. Verify endpoint is being called: `curl http://localhost:5000/api/telemetry/check-table`
2. Check backend logs for `[TELEMETRY]` messages
3. Verify desktop app is sending to correct URL
4. Run `curl http://localhost:5000/api/telemetry/debug` to check data

## Desktop App Configuration

Verify desktop app is configured correctly:

**File:** `/dspl-precision-pulse-desktop/src/core/config.py`

Should have:
```python
BACKEND_URL = 'http://localhost:5000'
```

**File:** `/dspl-precision-pulse-desktop/src/services/telemetry_service.py`

Should send to:
```python
requests.post(
    f"{Config.BACKEND_URL}/api/telemetry/stream",
    json=payload_dict,
    timeout=5
)
```

## Data Flow

1. Desktop app generates telemetry data
2. Desktop stores locally in SQLite `parameter_stream` table
3. Desktop sends to backend via `/api/telemetry/stream`
4. Backend stores in PostgreSQL `parameter_stream` table
5. Frontend queries backend for latest data

## Success Criteria

✓ Both tables have identical schema
✓ Data inserts successfully
✓ Data persists in database
✓ Data can be queried
✓ Desktop and backend tables stay in sync
