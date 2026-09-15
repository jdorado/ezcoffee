import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx
import jwt

PRIVY_API_URL = os.getenv("PRIVY_API_URL", "https://auth.privy.io").rstrip("/")
PRIVY_USER_API_URL = os.getenv("PRIVY_USER_API_URL", "https://api.privy.io/v1").rstrip("/")
PRIVY_APP_ID = os.getenv("PRIVY_APP_ID") or os.getenv("P1")
PRIVY_APP_SECRET = os.getenv("PRIVY_APP_SECRET") or os.getenv("P2")
PRIVY_ISSUER = os.getenv("PRIVY_ISSUER", "privy.io")

VERIFICATION_KEY_TTL_SEC = int(os.getenv("PRIVY_VERIFICATION_KEY_TTL_SEC", "3600"))
USER_EMAIL_TTL_SEC = int(os.getenv("PRIVY_USER_EMAIL_TTL_SEC", "900"))

_verification_key_cache: dict[str, Any] = {"key": None, "expires_at": 0.0}
_user_email_cache: dict[str, tuple[str | None, float]] = {}


class PrivyAuthError(Exception):
    pass


class PrivyConfigError(Exception):
    pass


@dataclass(frozen=True)
class PrivyAuthContext:
    user_id: str
    email: str | None
    session_id: str | None


def _require_privy_config() -> None:
    if not PRIVY_APP_ID or not PRIVY_APP_SECRET:
        raise PrivyConfigError("Privy app configuration is missing.")


def _get_auth_headers() -> dict[str, str]:
    _require_privy_config()
    return {
        "Authorization": f"Bearer {PRIVY_APP_SECRET}",
        "privy-app-id": PRIVY_APP_ID,
    }


async def _fetch_verification_key() -> str:
    _require_privy_config()
    url = f"{PRIVY_API_URL}/api/v1/apps/{PRIVY_APP_ID}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.get(url, headers=_get_auth_headers())
        response.raise_for_status()
        payload = response.json()

    verification_key = payload.get("verification_key")
    if not isinstance(verification_key, str) or not verification_key.strip():
        raise PrivyAuthError("Privy verification key missing from response.")
    return verification_key


async def get_verification_key() -> str:
    now = time.time()
    cached_key = _verification_key_cache.get("key")
    expires_at = _verification_key_cache.get("expires_at", 0.0)
    if cached_key and expires_at > now:
        return cached_key

    key = await _fetch_verification_key()
    _verification_key_cache["key"] = key
    _verification_key_cache["expires_at"] = now + VERIFICATION_KEY_TTL_SEC
    return key


def _email_from_linked_accounts(payload: dict[str, Any]) -> str | None:
    accounts = payload.get("linked_accounts")
    if not isinstance(accounts, list):
        return None

    for account in accounts:
        if not isinstance(account, dict):
            continue
        account_type = str(account.get("type") or "").lower()
        if "email" not in account_type and "google" not in account_type:
            continue
        for field in ("address", "email"):
            value = account.get(field)
            if isinstance(value, str) and "@" in value:
                return value.strip().lower()
    return None


async def get_privy_user_email(user_id: str) -> str | None:
    """Read Privy's verified linked email, with a cache for its rate-limited API."""
    if not user_id:
        return None
    now = time.time()
    cached = _user_email_cache.get(user_id)
    if cached and cached[1] > now:
        return cached[0]

    _require_privy_config()
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                f"{PRIVY_USER_API_URL}/users/{quote(user_id, safe='')}",
                auth=(PRIVY_APP_ID, PRIVY_APP_SECRET),
                headers={"privy-app-id": PRIVY_APP_ID},
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError:
        # A valid access token remains sufficient if this auxiliary lookup fails.
        return None

    email = _email_from_linked_accounts(payload) if isinstance(payload, dict) else None
    _user_email_cache[user_id] = (email, now + USER_EMAIL_TTL_SEC)
    return email


async def verify_privy_access_token(token: str) -> PrivyAuthContext:
    if not token:
        raise PrivyAuthError("Missing token.")

    verification_key = await get_verification_key()

    try:
        payload = jwt.decode(
            token,
            verification_key,
            algorithms=["ES256"],
            audience=PRIVY_APP_ID,
            issuer=PRIVY_ISSUER,
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise PrivyAuthError("Invalid token.") from exc

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        raise PrivyAuthError("Invalid token subject.")

    session_id = payload.get("sid") if isinstance(payload.get("sid"), str) else None
    email_claim = payload.get("email") or payload.get("email_address")
    email = email_claim.strip().lower() if isinstance(email_claim, str) and "@" in email_claim else None
    if not email:
        email = await get_privy_user_email(user_id)
    return PrivyAuthContext(user_id=user_id, email=email, session_id=session_id)
