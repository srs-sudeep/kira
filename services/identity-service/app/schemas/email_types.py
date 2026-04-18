"""Email types for local/dev — no DNS deliverability check (allows *.local, etc.)."""

from __future__ import annotations

from typing import Annotated

from email_validator import EmailNotValidError, validate_email
from pydantic import BeforeValidator


def _normalize_email_loose(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("email must be a string")
    text = value.strip()
    if not text:
        raise ValueError("email must not be empty")
    try:
        return validate_email(text, check_deliverability=False).normalized
    except EmailNotValidError as exc:
        raise ValueError(str(exc)) from exc


LooseEmailStr = Annotated[str, BeforeValidator(_normalize_email_loose)]
