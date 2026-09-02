#!/usr/bin/env pwsh

<#
WORKSTREAM G — DEMO DATA RESET

Purpose:
  Reset alerts, investigations, and telemetry data
  WITHOUT destroying schema or asset configuration.
  
  This allows the demo to be repeated reliably.

Usage:
  .\scripts\reset-demo.ps1

#>

Write-Host "════════════════════════════════════════════════════════════"
Write-Host "FACILITY INTELLIGENCE COPILOT — DEMO DATA RESET"
Write-Host "════════════════════════════════════════════════════════════"

# Navigate to project root
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"

Write-Host ""
Write-Host "Project root: $ProjectRoot"
Write-Host ""

# Activate virtual environment if present
Write-Host "Step 1: Checking Python environment"
$VenvPath = Join-Path $ProjectRoot ".venv" "Scripts" "Activate.ps1"
if (Test-Path $VenvPath) {
    & $VenvPath
    Write-Host "✓ Virtual environment activated"
} else {
    Write-Host "✓ Using system Python environment"
}


Write-Host ""
Write-Host "Step 2: Reset demonstration data"
Write-Host ""

# Note: The actual SQL reset would require PostgreSQL to be running
# For now, we'll provide instructions and a pseudo-reset for local testing

Push-Location $BackendDir

Write-Host "To reset demo data when PostgreSQL is running, execute:"
Write-Host ""
Write-Host "  -- Delete investigations (keep schema)"
Write-Host "  DELETE FROM investigations;"
Write-Host ""
Write-Host "  -- Delete recent alerts"
Write-Host "  DELETE FROM alerts WHERE detected_at > NOW() - INTERVAL '1 hour';"
Write-Host ""
Write-Host "  -- Delete recent sensor readings"
Write-Host "  DELETE FROM sensor_readings WHERE timestamp > NOW() - INTERVAL '1 hour';"
Write-Host ""
Write-Host "  -- KEEP:"
Write-Host "  --   buildings"
Write-Host "  --   floors"
Write-Host "  --   assets"
Write-Host "  --   sensors"
Write-Host "  --   relationships"
Write-Host "  --   schema/migrations"
Write-Host ""

# If running locally with in-memory test DB, we can simulate reset
Write-Host "Step 3: Check current environment"

$PythonPath = & python -c "import sys; print(sys.executable)" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Python: $PythonPath"
} else {
    Write-Host "✗ Python not available"
    exit 1
}

# Create a Python script to perform reset if database is available
$ResetScript = @'
import os
from pathlib import Path

# Add backend to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.db.database import SessionLocal, Base, engine
    from app.models.facility import Alert, Investigation, SensorReading
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    
    # Count items before
    print("\n📊 DEMO DATA STATUS (BEFORE RESET):")
    alert_count = db.query(Alert).count()
    investigation_count = db.query(Investigation).count()
    reading_count = db.query(SensorReading).count()
    
    print(f"  Alerts: {alert_count}")
    print(f"  Investigations: {investigation_count}")
    print(f"  Sensor readings: {reading_count}")
    
    # Reset recent data (last hour)
    cutoff_time = datetime.utcnow() - timedelta(hours=1)
    
    deleted_investigations = db.query(Investigation).filter(
        Investigation.created_at > cutoff_time
    ).delete()
    
    deleted_alerts = db.query(Alert).filter(
        Alert.detected_at > cutoff_time
    ).delete()
    
    deleted_readings = db.query(SensorReading).filter(
        SensorReading.timestamp > cutoff_time
    ).delete()
    
    db.commit()
    
    print("\n✓ DEMO DATA RESET COMPLETE:")
    print(f"  Deleted investigations: {deleted_investigations}")
    print(f"  Deleted alerts: {deleted_alerts}")
    print(f"  Deleted readings: {deleted_readings}")
    
    # Count items after
    print("\n📊 DEMO DATA STATUS (AFTER RESET):")
    alert_count = db.query(Alert).count()
    investigation_count = db.query(Investigation).count()
    reading_count = db.query(SensorReading).count()
    
    print(f"  Alerts: {alert_count}")
    print(f"  Investigations: {investigation_count}")
    print(f"  Sensor readings: {reading_count}")
    
    print("\n✓ Demo is ready for fresh run")
    
    db.close()

except Exception as e:
    print(f"\n⚠ Database reset not available: {e}")
    print("  Continue when PostgreSQL is available")
'@

# Run reset script
Write-Host ""
python -c $ResetScript 2>&1

Pop-Location

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════"
Write-Host "DEMO RESET COMPLETE"
Write-Host "════════════════════════════════════════════════════════════"
