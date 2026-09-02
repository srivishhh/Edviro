# Facility Simulator

This simulator publishes HVAC telemetry events to the Kafka topic `facility.telemetry`.

## Usage

```bash
python simulator.py --scenario normal
python simulator.py --scenario airflow_restriction
python simulator.py --scenario high_energy --interval 5
```

## Environment

- `KAFKA_BOOTSTRAP_SERVERS` defaults to `localhost:9092`
- `KAFKA_TELEMETRY_TOPIC` defaults to `facility.telemetry`
- `SIMULATION_INTERVAL_SECONDS` defaults to `5`
