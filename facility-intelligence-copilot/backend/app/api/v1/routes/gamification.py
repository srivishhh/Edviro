from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()

# Technician Accounts
TECHNICIAN_DB = {
    "tech-1": {
        "id": "tech-1",
        "name": "Alex Mercer",
        "role": "Senior Facility Technician",
        "credits": 2480,
        "completed": 24,
        "on_time": 21,
        "streak": 7,
        "level": "Master Specialist",
    }
}

# Transaction Ledger (Immutable)
TRANSACTIONS_DB: List[Dict] = [
    {
        "transaction_id": "tx-101",
        "technician_id": "tech-1",
        "incident_id": "inc-701",
        "amount": 150,
        "reason": "Airflow Restriction AHU-007 Resolved & Verified On-Time",
        "approved_by": "Facility Admin",
        "timestamp": "2026-09-14T16:50:00Z",
        "status": "APPROVED",
    },
    {
        "transaction_id": "tx-100",
        "technician_id": "tech-1",
        "incident_id": "inc-609",
        "amount": 80,
        "reason": "AHU-003 Filter Replacement Completed",
        "approved_by": "Facility Admin",
        "timestamp": "2026-09-12T11:00:00Z",
        "status": "APPROVED",
    },
]

# Reward Catalog
REWARDS_DB: List[Dict] = [
    {
        "id": "reward-1",
        "name": "₹500 Gift Card",
        "description": "Digital shopping voucher redeemable at major retailers.",
        "cost": 500,
        "inventory": 15,
        "active": True,
        "category": "Gift Cards",
    },
    {
        "id": "reward-2",
        "name": "Industrial Certification Voucher",
        "description": "Full sponsorship for HVAC/BMS advanced certification.",
        "cost": 1500,
        "inventory": 5,
        "active": True,
        "category": "Training",
    },
    {
        "id": "reward-3",
        "name": "Premium Tech Jacket",
        "description": "GSENSE custom branded weather-proof technical jacket.",
        "cost": 1000,
        "inventory": 8,
        "active": True,
        "category": "Merchandise",
    },
    {
        "id": "reward-4",
        "name": "Gourmet Lunch Voucher",
        "description": "Team lunch voucher for top performing week.",
        "cost": 300,
        "inventory": 20,
        "active": True,
        "category": "Perks",
    },
]

REDEMPTIONS_DB: List[Dict] = []

# Reports DB: stores resolution reports submitted by technicians
REPORTS_DB: Dict[str, Dict] = {
    "inc-609": {
        "report_id": "rep-609",
        "incident_id": "inc-609",
        "asset_id": "AHU-003",
        "technician_id": "tech-1",
        "technician_name": "Alex Mercer",
        "observed_problem": "Filter differential pressure high (>350 Pa)",
        "action_performed": "Replaced 12 pre-filter panels with new G4 rated cartridges",
        "root_cause_observed": "Particulate saturation after heavy dust storm",
        "resolution_status": "RESOLVED",
        "review_status": "APPROVED",
        "submitted_at": "2026-09-12T10:45:00Z",
        "approved_at": "2026-09-12T11:00:00Z",
        "suggested_credits": 80,
        "awarded_credits": 80,
        "admin_notes": "Verified DP returned to 85 Pa.",
    }
}

# Notification Center
NOTIFICATIONS_DB: List[Dict] = [
    {
        "id": "notif-001",
        "recipient_role": "admin",
        "type": "HIGH_ALERT",
        "title": "Airflow Restriction on AHU-007",
        "message": "Supply fan airflow reduced by 28%. Incident inc-701 created.",
        "timestamp": "2026-09-15T09:41:32Z",
        "read": False,
    },
    {
        "id": "notif-002",
        "recipient_role": "admin",
        "type": "SNS_DISPATCH",
        "title": "SNS Multi-Agent Investigation Dispatched",
        "message": "Investigation dispatched for AHU-007 airflow fault.",
        "timestamp": "2026-09-15T09:42:00Z",
        "read": False,
    },
]


# Pydantic Schemas
class ResolutionReportRequest(BaseModel):
    incident_id: str
    asset_id: str
    observed_problem: str
    action_performed: str
    root_cause_observed: str
    parts_inspected: Optional[str] = "Supply Fan, VFD Drive Belt, Dampers"
    resolution_status: str  # RESOLVED, PARTIALLY_RESOLVED, NOT_RESOLVED, ESCALATE
    additional_notes: Optional[str] = ""
    evidence: Optional[str] = "Telemetry differential pressure baseline verified"


class AdminApproveReportRequest(BaseModel):
    approved_credits: Optional[int] = None
    credits: Optional[int] = None
    admin_notes: Optional[str] = "Resolution verified by facility operations"

    def get_credits(self) -> int:
        if self.approved_credits is not None and self.approved_credits > 0:
            return self.approved_credits
        if self.credits is not None and self.credits > 0:
            return self.credits
        return 150


