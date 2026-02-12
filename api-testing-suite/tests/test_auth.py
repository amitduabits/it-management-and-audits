"""
Authentication & Authorization Tests
=======================================

Test coverage for API key validation, OAuth2 flows,
permission checks, and various authentication edge cases.
"""

import pytest


class TestAPIKeyAuthentication:
    """Tests for API key authentication."""

    def test_no_auth_header_returns_401(self, client, no_auth_headers):
        """AUTH-001: Request without auth header returns 401."""
        resp = client.post(
            "/v1/payments",
            json={"amount": 10, "currency": "USD",
                  "description": "test", "customer_email": "a@b.com"},
            headers=no_auth_headers,
        )
        assert resp.status_code == 401
        error = resp.get_json()["error"]
        assert error["type"] == "authentication_error"
        assert "API key" in error["message"]

    def test_invalid_api_key_returns_401(self, client):
        """AUTH-002: Invalid API key returns 401."""
        headers = {
            "Authorization": "Bearer demo_key_this_key_does_not_exist",
            "Content-Type": "application/json",
        }
        resp = client.get("/v1/payments", headers=headers)
        assert resp.status_code == 401
        assert resp.get_json()["error"]["type"] == "authentication_error"

    def test_expired_key_returns_403(self, client, expired_headers):
        """AUTH-003: Expired/inactive key returns 403."""
        resp = client.get("/v1/payments", headers=expired_headers)
        assert resp.status_code == 403
        error = resp.get_json()["error"]
        assert "deactivated" in error["message"]

    def test_live_key_rejected(self, client):
        """AUTH-004: Live API key (sk_live_) is rejected in test mode."""
        headers = {
            "Authorization": "Bearer sk_live_some_production_key",
            "Content-Type": "application/json",
        }
        resp = client.get("/v1/payments", headers=headers)
        assert resp.status_code == 403
        assert "Live API keys" in resp.get_json()["error"]["message"]

    def test_x_api_key_header_accepted(self, client):
        """AUTH-005: X-API-Key header is an alternative auth method."""
        headers = {
            "X-API-Key": "demo_key_4eC39HqLyjWDarjtT1zdp7dc",
            "Content-Type": "application/json",
        }
        resp = client.get("/v1/payments", headers=headers)
        assert resp.status_code == 200

    def test_bearer_token_format(self, client, auth_headers):
        """AUTH-006: Bearer token format works correctly."""
        resp = client.get("/v1/payments", headers=auth_headers)
        assert resp.status_code == 200

    def test_malformed_bearer_header(self, client):
        """AUTH-007: Malformed Authorization header returns 401."""
        headers = {
            "Authorization": "NotBearer some_token",
            "Content-Type": "application/json",
        }
        resp = client.get("/v1/payments", headers=headers)
        assert resp.status_code == 401


class TestPermissions:
    """Tests for role-based authorization."""

    def test_readonly_key_can_list_payments(self, client, readonly_headers):
        """AUTH-008: Read-only key can GET payments."""
        resp = client.get("/v1/payments", headers=readonly_headers)
        assert resp.status_code == 200

    def test_readonly_key_cannot_create_payment(self, client, readonly_headers):
        """AUTH-009: Read-only key cannot POST payments (403)."""
        resp = client.post("/v1/payments", json={
            "amount": 10, "currency": "USD",
            "description": "test", "customer_email": "a@b.com",
        }, headers=readonly_headers)
        assert resp.status_code == 403
        assert resp.get_json()["error"]["type"] == "authorization_error"

    def test_standard_key_cannot_manage_webhooks(self, client, auth_headers):
        """AUTH-010: Standard key lacks webhooks:manage permission."""
        resp = client.post("/v1/webhooks/endpoints", json={
            "url": "https://example.com/webhook",
        }, headers=auth_headers)
        assert resp.status_code == 403

    def test_admin_key_can_manage_webhooks(self, client, admin_headers):
        """AUTH-011: Admin key has webhooks:manage permission."""
        resp = client.post("/v1/webhooks/endpoints", json={
            "url": "https://example.com/webhook",
        }, headers=admin_headers)
        assert resp.status_code == 201

    def test_admin_key_can_reset_data(self, client, admin_headers):
        """AUTH-012: Admin key can use the test reset endpoint."""
        resp = client.post("/v1/test/reset", headers=admin_headers)
        assert resp.status_code == 200

    def test_standard_key_cannot_reset_data(self, client, auth_headers):
        """AUTH-013: Standard key cannot use test reset (403)."""
        resp = client.post("/v1/test/reset", headers=auth_headers)
        assert resp.status_code == 403


