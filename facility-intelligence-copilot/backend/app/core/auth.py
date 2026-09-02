from __future__ import annotations

import hmac
import logging
from enum import Enum
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

security_bearer = HTTPBearer(auto_error=False)


class Role(str, Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


ROLE_HIERARCHY: dict[Role, set[Role]] = {
    Role.ADMIN: {Role.ADMIN, Role.OPERATOR, Role.VIEWER},
    Role.OPERATOR: {Role.OPERATOR, Role.VIEWER},
    Role.VIEWER: {Role.VIEWER},
}


class AuthenticatedUser(BaseModel):
    key_name: str = "anonymous"
    role: Role = Role.ADMIN
    facility_id: str = "FAC-001"


def _parse_api_keys() -> dict[str, tuple[str, Role]]:
    """
    Parses API_KEYS from settings.
    Format supported:
      - "key1:ADMIN,key2:OPERATOR,key3:VIEWER"
      - "key1,key2" (defaults to ADMIN)
    """
    raw = settings.api_keys or ""
    key_map: dict[str, tuple[str, Role]] = {}

    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if ":" in entry:
            parts = entry.split(":", 1)
            k = parts[0].strip()
            r_str = parts[1].strip().upper()
            role = Role[r_str] if r_str in Role.__members__ else Role.VIEWER
            key_map[k] = (k[:4] + "***", role)
        else:
            key_map[entry] = (entry[:4] + "***", Role.ADMIN)

    return key_map


def get_current_user(
    bearer_creds: Annotated[HTTPAuthorizationCredentials | None, Security(security_bearer)] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> AuthenticatedUser:
    """
    Validates API key from Authorization Bearer or X-API-Key header.
    When API_AUTH_ENABLED is False (development default), grants ADMIN role.
    """
    if not settings.api_auth_enabled:
        return AuthenticatedUser(key_name="dev-default", role=Role.ADMIN, facility_id="FAC-001")

    token = None
    if bearer_creds and bearer_creds.credentials:
        token = bearer_creds.credentials.strip()
    elif x_api_key:
        token = x_api_key.strip()

    if not token:
        logger.warning("Authentication failed: Missing API Key header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide 'Authorization: Bearer <key>' or 'X-API-Key: <key>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    key_map = _parse_api_keys()
    matched_role: Role | None = None
    matched_name: str | None = None

    for valid_key, (name, role) in key_map.items():
        if hmac.compare_digest(token.encode("utf-8"), valid_key.encode("utf-8")):
            matched_role = role
            matched_name = name
            break

    if matched_role is None:
        logger.warning("Authentication failed: Invalid API Key provided.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthenticatedUser(key_name=matched_name or "valid-key", role=matched_role, facility_id="FAC-001")


def require_role(allowed_roles: list[Role | str]):
    """
    Enforces that the authenticated user possesses one of the required roles.
    """
    normalized_roles = {
        Role[r.upper()] if isinstance(r, str) else r for r in allowed_roles
    }

    def role_checker(user: Annotated[AuthenticatedUser, Depends(get_current_user)]) -> AuthenticatedUser:
        user_effective_roles = ROLE_HIERARCHY.get(user.role, {user.role})
        if not normalized_roles.intersection(user_effective_roles):
            logger.warning(
                "Authorization failed: User role '%s' lacks required role from %s",
                user.role.value,
                [r.value for r in normalized_roles],
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Insufficient privileges for this operation.",
            )
        return user

    return role_checker