class AdminRejectReportRequest(BaseModel):
    reason: str


class RewardCreateRequest(BaseModel):
    name: str
    description: str
    cost: int = Field(gt=0)
    inventory: int = Field(ge=0)
    category: str = "General"


class RewardUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cost: Optional[int] = None
    inventory: Optional[int] = None
    active: Optional[bool] = None
    category: Optional[str] = None


class RedeemRequest(BaseModel):
    reward_id: str


# Technician Endpoints
@router.get("/technicians/me")
def get_current_technician():
    return TECHNICIAN_DB["tech-1"]


@router.get("/technicians/me/credits")
def get_technician_credits():
    tech = TECHNICIAN_DB["tech-1"]
    return {
        "technician_id": tech["id"],
        "available_credits": tech["credits"],
        "total_earned": sum(t["amount"] for t in TRANSACTIONS_DB if t["amount"] > 0 and t["status"] == "APPROVED"),
        "total_redeemed": sum(r["cost"] for r in REDEMPTIONS_DB if r["status"] == "COMPLETED"),
    }


@router.get("/technicians/me/transactions")
def get_technician_transactions():
    return sorted(TRANSACTIONS_DB, key=lambda x: x["timestamp"], reverse=True)


@router.post("/incidents/{incident_id}/resolution-report")
def submit_resolution_report(incident_id: str, payload: ResolutionReportRequest):
    tech = TECHNICIAN_DB["tech-1"]

    if incident_id in REPORTS_DB and REPORTS_DB[incident_id].get("review_status") == "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resolution report already submitted and approved for this incident."
        )

    # Calculate deterministic suggested credits
    base_credits = 100
    severity_bonus = 50 if "AHU-007" in payload.asset_id or "HIGH" in payload.resolution_status else 20
    quality_bonus = 30 if len(payload.action_performed) > 15 and len(payload.root_cause_observed) > 15 else 10

    if payload.resolution_status == "RESOLVED":
        suggested = base_credits + severity_bonus + quality_bonus
    elif payload.resolution_status == "PARTIALLY_RESOLVED":
        suggested = (base_credits + severity_bonus) // 2
    else:
        suggested = 0

    now_str = datetime.now(timezone.utc).isoformat()

    report_record = {
        "report_id": f"rep-{uuid4().hex[:8]}",
        "incident_id": incident_id,
        "asset_id": payload.asset_id,
        "technician_id": tech["id"],
        "technician_name": tech["name"],
        "observed_problem": payload.observed_problem,
        "action_performed": payload.action_performed,
        "root_cause_observed": payload.root_cause_observed,
        "parts_inspected": payload.parts_inspected,
        "resolution_status": payload.resolution_status,
        "review_status": "UNDER_REVIEW",  # Awaiting Admin Approval
        "additional_notes": payload.additional_notes,
        "evidence": payload.evidence,
        "submitted_at": now_str,
        "suggested_credits": suggested,
        "awarded_credits": 0,
        "admin_notes": "",
    }
    REPORTS_DB[incident_id] = report_record

    # Notify Admin
    NOTIFICATIONS_DB.append({
        "id": f"notif-{uuid4().hex[:6]}",
        "recipient_role": "admin",
        "type": "TECHNICIAN_REPORT_SUBMITTED",
        "title": f"Technician Report: {payload.asset_id}",
        "message": f"{tech['name']} submitted resolution report for incident {incident_id}. Ready for Admin Review.",
        "timestamp": now_str,
        "read": False,
    })

    return {
        "status": "SUBMITTED",
        "message": "Report submitted successfully. Awaiting Admin Review & Credit Approval.",
        "report": report_record,
    }


@router.get("/incidents/{incident_id}/resolution-report")
def get_resolution_report(incident_id: str):
    if incident_id not in REPORTS_DB:
        return {"submitted": False, "report": None}
    return {"submitted": True, "report": REPORTS_DB[incident_id]}


# Admin Report Review & Credit Approval Endpoints
@router.get("/admin/reports")
def admin_get_all_reports():
    return list(REPORTS_DB.values())


