from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class RagDocument(BaseModel):
    doc_id: str
    incident_id: str
    asset_id: str
    document_type: str  # ANOMALY, INVESTIGATION, X_RAY, TECHNICIAN_REPORT, MAINTENANCE, RESOLUTION, SOP_MANUAL
    timestamp: str
    severity: str
    fault_type: str
    title: str
    content: str
    metadata: Dict[str, Any]


# Authoritative Facility & LBNL Knowledge Base
FACILITY_KNOWLEDGE_BASE: List[RagDocument] = [
    RagDocument(
        doc_id="rag-doc-001",
        incident_id="inc-701",
        asset_id="AHU-007",
        document_type="X_RAY",
        timestamp="2026-09-14T14:30:00Z",
        severity="HIGH",
        fault_type="AIRFLOW_RESTRICTION",
        title="AHU-007 Supply Airflow Restriction Diagnosis",
        content="Differential pressure sensor across supply fan indicated 28% airflow reduction below 10,000 CFM baseline. SNS Multi-Agent investigation isolated fault to VFD drive belt slippage and guide vane mechanical restriction. Recommended immediate belt tensioning and bearing inspection.",
        metadata={"building": "Building 74", "floor": "Floor 2", "confidence": "0.94", "status": "VERIFIED"}
    ),
    RagDocument(
        doc_id="rag-doc-002",
        incident_id="inc-701",
        asset_id="AHU-007",
        document_type="TECHNICIAN_REPORT",
        timestamp="2026-09-14T16:45:00Z",
        severity="HIGH",
        fault_type="AIRFLOW_RESTRICTION",
        title="AHU-007 Verified Resolution Report by Alex Mercer",
        content="Technician Alex Mercer inspected supply fan plenum. Observed loose VFD drive belt with 35mm deflection. Re-tensioned drive belt to manufacturer spec (12mm deflection), cleaned inlet guide vanes, and lubricated motor bearings. Airflow returned to 9,850 CFM (98.5% baseline). Resolution verified on-time.",
        metadata={"technician": "Alex Mercer", "hours_spent": 1.5, "parts_replaced": "None (re-tensioned)", "credits_awarded": 150}
    ),
    RagDocument(
        doc_id="rag-doc-003",
        incident_id="inc-609",
        asset_id="AHU-003",
        document_type="MAINTENANCE",
        timestamp="2026-09-12T10:15:00Z",
        severity="MEDIUM",
        fault_type="FILTER_PRESSURE_HIGH",
        title="AHU-003 Filter Bank Saturation & Replacement",
        content="Filter differential pressure exceeded 350 Pa limit. Pre-filter and final HEPA filter banks were saturated with particulate matter. Technicians replaced 12 pre-filter panels and verified DP dropped back to 85 Pa under normal fan speed.",
        metadata={"building": "Building 74", "floor": "Floor 2", "technician": "Sarah Jenkins", "credits_awarded": 80}
    ),
    RagDocument(
        doc_id="rag-doc-004",
        incident_id="inc-512",
        asset_id="CHILLER-001",
        document_type="INVESTIGATION",
        timestamp="2026-08-28T08:20:00Z",
        severity="HIGH",
        fault_type="EVAPORATOR_APPROACH_HIGH",
        title="CHILLER-001 High Evaporator Approach Temperature",
        content="Evaporator approach temperature reached 4.2°C (limit: 2.0°C), causing 15% efficiency penalty on chiller compressor. Root cause isolated to condenser tube scale buildup. Mechanical brushing and descaling chemical flush performed.",
        metadata={"building": "Central Plant", "floor": "Basement", "cop_impact": "-0.6", "status": "CLOSED"}
    ),
    RagDocument(
        doc_id="rag-doc-005",
        incident_id="inc-408",
        asset_id="AHU-002",
        document_type="RESOLUTION",
        timestamp="2026-08-15T11:00:00Z",
        severity="MEDIUM",
        fault_type="DAMPER_STUCK_OPEN",
        title="AHU-002 Outdoor Air Damper Actuator Re-alignment",
        content="Outdoor air damper was stuck 100% open during peak outdoor cooling conditions (34°C ambient), overloading chilled water coil. Actuator linkage was disengaged. Actuator arm re-secured, stroke recalibrated from 0-10V control signal.",
        metadata={"building": "Building 74", "floor": "Floor 1", "energy_waste_kw": 18.5, "status": "VERIFIED"}
    ),
    RagDocument(
        doc_id="rag-doc-006",
        incident_id="inc-302",
        asset_id="AHU-001",
        document_type="ANOMALY",
        timestamp="2026-07-20T09:30:00Z",
        severity="LOW",
        fault_type="SENSOR_DRIFT_TEMP",
        title="AHU-001 Supply Air Temperature Sensor Bias",
        content="LBNL dataset sensor bias test identified +4.0°C positive offset on SAT sensor, causing false economizer cycle locks. Sensor replaced with calibrated 10k Type II thermistor.",
        metadata={"building": "Building 74", "floor": "Floor 1", "offset_deg_c": 4.0, "status": "CLOSED"}
    ),
    RagDocument(
        doc_id="rag-doc-007",
        incident_id="sop-101",
        asset_id="FACILITY-WIDE",
        document_type="SOP_MANUAL",
        timestamp="2026-01-10T00:00:00Z",
        severity="INFO",
        fault_type="GENERAL_OPERATING_PROCEDURE",
        title="Standard Operating Procedure: Airflow & VFD Diagnostics",
        content="When supply airflow drops below 80% nominal while fan speed command is >90%: 1. Inspect static pressure sensor and pitot tube alignment. 2. Verify belt tension (ideal deflection 10-15mm). 3. Check inlet guide vanes and fire dampers for unintended closure. 4. Log findings and submit resolution report for admin sign-off.",
        metadata={"category": "Standard Operating Procedure", "author": "Facility Engineering"}
    ),
    RagDocument(
        doc_id="rag-doc-008",
        incident_id="sop-102",
        asset_id="FACILITY-WIDE",
        document_type="SOP_MANUAL",
        timestamp="2026-01-15T00:00:00Z",
        severity="INFO",
        fault_type="CHILLED_WATER_VALVE_LEAKAGE",
        title="LBNL Fault Diagnostic Rule: Cooling Coil Valve Leakage",
        content="If chilled water valve command is 0% but temperature drop across the coil (MAT - SAT) is > 3°F under fan operation, the cooling coil valve is leaking or mechanically stuck. Inspect actuator 24VAC control signal and valve seat seal.",
        metadata={"category": "LBNL FDD Rule", "source": "LBNL Single-Duct AHU Study"}
    ),
]


