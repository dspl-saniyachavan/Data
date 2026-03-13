# Parameter Stream Data Not Saving - Troubleshooting Guide

## Issue
Data is not being saved to the `parameter_stream` table in PostgreSQL backend.

## Root Causes to Check

### 1. Table Not Created
The table might not exist in the database.

**Check:**
```bash
# Run the test script
cd /home/saniyachavani/Documents/Precision_Pulse/backend
python test_parameter_stream.py
```

**Or use the API endpoint:**
```bash
curl http://localhost:5000/api/telemetry/check-table
```

**Fix if table doesn't exist:**
```bash
python init_db.py
```

### 2. Database Connection Issue
The backend might not be connected to PostgreSQL properly.

**Check:**
- Verify PostgreSQL is running
- Check DATABASE_URL in `.env` file
- Verify credentials are correct

**Test connection:**
```bash
python test_parameter_stream.py
```

### 3. Model Not Imported
The ParameterStream model might not be imported in `app/__init__.py`.

**Verify in `/home/saniyachavani/Documents/Precision_Pulse/backend/app/__init__.py`:**
```python
from app.models.parameter_stream import ParameterStream
```

This line should be present (it is).

### 4. Endpoint Not Being Called
The `/api/telemetry/stream` endpoint might not be receiving requests.

**Test the endpoint:**
```bash
curl -X POST http://localhost:5000/api/telemetry/stream \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test-device-001",
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

**Or test insert directly:**
```bash
curl -X POST http://localhost:5000/api/telemetry/test-insert
```

### 5. Database Session Not Committing
The data might be added to session but not committed.

**Check logs for:**
- `[TELEMETRY] About to commit X records`
- `[TELEMETRY] Successfully committed X records`
- `[TELEMETRY] Error committing to database`

## Step-by-Step Debugging

### Step 1: Verify Table Exists
```bash
python test_parameter_stream.py
```

Expected output:
```
✓ parameter_stream table EXISTS
  Columns: ['id', 'parameter_id', 'value', 'timestamp', 'synced']
✓ Total records: 0
```

### Step 2: Test Direct Insert
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

### Step 3: Check Logs
Look for detailed logging output:
```bash
# In backend logs, you should see:
[TELEMETRY] /stream endpoint called
[TELEMETRY] Received data: {...}
[TELEMETRY] client_id=test-device-001, parameters count=1
[TELEMETRY] Storing param_id=1, value=25.5
[TELEMETRY] Added to session: param_id=1
[TELEMETRY] About to commit 1 records
[TELEMETRY] Successfully committed 1 records
```

### Step 4: Verify Data in Database
```bash
# Connect to PostgreSQL
psql -U postgres -d precision_pulse

# Check table
SELECT * FROM parameter_stream;

# Check record count
SELECT COUNT(*) FROM parameter_stream;
```

## Common Issues and Solutions

### Issue: "Table 'parameter_stream' does not exist"
**Solution:**
```bash
python init_db.py
```

### Issue: "Error committing to database: ..."
**Solution:**
1. Check database connection
2. Verify all required columns are provided
3. Check for constraint violations

### Issue: Data inserted but not visible
**Solution:**
1. Verify you're querying the correct database
2. Check if transaction was committed
3. Verify no rollback occurred

## Files Modified

1. **`/backend/app/models/parameter_stream.py`** - Simplified model
2. **`/backend/app/routes/telemetry_routes.py`** - Added comprehensive logging
3. **`/backend/init_db.py`** - Database initialization script
4. **`/backend/test_parameter_stream.py`** - Test script

## Next Steps

1. Run `python test_parameter_stream.py` to verify table and basic operations
2. Test the `/api/telemetry/test-insert` endpoint
3. Check backend logs for any errors
4. If still not working, check PostgreSQL connection and permissions
5. Verify the desktop app is sending data to the correct endpoint

## Desktop App Configuration

Verify the desktop app is sending to the correct endpoint:

**File:** `/home/saniyachavani/Documents/Precision_Pulse/dspl-precision-pulse-desktop/src/services/telemetry_service.py`

Should have:
```python
requests.post(
    f"{Config.BACKEND_URL}/api/telemetry/stream",
    json=payload_dict,
    timeout=5
)
```

**Verify Config.BACKEND_URL:**
Check `/home/saniyachavani/Documents/Precision_Pulse/dspl-precision-pulse-desktop/src/core/config.py`

Should be:
```python
BACKEND_URL = 'http://localhost:5000'
```
