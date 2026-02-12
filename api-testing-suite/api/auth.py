"""
Authentication & Authorization Module
=======================================

Provides API key validation, OAuth2 mock flow, and request
authentication middleware for the payment API.
"""

import uuid
import time
import hashlib
import hmac
from functools import wraps
from flask import request, jsonify, g


# ---------------------------------------------------------------------------
# Valid API keys for testing purposes
# ---------------------------------------------------------------------------
VALID_API_KEYS = {
    "demo_key_4eC39HqLyjWDarjtT1zdp7dc": {
        "name": "Test Key - Standard",
        "permissions": ["payments:read", "payments:write", "refunds:write"],
        "rate_limit": 100,
        "active": True,
    },
    "demo_key_BQokikJOvBiI2HlWgH4olfQ2": {
        "name": "Test Key - Admin",
        "permissions": ["payments:read", "payments:write", "refunds:write",
                        "webhooks:manage", "api:admin"],
        "rate_limit": 500,
        "active": True,
    },
    "demo_key_expired_key_do_not_use": {
        "name": "Test Key - Expired",
        "permissions": [],
        "rate_limit": 0,
        "active": False,
    },
    "demo_key_readonly_9f8g7h6j5k4l3m2n": {
        "name": "Test Key - Read Only",
        "permissions": ["payments:read"],
        "rate_limit": 50,
        "active": True,
    },
}

# ---------------------------------------------------------------------------
# OAuth2 mock tokens store
# ---------------------------------------------------------------------------
_oauth_tokens = {}
_authorization_codes = {}


def _error_response(status_code, error_type, message, param=None):
    """Generate a standardized error response."""
    body = {
        "error": {
            "type": error_type,
            "message": message,
            "status": status_code,
        }
    }
    if param:
        body["error"]["param"] = param
    return jsonify(body), status_code


def extract_api_key():
    """
    Extract API key from the request.
    Supports Bearer token in Authorization header and X-API-Key header.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    api_key_header = request.headers.get("X-API-Key", "")
    if api_key_header:
        return api_key_header.strip()

    return None


def validate_api_key(api_key):
    """Validate an API key and return the key metadata if valid."""
    if not api_key:
        return None, "missing_key"

    if api_key.startswith("sk_live_"):
        return None, "live_key_not_allowed"

    key_data = VALID_API_KEYS.get(api_key)
    if not key_data:
        return None, "invalid_key"

    if not key_data["active"]:
        return None, "key_inactive"

    return key_data, None


def require_auth(f):
    """Decorator: require valid API key authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = extract_api_key()

        if not api_key:
            return _error_response(
                401,
                "authentication_error",
                "No API key provided. Include your API key in the "
                "Authorization header using Bearer scheme, or in "
                "the X-API-Key header."
            )

        key_data, error = validate_api_key(api_key)

        if error == "live_key_not_allowed":
            return _error_response(
                403,
                "authentication_error",
                "Live API keys are not permitted in test mode. "
                "Use a test key (demo_key_...) instead."
            )

        if error == "invalid_key":
            return _error_response(
                401,
                "authentication_error",
                "Invalid API key provided. Check that your API key "
                "is correct and has not been revoked."
            )

        if error == "key_inactive":
            return _error_response(
                403,
                "authentication_error",
                "This API key has been deactivated. Please generate "
                "a new key from your dashboard."
            )

        if error == "missing_key":
            return _error_response(
                401,
                "authentication_error",
                "API key is required for this endpoint."
            )

        g.api_key = api_key
        g.key_data = key_data
        return f(*args, **kwargs)

    return decorated


