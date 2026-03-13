# Telemetry Unit Tests

Comprehensive unit tests for telemetry generation, timestamping, and buffering logic in PrecisionPulse Desktop.

## Test Coverage

### 1. Telemetry Generation (`TestTelemetryGeneration`)
- **test_parameters_initialization**: Verifies parameters are initialized correctly from database
- **test_parameter_values_within_bounds**: Ensures generated values stay within min/max bounds
- **test_parameter_value_variation**: Confirms parameter values change over time
- **test_parameter_structure**: Validates parameter object structure

### 2. Timestamping (`TestTimestamping`)
- **test_timestamp_format_iso8601**: Verifies timestamps use ISO8601 format
- **test_streaming_data_timestamp**: Confirms ParameterStreamingData includes timestamp
- **test_payload_timestamp_consistency**: Ensures all parameters in payload have same timestamp

### 3. Buffering (`TestBuffering`)
- **test_data_buffered_when_disconnected**: Verifies data is buffered when MQTT disconnected
- **test_buffer_contains_parameter_data**: Confirms buffered data has correct structure
- **test_flush_buffered_data**: Tests flushing buffered data to MQTT
- **test_delete_buffered_data_after_sync**: Verifies buffered data is deleted after sync

### 4. MQTT Telemetry Sender (`TestMQTTTelemetrySender`)
- **test_mqtt_payload_structure**: Validates MQTT payload structure
- **test_mqtt_payload_timestamp_format**: Confirms MQTT payload timestamp is ISO8601
- **test_mqtt_parameters_in_payload**: Verifies parameters are included in payload

### 5. Parameter Streaming Data (`TestParameterStreamingData`)
- **test_from_parameter_conversion**: Tests converting parameter dict to ParameterStreamingData
- **test_to_dict_conversion**: Validates converting ParameterStreamingData to dict

### 6. Parameter Streaming Payload (`TestParameterStreamingPayload`)
- **test_payload_creation**: Tests creating ParameterStreamingPayload
- **test_payload_to_dict**: Validates converting payload to dict

## Running Tests

### Run all tests:
```bash
cd dspl-precision-pulse-desktop
python run_tests.py
```

### Run specific test class:
```bash
python -m unittest tests.test_telemetry.TestTelemetryGeneration
```

### Run specific test:
```bash
python -m unittest tests.test_telemetry.TestTelemetryGeneration.test_parameters_initialization
```

### Run with verbose output:
```bash
python -m unittest tests.test_telemetry -v
```

## Test Structure

Each test class uses:
- **setUp()**: Initialize mock objects and test fixtures
- **tearDown()**: Cleanup (if needed)
- **Test methods**: Individual test cases

## Mock Objects

Tests use `unittest.mock` to mock:
- MQTT service and client
- Database manager
- Telemetry service dependencies

## Key Test Scenarios

### Telemetry Generation
- Parameters initialized from database
- Values generated within bounds
- Values vary over time
- Correct data structure

### Timestamping
- ISO8601 format compliance
- Timestamp included in all data
- Consistent timestamps across payload

### Buffering
- Data buffered when disconnected
- Buffered data has correct structure
- Successful flush and cleanup
- Data deleted after sync

### MQTT Publishing
- Correct payload structure
- ISO8601 timestamps
- All parameters included
- Proper JSON serialization

## Expected Output

```
test_buffer_contains_parameter_data (tests.test_telemetry.TestBuffering) ... ok
test_data_buffered_when_disconnected (tests.test_telemetry.TestBuffering) ... ok
test_delete_buffered_data_after_sync (tests.test_telemetry.TestBuffering) ... ok
test_flush_buffered_data (tests.test_telemetry.TestBuffering) ... ok
...

======================================================================
TEST SUMMARY
======================================================================
Tests run: 20
Successes: 20
Failures: 0
Errors: 0
======================================================================
```

## Troubleshooting

### Import errors
Ensure the project root is in Python path:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Mock issues
Verify mock objects have required attributes and methods defined in setUp()

### Timestamp parsing errors
Ensure datetime objects use `.isoformat()` for string representation

## Future Enhancements

- Add integration tests with real MQTT broker
- Add performance benchmarks
- Add stress tests for large parameter sets
- Add tests for error recovery scenarios
