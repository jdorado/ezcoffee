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
_user_profile_cache: dict[str, tuple["PrivyUserProfile", float]] = {}


class PrivyAuthError(Exception):
    pass


class PrivyConfigError(Exception):
    pass


@dataclass(frozen=True)
class PrivyAuthContext:
    user_id: str
    email: str | None
    name: str | None
    created_at: int | None
    session_id: str | None


@dataclass(frozen=True)
class PrivyUserProfile:
    email: str | None
    name: str | None
    created_at: int | None


def _current_app_id() -> str | None:
    return os.getenv("PRIVY_APP_ID") or os.getenv("P1") or PRIVY_APP_ID


def _current_app_secret() -> str | None:
    return os.getenv("PRIVY_APP_SECRET") or os.getenv("P2") or PRIVY_APP_SECRET


def _current_api_url() -> str:
    return (os.getenv("PRIVY_API_URL") or PRIVY_API_URL or "https://auth.privy.io").rstrip("/")


def _current_issuer() -> str:
    return os.getenv("PRIVY_ISSUER") or PRIVY_ISSUER or "privy.io"


def _verification_key_override() -> str | None:
    raw = os.getenv("PRIVY_VERIFICATION_KEY") or os.getenv("PRIVY_JWT_VERIFICATION_KEY") or ""
    raw = raw.strip()
    if not raw:
        return None
    # Allow dotenv-escaped PEMs.
    if "\\n" in raw:
        raw = raw.replace("\\n", "\n")
    return raw


def _jwks_url(app_id: str) -> str:
    return f"{_current_api_url()}/api/v1/apps/{app_id}/jwks.json"


_jwks_cache: dict[str, Any] = {"keys": None, "expires_at": 0.0}


def _clear_key_caches() -> None:
    _verification_key_cache["key"] = None
    _verification_key_cache["expires_at"] = 0.0
    _jwks_cache["keys"] = None
    _jwks_cache["expires_at"] = 0.0


def _require_privy_config() -> None:
    if not _current_app_id() or not _current_app_secret():
        raise PrivyConfigError("Privy app configuration is missing.")


def _get_auth_headers() -> dict[str, str]:
    _require_privy_config()
    return {
        "Authorization": f"Bearer {_current_app_secret()}",
        "privy-app-id": _current_app_id() or "",
    }


async def _fetch_verification_key() -> str:
    _require_privy_config()
    app_id = _current_app_id() or ""
    url = f"{_current_api_url()}/api/v1/apps/{app_id}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.get(url, headers=_get_auth_headers())
        response.raise_for_status()
        payload = response.json()

    verification_key = payload.get("verification_key")
    if not isinstance(verification_key, str) or not verification_key.strip():
        raise PrivyAuthError("Privy verification key missing from response.")
    return verification_key


async def _fetch_jwks() -> dict[str, Any]:
    app_id = _current_app_id()
    if not app_id:
        raise PrivyConfigError("Privy app configuration is missing.")
    url = _jwks_url(app_id)
    # The JWKS document holds public keys only, so no secret is sent.
    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()
    if not isinstance(payload, dict) or not isinstance(payload.get("keys"), list):
        raise PrivyAuthError("Privy key set missing from response.")
    return payload


async def _get_jwks() -> dict[str, Any]:
    now = time.time()
    cached = _jwks_cache.get("keys")
    if cached and _jwks_cache.get("expires_at", 0.0) > now:
        return cached
    payload = await _fetch_jwks()
    _jwks_cache["keys"] = payload
    _jwks_cache["expires_at"] = now + VERIFICATION_KEY_TTL_SEC
    return payload


def _signing_keys_from_jwks(payload: dict[str, Any], token: str) -> list[Any]:
    try:
        kid = jwt.get_unverified_header(token).get("kid")
    except jwt.PyJWTError:
        kid = None
    try:
        key_set = jwt.PyJWKSet.from_dict(payload)
    except jwt.PyJWTError as exc:
        raise PrivyAuthError("Invalid Privy key set.") from exc
    keys = list(key_set)
    if not keys:
        raise PrivyAuthError("Invalid Privy key set.")
    if kid:
        matched = [entry for entry in keys if entry.key_id == kid]
        if matched:
            return [matched[0].key]
    if len(keys) == 1:
        return [keys[0].key]
    return [entry.key for entry in keys]


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


def _name_from_linked_accounts(payload: dict[str, Any]) -> str | None:
    accounts = payload.get("linked_accounts")
    if not isinstance(accounts, list):
        return None
    for account in accounts:
        if not isinstance(account, dict):
            continue
        value = account.get("name")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