def require_permission(permission):
    """Decorator: require a specific permission on the authenticated key."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            key_data = getattr(g, "key_data", None)
            if not key_data:
                return _error_response(
                    401,
                    "authentication_error",
                    "Authentication required."
                )

            if permission not in key_data.get("permissions", []):
                return _error_response(
                    403,
                    "authorization_error",
                    f"Your API key does not have the '{permission}' "
                    f"permission required for this operation. "
                    f"Current permissions: {key_data.get('permissions', [])}"
                )

            return f(*args, **kwargs)
        return decorated
    return decorator


# ---------------------------------------------------------------------------
# OAuth2 Mock Flow Endpoints
# ---------------------------------------------------------------------------

def oauth2_authorize():
    """
    Mock OAuth2 authorization endpoint.
    In a real system this would render a consent screen.
    """
    client_id = request.args.get("client_id")
    redirect_uri = request.args.get("redirect_uri")
    response_type = request.args.get("response_type", "code")
    scope = request.args.get("scope", "payments:read")
    state = request.args.get("state", "")

    if not client_id:
        return _error_response(400, "invalid_request", "client_id is required.")

    if not redirect_uri:
        return _error_response(400, "invalid_request", "redirect_uri is required.")

    if response_type != "code":
        return _error_response(
            400,
            "unsupported_response_type",
            "Only 'code' response_type is supported."
        )

    auth_code = f"authcode_{uuid.uuid4().hex[:16]}"
    _authorization_codes[auth_code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "created_at": time.time(),
        "expires_at": time.time() + 600,  # 10 minute expiry
        "used": False,
    }

    return jsonify({
        "authorization_code": auth_code,
        "redirect_uri": f"{redirect_uri}?code={auth_code}&state={state}",
        "expires_in": 600,
        "note": "In production, this would redirect the user agent to the "
                "redirect_uri. This mock returns the code directly.",
    })


def oauth2_token():
    """
    Mock OAuth2 token exchange endpoint.
    Exchanges an authorization code for an access token.
    """
    grant_type = request.form.get("grant_type") or (request.json or {}).get("grant_type")
    code = request.form.get("code") or (request.json or {}).get("code")
    client_id = request.form.get("client_id") or (request.json or {}).get("client_id")
    client_secret = request.form.get("client_secret") or (request.json or {}).get("client_secret")
    refresh_token_val = request.form.get("refresh_token") or (request.json or {}).get("refresh_token")

    if grant_type == "authorization_code":
        if not code:
            return _error_response(400, "invalid_request", "Authorization code is required.")

        auth_data = _authorization_codes.get(code)
        if not auth_data:
            return _error_response(400, "invalid_grant", "Invalid or expired authorization code.")

        if auth_data["used"]:
            return _error_response(
                400, "invalid_grant",
                "Authorization code has already been used. "
                "Codes are single-use."
            )

        if time.time() > auth_data["expires_at"]:
            return _error_response(400, "invalid_grant", "Authorization code has expired.")

        auth_data["used"] = True

        access_token = f"tok_{uuid.uuid4().hex[:32]}"
        refresh_token = f"rtok_{uuid.uuid4().hex[:32]}"

        _oauth_tokens[access_token] = {
            "client_id": auth_data["client_id"],
            "scope": auth_data["scope"],
            "created_at": time.time(),
            "expires_at": time.time() + 3600,
            "active": True,
        }

        return jsonify({
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token,
            "scope": auth_data["scope"],
        })

    elif grant_type == "refresh_token":
        if not refresh_token_val:
            return _error_response(400, "invalid_request", "refresh_token is required.")

        access_token = f"tok_{uuid.uuid4().hex[:32]}"
        refresh_token = f"rtok_{uuid.uuid4().hex[:32]}"

        _oauth_tokens[access_token] = {
            "client_id": client_id or "unknown",
            "scope": "payments:read payments:write",
            "created_at": time.time(),
            "expires_at": time.time() + 3600,
            "active": True,
        }

        return jsonify({
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token,
            "scope": "payments:read payments:write",
        })

    elif grant_type == "client_credentials":
        if not client_id or not client_secret:
            return _error_response(
                400, "invalid_request",
                "client_id and client_secret are required for "
                "client_credentials grant."
            )

        access_token = f"tok_{uuid.uuid4().hex[:32]}"
        _oauth_tokens[access_token] = {
            "client_id": client_id,
            "scope": "payments:read",
            "created_at": time.time(),
            "expires_at": time.time() + 3600,
            "active": True,
        }

        return jsonify({
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "payments:read",
        })

    else:
        return _error_response(
            400,
            "unsupported_grant_type",
            f"Grant type '{grant_type}' is not supported. "
            f"Supported types: authorization_code, refresh_token, "
            f"client_credentials."
        )


def verify_webhook_signature(payload, signature, secret):
    """
    Verify a webhook payload signature using HMAC-SHA256.
    Returns True if the signature is valid.
    """
    expected = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
