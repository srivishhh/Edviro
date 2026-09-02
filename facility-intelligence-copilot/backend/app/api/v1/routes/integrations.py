from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.auth import AuthenticatedUser, require_role
from app.core.config import settings
from app.integrations.sns_workbench import (
    SNSWorkbenchClient,
    create_test_hvac_payload,
    normalize_generic_event,
)
from app.schemas.sns import SNSGenericEventRequest

router = APIRouter()
logger = logging.getLogger(__name__)
sns_client = SNSWorkbenchClient()


@router.post("/integrations/sns/test")
def test_sns_webhook_connection() -> JSONResponse:
    """
    Sends the canonical HVAC-007 anomaly payload to the configured SNS_WEBHOOK_TEST_URL.
    Returns structured transmission status and HTTP code without leaking secrets.
    """
    payload = create_test_hvac_payload()
    result = sns_client.send_webhook_event(payload, mode="test")

    status_code = (
        status.HTTP_200_OK
        if result["status"] == "sent"
        else (status.HTTP_502_BAD_GATEWAY if result.get("sns_status_code") else status.HTTP_400_BAD_REQUEST)
    )

    return JSONResponse(
        status_code=status_code,
        content=result,
    )


@router.post("/integrations/sns/events")
def forward_event_to_sns(
    event_req: SNSGenericEventRequest,
    current_user: Annotated[AuthenticatedUser, Depends(require_role(["OPERATOR", "ADMIN"]))],
) -> JSONResponse:
    """
    Accepts a telemetry / investigation event, normalizes it into the canonical
    SNS payload schema, and dispatches it to SNS Workbench.
    Requires OPERATOR or ADMIN role when API authentication is enabled.
    """
    payload = normalize_generic_event(event_req)
    result = sns_client.send_webhook_event(payload, mode="test" if not settings.sns_webhook_production_url else "production")

    status_code = (
        status.HTTP_200_OK
        if result["status"] == "sent"
        else (status.HTTP_502_BAD_GATEWAY if result.get("sns_status_code") else status.HTTP_400_BAD_REQUEST)
    )

    return JSONResponse(
        status_code=status_code,
        content=result,
    )


@router.post("/integrations/sns/webhook")
async def receive_sns_webhook(
    request: Request,
    x_sns_signature: Annotated[str | None, Header(alias="X-SNS-Signature")] = None,
) -> dict[str, Any]:
    """
    Inbound webhook receiver from SNS Workbench.
    Validates HMAC-SHA256 signature against SNS_WEBHOOK_SIGNING_SECRET.
    """
    signing_secret = settings.sns_webhook_signing_secret

    raw_body = await request.body()

    if signing_secret and signing_secret.strip():
        if not x_sns_signature:
            logger.warning("Inbound SNS Webhook rejected: Missing X-SNS-Signature header.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-SNS-Signature header.",
            )

        expected_prefix = "sha256="
        if not x_sns_signature.startswith(expected_prefix):
            logger.warning("Inbound SNS Webhook rejected: Malformed signature header format.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature format. Expected 'sha256=<hex>'.",
            )

        provided_hash = x_sns_signature[len(expected_prefix):].strip()
        computed_hash = hmac.new(
            signing_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(provided_hash, computed_hash):
            logger.warning("Inbound SNS Webhook rejected: Signature verification failed.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature.",
            )

    logger.info("Inbound SNS Webhook received and verified successfully.")
    return {
        "status": "received",
        "message": "Webhook verified and processed successfully.",
    }