@router.post("/admin/reports/{incident_id}/approve")
def admin_approve_report(incident_id: str, payload: AdminApproveReportRequest):
    if incident_id not in REPORTS_DB:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    report = REPORTS_DB[incident_id]
    if report.get("review_status") == "APPROVED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report already approved.")

    tech = TECHNICIAN_DB["tech-1"]
    now_str = datetime.now(timezone.utc).isoformat()
    awarded_amount = payload.get_credits()

    report["review_status"] = "APPROVED"
    report["awarded_credits"] = awarded_amount
    report["admin_notes"] = payload.admin_notes or "Verified on-time resolution"
    report["approved_at"] = now_str

    # Atomically update technician credit balance and statistics
    tech["credits"] += awarded_amount
    tech["completed"] += 1
    tech["streak"] += 1

    # Record in Immutable Ledger
    tx = {
        "transaction_id": f"tx-{uuid4().hex[:8]}",
        "technician_id": tech["id"],
        "incident_id": incident_id,
        "amount": awarded_amount,
        "reason": f"Incident {report['asset_id']} Verified Resolution ({report['admin_notes']})",
        "approved_by": "Facility Administrator",
        "timestamp": now_str,
        "status": "APPROVED",
    }
    TRANSACTIONS_DB.append(tx)

    # Add real notification
    NOTIFICATIONS_DB.append({
        "id": f"notif-{uuid4().hex[:6]}",
        "recipient_role": "technician",
        "type": "CREDIT_AWARDED",
        "title": f"+{awarded_amount} Credits Transferred!",
        "message": f"Admin approved your report for {report['asset_id']}. Updated Balance: {tech['credits']} Credits.",
        "timestamp": now_str,
        "read": False,
    })

    return {
        "status": "APPROVED",
        "message": f"Report approved. +{awarded_amount} credits successfully transferred to {tech['name']}.",
        "report": report,
        "new_balance": tech["credits"],
    }


@router.post("/admin/reports/{incident_id}/reject")
def admin_reject_report(incident_id: str, payload: AdminRejectReportRequest):
    if incident_id not in REPORTS_DB:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    report = REPORTS_DB[incident_id]
    report["review_status"] = "NEEDS_REVIEW"
    report["admin_notes"] = payload.reason

    return {
        "status": "NEEDS_REVIEW",
        "message": f"Report sent back for review: {payload.reason}",
        "report": report,
    }


# Rewards Catalog & Redemption
@router.get("/rewards")
def get_rewards():
    return [r for r in REWARDS_DB if r["active"]]


@router.post("/redemptions")
def redeem_reward(payload: RedeemRequest):
    tech = TECHNICIAN_DB["tech-1"]
    reward = next((r for r in REWARDS_DB if r["id"] == payload.reward_id and r["active"]), None)

    if not reward:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reward not found or inactive")

    if reward["inventory"] <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reward is out of stock")

    if tech["credits"] < reward["cost"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient credit balance")

    tech["credits"] -= reward["cost"]
    reward["inventory"] -= 1
    now_str = datetime.now(timezone.utc).isoformat()

    redemption = {
        "redemption_id": f"red-{uuid4().hex[:8]}",
        "technician_id": tech["id"],
        "technician_name": tech["name"],
        "reward_id": reward["id"],
        "reward_name": reward["name"],
        "cost": reward["cost"],
        "timestamp": now_str,
        "status": "COMPLETED",
    }
    REDEMPTIONS_DB.append(redemption)

    tx = {
        "transaction_id": f"tx-{uuid4().hex[:8]}",
        "technician_id": tech["id"],
        "incident_id": None,
        "amount": -reward["cost"],
        "reason": f"Redeemed Reward: {reward['name']}",
        "approved_by": "System Automated Ledger",
        "timestamp": now_str,
        "status": "APPROVED",
    }
    TRANSACTIONS_DB.append(tx)

    return {
        "status": "SUCCESS",
        "message": f"Successfully redeemed {reward['name']}!",
        "redemption": redemption,
        "new_balance": tech["credits"],
    }


# Admin Management Endpoints
@router.get("/admin/rewards")
def admin_get_all_rewards():
    return REWARDS_DB


@router.post("/admin/rewards")
def admin_create_reward(payload: RewardCreateRequest):
    new_reward = {
        "id": f"reward-{uuid4().hex[:6]}",
        "name": payload.name,
        "description": payload.description,
        "cost": payload.cost,
        "inventory": payload.inventory,
        "active": True,
        "category": payload.category,
    }
    REWARDS_DB.append(new_reward)
    return new_reward


@router.patch("/admin/rewards/{reward_id}")
def admin_update_reward(reward_id: str, payload: RewardUpdateRequest):
    reward = next((r for r in REWARDS_DB if r["id"] == reward_id), None)
    if not reward:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reward not found")

    if payload.name is not None:
        reward["name"] = payload.name
    if payload.description is not None:
        reward["description"] = payload.description
    if payload.cost is not None:
        reward["cost"] = payload.cost
    if payload.inventory is not None:
        reward["inventory"] = payload.inventory
    if payload.active is not None:
        reward["active"] = payload.active
    if payload.category is not None:
        reward["category"] = payload.category

    return reward


@router.get("/admin/redemptions")
def admin_get_redemptions():
    return REDEMPTIONS_DB


@router.get("/admin/notifications")
def admin_get_notifications():
    return sorted(NOTIFICATIONS_DB, key=lambda x: x["timestamp"], reverse=True)