class TestOAuth2Flow:
    """Tests for the OAuth2 mock endpoints."""

    def test_authorize_returns_code(self, client):
        """AUTH-014: OAuth2 authorize returns an authorization code."""
        resp = client.get(
            "/v1/oauth/authorize?"
            "client_id=test_client&"
            "redirect_uri=https://example.com/callback&"
            "response_type=code&"
            "scope=payments:read&"
            "state=random_state_123"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "authorization_code" in data
        assert data["authorization_code"].startswith("authcode_")

    def test_authorize_missing_client_id(self, client):
        """AUTH-015: Missing client_id returns 400."""
        resp = client.get(
            "/v1/oauth/authorize?"
            "redirect_uri=https://example.com/callback&"
            "response_type=code"
        )
        assert resp.status_code == 400

    def test_authorize_missing_redirect_uri(self, client):
        """AUTH-016: Missing redirect_uri returns 400."""
        resp = client.get(
            "/v1/oauth/authorize?"
            "client_id=test_client&"
            "response_type=code"
        )
        assert resp.status_code == 400

    def test_token_exchange_success(self, client):
        """AUTH-017: Exchange authorization code for access token."""
        # Get auth code
        auth_resp = client.get(
            "/v1/oauth/authorize?"
            "client_id=test_client&"
            "redirect_uri=https://example.com/callback&"
            "response_type=code"
        )
        code = auth_resp.get_json()["authorization_code"]

        # Exchange code for token
        token_resp = client.post("/v1/oauth/token", json={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": "test_client",
        })
        assert token_resp.status_code == 200

        data = token_resp.get_json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"
        assert "refresh_token" in data
        assert data["expires_in"] == 3600

    def test_token_exchange_code_reuse_fails(self, client):
        """AUTH-018: Authorization code cannot be used twice."""
        auth_resp = client.get(
            "/v1/oauth/authorize?"
            "client_id=test_client&"
            "redirect_uri=https://example.com/callback&"
            "response_type=code"
        )
        code = auth_resp.get_json()["authorization_code"]

        # First use
        client.post("/v1/oauth/token", json={
            "grant_type": "authorization_code",
            "code": code,
        })

        # Second use should fail
        resp = client.post("/v1/oauth/token", json={
            "grant_type": "authorization_code",
            "code": code,
        })
        assert resp.status_code == 400
        assert "already been used" in resp.get_json()["error"]["message"]

    def test_client_credentials_grant(self, client):
        """AUTH-019: Client credentials grant returns token."""
        resp = client.post("/v1/oauth/token", json={
            "grant_type": "client_credentials",
            "client_id": "my_service",
            "client_secret": "my_secret",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.get_json()

    def test_refresh_token_grant(self, client):
        """AUTH-020: Refresh token grant returns new access token."""
        resp = client.post("/v1/oauth/token", json={
            "grant_type": "refresh_token",
            "refresh_token": "rtok_some_refresh_token",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_unsupported_grant_type(self, client):
        """AUTH-021: Unsupported grant type returns 400."""
        resp = client.post("/v1/oauth/token", json={
            "grant_type": "password",
        })
        assert resp.status_code == 400
        assert "not supported" in resp.get_json()["error"]["message"]


class TestPublicEndpoints:
    """Tests verifying public endpoints do not require auth."""

    def test_health_no_auth(self, client):
        """AUTH-022: Health endpoint works without authentication."""
        resp = client.get("/v1/health")
        assert resp.status_code == 200

    def test_api_info_no_auth(self, client):
        """AUTH-023: API info endpoint works without authentication."""
        resp = client.get("/v1/api-info")
        assert resp.status_code == 200