class FacilityRagService:
    def __init__(self, documents: Optional[List[RagDocument]] = None):
        self.documents = documents or FACILITY_KNOWLEDGE_BASE

    def search(self, query: str, top_k: int = 3) -> List[RagDocument]:
        query_tokens = set(re.findall(r'\w+', query.lower()))
        if not query_tokens:
            return []

        scored_docs = []
        for doc in self.documents:
            doc_text = f"{doc.title} {doc.content} {doc.asset_id} {doc.fault_type} {doc.incident_id} {doc.document_type}".lower()
            doc_tokens = set(re.findall(r'\w+', doc_text))
            
            overlap = query_tokens.intersection(doc_tokens)
            score = len(overlap)

            if any(token in doc.asset_id.lower() for token in query_tokens):
                score += 5
            if any(token in doc.incident_id.lower() for token in query_tokens):
                score += 5
            if any(token in doc.fault_type.lower() for token in query_tokens):
                score += 4

            if score > 0:
                scored_docs.append((score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:top_k]]

    def answer_query(self, query: str) -> Dict[str, Any]:
        matched_docs = self.search(query, top_k=3)

        if not matched_docs:
            return {
                "query": query,
                "answer": "NO MATCHING FACILITY RECORD FOUND in the historical intelligence knowledge base for your search terms. Try searching for 'AHU-007', 'airflow', 'filter', 'chiller', 'damper', or 'SOP'.",
                "sources": [],
                "grounded": False,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        primary_doc = matched_docs[0]
        sources = [
            {
                "doc_id": d.doc_id,
                "incident_id": d.incident_id,
                "asset_id": d.asset_id,
                "document_type": d.document_type,
                "severity": d.severity,
                "timestamp": d.timestamp,
                "title": d.title,
                "fault_type": d.fault_type,
            }
            for d in matched_docs
        ]

        q_lower = query.lower()
        if "ahu-007" in q_lower or "inc-701" in q_lower or "airflow" in q_lower:
            answer_text = (
                f"Historical records for **{primary_doc.asset_id}** ({primary_doc.incident_id}): "
                f"On {primary_doc.timestamp[:10]}, an **AIRFLOW_RESTRICTION** fault occurred due to VFD belt slippage (35mm deflection). "
                f"Technician Alex Mercer re-tensioned the belt to 12mm and lubricated bearings, successfully restoring airflow from 72% to 98.5% (9,850 CFM). "
                f"The resolution earned 150 technician credits upon admin approval."
            )
        elif "ahu-003" in q_lower or "filter" in q_lower:
            answer_text = (
                f"Historical records for **{primary_doc.asset_id}** ({primary_doc.incident_id}): "
                f"On {primary_doc.timestamp[:10]}, high filter differential pressure (>350 Pa) was diagnosed. "
                f"Technician Sarah Jenkins replaced 12 pre-filter panels, returning DP to 85 Pa."
            )
        elif "chiller" in q_lower or "inc-512" in q_lower:
            answer_text = (
                f"Historical records for **{primary_doc.asset_id}** ({primary_doc.incident_id}): "
                f"High evaporator approach temperature (4.2°C) was resolved via mechanical tube brushing and descaling chemical flush."
            )
        elif "damper" in q_lower or "ahu-002" in q_lower:
            answer_text = (
                f"Historical records for **{primary_doc.asset_id}** ({primary_doc.incident_id}): "
                f"Outdoor air damper was jammed 100% open during high ambient temperatures. The actuator linkage was re-secured and calibrated."
            )
        elif "sop" in q_lower or "procedure" in q_lower or "manual" in q_lower:
            answer_text = (
                f"Facility Operating Guidance (**{primary_doc.title}**): "
                f"{primary_doc.content}"
            )
        else:
            answer_text = (
                f"Based on historical facility intelligence (**{primary_doc.title}** - {primary_doc.incident_id}):\n\n"
                f"{primary_doc.content}"
            )

        return {
            "query": query,
            "answer": answer_text,
            "sources": sources,
            "grounded": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
