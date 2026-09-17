import os
from dataclasses import dataclass
from typing import Any

import httpx


class TypeSafeConfigError(RuntimeError):
    pass


class TypeSafeError(RuntimeError):
    pass


@dataclass(frozen=True)
class TypeSafeSettings:
    api_key: str
    model: str
    base_url: str
    timeout_seconds: float

    @classmethod
    def from_env(cls) -> "TypeSafeSettings":
        api_key = os.getenv("TYPESAFE_API_KEY", "").strip()
        if not api_key:
            raise TypeSafeConfigError("TYPESAFE_API_KEY is required for fast next-shot recommendations.")
        try:
            timeout_seconds = float(os.getenv("TYPESAFE_TIMEOUT_SECONDS", "15"))
        except ValueError as exc:
            raise TypeSafeConfigError("TYPESAFE_TIMEOUT_SECONDS must be a number.") from exc
        if not 1 <= timeout_seconds <= 60:
            raise TypeSafeConfigError("TYPESAFE_TIMEOUT_SECONDS must be between 1 and 60.")
        return cls(api_key, os.getenv("TYPESAFE_MODEL", "jev-latest").strip() or "jev-latest",
                   os.getenv("TYPESAFE_BASE_URL", "https://api.typesafe.ai/v1").rstrip("/"), timeout_seconds)


def build_payload(state: dict[str, Any], candidates: dict[str, dict[str, Any]], settings: TypeSafeSettings) -> dict[str, Any]:
    return {
        "model": settings.model,
        "state": state,
        "questions": {"next_shot": {
            "type": "choice",
            "instructions": (
                "Choose the single best next recipe to dial in this coffee. Use all supplied shots, "
                "prioritize explicit taste, balance, outcome, rating, choking, and locked/reference signals, "
                "the coffee's explicit roast age, and the owner's optional guidance for this next shot. "
                "Prefer changing one variable and choose only from the supplied candidates. "
                "Do not judge success from measurements alone."
            ),
            "criteria": {key: {"change": value["label"], "recipe": value["plan"]} for key, value in candidates.items()},
        }},
    }


async def typesafe_choice(state: dict[str, Any], candidates: dict[str, dict[str, Any]]) -> tuple[str, float, str]:
    settings = TypeSafeSettings.from_env()
    try:
        async with httpx.AsyncClient(timeout=settings.timeout_seconds) as client:
            response = await client.post(f"{settings.base_url}/systemone",
                headers={"Authorization": f"Bearer {settings.api_key}", "Content-Type": "application/json"},
                json=build_payload(state, candidates, settings))
    except httpx.HTTPError as exc:
        raise TypeSafeError("Could not reach TypeSafe.") from exc
    if not response.is_success:
        raise TypeSafeError(f"TypeSafe request failed with status {response.status_code}.")
    try:
        payload = response.json(); answer = payload["answers"]["next_shot"]
        choice = answer["choice"]; confidence = float(answer["confidence"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TypeSafeError("TypeSafe returned an invalid recommendation.") from exc
    if choice not in candidates or not 0 <= confidence <= 1:
        raise TypeSafeError("TypeSafe returned an invalid recommendation.")
    return choice, confidence, str(payload.get("model", settings.model))
