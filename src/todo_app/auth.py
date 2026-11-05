# Task T0401, T-014 extended � Spec FR-034, FR-105 � Plan Auth split
from __future__ import annotations

import os

import jwt
from fastapi import Depends, HTTPException, Request
from jwt import PyJWKClient
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidTokenError,
    PyJWKClientConnectionError,
    PyJWKClientError,
)
from sqlmodel import Session

from .database import get_db
from .models import User

JWT_ALGORITHM_ALLOWLIST: tuple[str, ...] = ("RS256",)
JWT_EXP_LEEWAY_SECONDS = 60

_jwk_clients: dict[str, PyJWKClient] = {}


def jwt_jwks_url() -> str | None:
    jwks_url = os.environ.get("JWT_JWKS_URL")
    if jwks_url:
        return jwks_url
    origin = os.environ.get("BETTER_AUTH_URL")
    if not origin:
        return None
    return origin.rstrip("/") + "/api/auth/jwks"


def jwt_issuer() -> str | None:
    return os.environ.get("JWT_ISSUER") or os.environ.get("BETTER_AUTH_URL")


def jwt_audience() -> str | None:
    return os.environ.get("JWT_AUDIENCE") or os.environ.get("BETTER_AUTH_URL")


def require_jwt_config() -> tuple[str, str, str]:
    jwks_url = jwt_jwks_url()
    issuer = jwt_issuer()
    audience = jwt_audience()
    missing: list[str] = []
    if not jwks_url:
        missing.append("JWT_JWKS_URL (or BETTER_AUTH_URL)")
    if not issuer:
        missing.append("JWT_ISSUER (or BETTER_AUTH_URL)")
    if not audience:
        missing.append("JWT_AUDIENCE (or BETTER_AUTH_URL)")
    if missing:
        raise RuntimeError(
            "Missing JWT verification configuration: "
            + ", ".join(missing)
            + ". The backend refuses to start without JWKS-based Bearer "
            "verification config (BETTER_AUTH_SECRET is frontend-only)."
        )
    return jwks_url, issuer, audience


def _jwk_client_for(jwks_url: str) -> PyJWKClient:
    client = _jwk_clients.get(jwks_url)
    if client is None:
        client = PyJWKClient(jwks_url, cooldown_duration=0)
        _jwk_clients[jwks_url] = client
    return client


def get_token_claims(request: Request):
    """Verify JWT and return claims without DB access."""
    authorization = request.headers.get("Authorization", "")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].casefold() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = parts[1]

    jwks_url, issuer, audience = require_jwt_config()

    try:
        algorithm = jwt.get_unverified_header(token).get("alg")
        if algorithm not in JWT_ALGORITHM_ALLOWLIST:
            raise HTTPException(status_code=401, detail="Invalid token")
        client = _jwk_client_for(jwks_url)
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=list(JWT_ALGORITHM_ALLOWLIST),
            leeway=JWT_EXP_LEEWAY_SECONDS,
            issuer=issuer,
            audience=audience,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except PyJWKClientConnectionError:
        raise HTTPException(status_code=503, detail="JWKS service unavailable")
    except PyJWKClientError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_path_user(user_id: str, claims = Depends(get_token_claims), db: Session = Depends(get_db)):
    """403 before any DB lookup if path user mismatches token sub."""
    try:
        sub = claims.get("sub") if isinstance(claims, dict) else getattr(claims, "sub", None)
    except Exception:
        sub = None
    if sub != user_id:
        raise HTTPException(status_code=403, detail="Path user does not match token")
    user = db.get(User, sub)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def bearer_user(request: Request, db: Session) -> User:
    claims = get_token_claims(request)
    try:
        sub = claims.get("sub") if isinstance(claims, dict) else getattr(claims, "sub", None)
    except Exception:
        sub = None
    user = db.get(User, sub)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> User:
    if not request.headers.get("Authorization"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return bearer_user(request, db)
