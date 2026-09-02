CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS buildings (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    address VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS floors (
    id SERIAL PRIMARY KEY,
    building_id INTEGER NOT NULL,
    name VARCHAR(150) NOT NULL,
    floor_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    asset_code VARCHAR(80) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    asset_type VARCHAR(80) NOT NULL,
    building_id INTEGER,
    floor_id INTEGER,
    manufacturer VARCHAR(150),
    model VARCHAR(150),
    installation_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'healthy',
    health_score DOUBLE PRECISION DEFAULT 100.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sensors (
    id SERIAL PRIMARY KEY,
    sensor_code VARCHAR(80) UNIQUE NOT NULL,
    asset_id INTEGER NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,
    unit VARCHAR(30),
    normal_min DOUBLE PRECISION,
    normal_max DOUBLE PRECISION,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sensor_readings (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    value DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS asset_relationships (
    id SERIAL PRIMARY KEY,
    source_asset_id INTEGER NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    target_asset_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL,
    alert_type VARCHAR(80) NOT NULL,
    severity VARCHAR(30) NOT NULL,
    message TEXT NOT NULL,
    anomaly_score DOUBLE PRECISION,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    status VARCHAR(30) DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL,
    alert_id INTEGER,
    fault_type VARCHAR(80),
    symptoms TEXT,
    root_cause TEXT,
    diagnosis_confidence DOUBLE PRECISION,
    resolution TEXT,
    resolved_at TIMESTAMP,
    outcome VARCHAR(80),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS maintenance_records (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL,
    incident_id INTEGER,
    action TEXT,
    technician_notes TEXT,
    cost DOUBLE PRECISION,
    duration_minutes INTEGER,
    result VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL,
    incident_id INTEGER,
    recommendation_type VARCHAR(80),
    recommendation TEXT,
    confidence DOUBLE PRECISION,
    estimated_cost DOUBLE PRECISION,
    estimated_saving DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS what_if_scenarios (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL,
    scenario_name VARCHAR(100) NOT NULL,
    assumptions TEXT,
    estimated_cost DOUBLE PRECISION,
    estimated_energy_change DOUBLE PRECISION,
    estimated_savings DOUBLE PRECISION,
    payback_days INTEGER,
    recommendation TEXT,
    confidence DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sensor_readings_sensor_time ON sensor_readings (sensor_id, timestamp);