async def get_privy_user_profile(user_id: str) -> PrivyUserProfile:
    """Read the verified Privy profile, cached to respect the provider API."""
    if not user_id:
        return PrivyUserProfile(None, None, None)
    now = time.time()
    cached = _user_profile_cache.get(user_id)
    if cached and cached[1] > now:
        return cached[0]

    _require_privy_config()
    app_id = _current_app_id() or ""
    secret = _current_app_secret() or ""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                f"{PRIVY_USER_API_URL}/users/{quote(user_id, safe='')}",
                auth=(app_id, secret),
                headers={"privy-app-id": app_id},
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError:
        # A valid access token remains sufficient if this auxiliary lookup fails.
        return PrivyUserProfile(None, None, None)

    if not isinstance(payload, dict):
        return PrivyUserProfile(None, None, None)
    created_at = payload.get("created_at")
    profile = PrivyUserProfile(
        email=_email_from_linked_accounts(payload),
        name=_name_from_linked_accounts(payload),
        created_at=created_at if isinstance(created_at, int) else None,
    )
    _user_profile_cache[user_id] = (profile, now + USER_EMAIL_TTL_SEC)
    return profile


def _decode_with_key(token: str, key: Any, app_id: str, issuer: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=["ES256"],
            audience=app_id,
            issuer=issuer,
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise PrivyAuthError("Token expired.") from exc
    except (jwt.InvalidAudienceError, jwt.InvalidIssuerError) as exc:
        raise PrivyAuthError("Invalid token.") from exc
    except jwt.InvalidSignatureError as exc:
        # Key rotation looks exactly like this; caller may refresh and retry.
        raise PrivyAuthError("Invalid signature.") from exc
    except jwt.PyJWTError as exc:
        raise PrivyAuthError("Invalid token.") from exc
    if not isinstance(payload, dict):
        raise PrivyAuthError("Invalid token.")
    return payload


async def _context_from_payload(payload: dict[str, Any]) -> PrivyAuthContext:
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        raise PrivyAuthError("Invalid token subject.")

    session_id = payload.get("sid") if isinstance(payload.get("sid"), str) else None
    email_claim = payload.get("email") or payload.get("email_address")
    email = email_claim.strip().lower() if isinstance(email_claim, str) and "@" in email_claim else None
    profile = await get_privy_user_profile(user_id)
    return PrivyAuthContext(
        user_id=user_id,
        email=email or profile.email,
        name=profile.name,
        created_at=profile.created_at,
        session_id=session_id,
    )


async def verify_privy_access_token(token: str) -> PrivyAuthContext:
    if not token or not token.strip():
        raise PrivyAuthError("Missing token.")

    app_id = _current_app_id()
    if not app_id:
        raise PrivyConfigError("Privy app configuration is missing.")
    issuer = _current_issuer()
    cleaned = token.strip()

    override = _verification_key_override()
    if override:
        return await _context_from_payload(_decode_with_key(cleaned, override, app_id, issuer))

    # Preferred path: public JWKS, no secret required. Refresh once when the
    # cached key set no longer verifies (key rotation).
    for attempt in (0, 1):
        try:
            jwks = await _get_jwks()
        except httpx.HTTPError:
            break
        except PrivyAuthError:
            break
        candidates = _signing_keys_from_jwks(jwks, cleaned)
        signature_failed = False
        for key in candidates:
            try:
                return await _context_from_payload(_decode_with_key(cleaned, key, app_id, issuer))
            except PrivyAuthError as exc:
                if str(exc) in ("Token expired.", "Invalid token.", "Invalid token subject."):
                    raise
                # "Invalid signature." (or key-set problems) may heal after
                # a refresh; other messages fall through to legacy fallback.
                signature_failed = True
                continue
        if not signature_failed:
            break
        _jwks_cache["keys"] = None
        _jwks_cache["expires_at"] = 0.0
        if attempt == 1:
            break

    # Legacy fallback: PEM verification key (requires the app secret).
    try:
        verification_key = await get_verification_key()
    except httpx.HTTPError as exc:
        raise PrivyAuthError("Could not reach Privy.") from exc
    try:
        payload = _decode_with_key(cleaned, verification_key, app_id, issuer)
    except PrivyAuthError as exc:
        # A rotated PEM stays cached for up to an hour; retry once fresh
        # before giving up, so relogin is not stuck behind stale cache.
        if str(exc) == "Invalid signature.":
            _clear_key_caches()
            try:
                verification_key = await get_verification_key()
            except httpx.HTTPError as retry_exc:
                raise PrivyAuthError("Could not reach Privy.") from retry_exc
            payload = _decode_with_key(cleaned, verification_key, app_id, issuer)
        else:
            raise
    return await _context_from_payload(payload)
