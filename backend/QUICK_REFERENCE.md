# Quick Reference: Parameter Stream Setup

## One-Command Setup
```bash
cd /home/saniyachavani/Documents/Precision_Pulse/backend
python setup_parameter_stream.py
```

This will:
1. Compare SQLite and PostgreSQL schemas
2. Migrate PostgreSQL table if needed
3. Verify everything works
4. Show success/failure status

## Manual Steps (if needed)

### 1. Compare Schemas
```bash
python compare_schemas.py
```

### 2. Migrate Table
```bash
python migrate_parameter_stream.py
```

### 3. Test Insert
```bash
curl -X POST http://localhost:5000/api/telemetry/test-insert
```

### 4. Check Data
```bash
curl http://localhost:5000/api/telemetry/debug
```

## Expected Schema

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| parameter_id | INTEGER | NOT NULL |
| value | FLOAT | NOT NULL |
| timestamp | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| synced | BOOLEAN | DEFAULT FALSE |

## Indexes
- `idx_parameter_stream_param_id` on `parameter_id`
- `idx_parameter_stream_timestamp` on `timestamp`
- `idx_parameter_stream_synced` on `synced`

## Files
- **Model:** `app/models/parameter_stream.py`
- **Routes:** `app/routes/telemetry_routes.py`
- **Setup:** `setup_parameter_stream.py`
- **Migration:** `migrate_parameter_stream.py`
- **Comparison:** `compare_schemas.py`
- **Docs:** `PARAMETER_STREAM_SETUP.md`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Table doesn't exist | Run `python migrate_parameter_stream.py` |
| Schema mismatch | Run `python compare_schemas.py` then migrate |
| Insert fails | Check PostgreSQL connection and run migration |
| Data not appearing | Check backend logs for `[TELEMETRY]` messages |

## Verification Checklist
- [ ] Run `python setup_parameter_stream.py`
- [ ] See "SETUP COMPLETED SUCCESSFULLY ✓"
- [ ] Run `curl http://localhost:5000/api/telemetry/debug`
- [ ] See data in response
- [ ] Start desktop app
- [ ] Verify data flows to backend
