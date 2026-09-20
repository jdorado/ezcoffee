import json
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import httpx
import jwt
from fastapi import Header, HTTPException


def _private_text(path_value: str) -> str:
    path = Path(path_value)
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError("Secret path must be an absolute regular file")
    if path.stat().st_mode & 0o077:
        raise ValueError("Secret file must be owner-only")
    return path.read_text().strip()


def binding_for(principal_id: str) -> dict:
    registry_path = os.getenv("EZ_BINDINGS_FILE", "")
    try:
        registry = json.loads(_private_text(registry_path))
        if registry.get("version") != 1 or not isinstance(registry.get("bindings"), list):
            raise ValueError("Invalid binding registry")
        binding = next(
            item for item in registry["bindings"]
            if item.get("principalId") == principal_id and not item.get("revoked")
        )
        parsed = urlparse(binding["url"])
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
            raise ValueError("Local development Ez endpoint required")
        if not Path(binding["tokenFile"]).is_absolute():
            raise ValueError("Absolute token file required")
        return binding
    except (OSError, ValueError, KeyError, StopIteration, TypeError) as error:
        raise HTTPException(503, "Chat is not connected for this account.") from error


async def call(binding: dict, method: str, path: str, body: dict | None = None) -> dict:
    try:
        token = _private_text(binding["tokenFile"])
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.request(
                method,
                binding["url"].rstrip("/") + path,
                headers={"Authorization": f"Bearer {token}"},
                json=body,
            )
        if response.status_code == 404:
            raise HTTPException(404, "Ez run not found.")
        if response.status_code == 409:
            raise HTTPException(409, "The request key already has different content.")
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise ValueError("Ez response must be an object")
        return result
    except HTTPException:
        raise
    except (OSError, ValueError, httpx.HTTPError) as error:
        raise HTTPException(503, "Ez is unavailable.") from error


async def verified_binding(principal_id: str) -> dict:
    """Resolve the private binding and prove it still belongs to this owner."""
    binding = binding_for(principal_id)
    # Entries created against a shared personal runtime carry that runtime's
    # installation owner (e.g. a Telegram owner id); entries without one fall
    # back to the principal itself. Either way the live registration must
    # match the bound entry — never browser input.
    expected_owner = binding.get("ownerId") or principal_id
    registration = await call(binding, "GET", "/v1/registration")
    binding_id = registration.get("bindingId")
    if registration.get("ownerId") != expected_owner or not isinstance(binding_id, str) or not binding_id:
        raise HTTPException(503, "Chat binding does not match this account.")
    return {**binding, "bindingId": binding_id}


COFFEE_AGENT_CAPABILITY_SECRET = os.getenv("COFFEE_AGENT_CAPABILITY_SECRET", "").strip()
COFFEE_AGENT_API_BASE_URL = os.getenv("COFFEE_AGENT_API_BASE_URL", "").rstrip("/")
AGENT_PERMISSIONS = frozenset({"coffees:write", "shots:write", "records:delete"})


@dataclass(frozen=True)
class AgentCapability:
    account_id: str
    job_id: str
    permissions: frozenset[str]


def _agent_capability_secret() -> str:
    if len(COFFEE_AGENT_CAPABILITY_SECRET) < 32:
        raise HTTPException(503, "Coffee agent capabilities require a strong configured secret.")
    return COFFEE_AGENT_CAPABILITY_SECRET


def mint_agent_capability(
    *, account_id: str, job_id: str, permissions: set[str], expires_in_minutes: int = 20,
) -> str:
    """Mint a capability for one admitted Ez run, never for a browser client."""
    secret = _agent_capability_secret()
    issued = datetime.now(UTC)
    return jwt.encode({
        "iss": "ezcoffee-api",
        "aud": "ezcoffee-agent",
        "sub": account_id,
        "job_id": job_id,
        "permissions": sorted(permissions),
        "iat": issued,
        "exp": issued + timedelta(minutes=expires_in_minutes),
        "jti": secrets.token_urlsafe(18),
    }, secret, algorithm="HS256")


async def require_agent_capability(authorization: str | None = Header(default=None)) -> AgentCapability:
    secret = _agent_capability_secret()
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Agent capability required.")
    try:
        claims = jwt.decode(
            authorization.removeprefix("Bearer "),
            secret,
            algorithms=["HS256"], audience="ezcoffee-agent", issuer="ezcoffee-api",
        )
    except jwt.PyJWTError as error:
        raise HTTPException(401, "Agent capability is invalid or expired.") from error
    account_id, job_id, permissions = claims.get("sub"), claims.get("job_id"), claims.get("permissions")
    if not all(isinstance(value, str) and value for value in (account_id, job_id)):
        raise HTTPException(401, "Agent capability is invalid.")
    if not isinstance(permissions, list) or not permissions or any(not isinstance(value, str) or not value for value in permissions):
        raise HTTPException(401, "Agent capability is invalid.")
    return AgentCapability(account_id, job_id, frozenset(permissions))


def require_agent_request(capability: AgentCapability, request_id: str) -> None:
    if not secrets.compare_digest(request_id, capability.job_id):
        raise HTTPException(403, "This agent capability does not match the request.")


def require_agent_permission(capability: AgentCapability, permission: str) -> None:
    if permission not in capability.permissions:
        raise HTTPException(403, "This agent run does not have the required coffee permission.")


def agent_api_base_url() -> str | None:
    """Accept only an operator-supplied HTTP(S) origin without userinfo."""
    value = COFFEE_AGENT_API_BASE_URL.strip()
    if not value or any(character.isspace() for character in value):
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        return None
    return value


def agent_run_context(account_id: str, request_id: str) -> dict | None:
    """Opaque data for the coffee Ez plugin; never sent to or stored by the browser."""
    api_base_url = agent_api_base_url()
    if not COFFEE_AGENT_CAPABILITY_SECRET or not api_base_url:
        return None
    return {"plugins": {"coffee": {
        "api_base_url": api_base_url,
        "capability": mint_agent_capability(
            account_id=account_id, job_id=request_id, permissions=set(AGENT_PERMISSIONS),
        ),
    }}}
