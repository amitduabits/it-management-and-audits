"""
Payment Endpoint Tests
========================

Comprehensive test coverage for payment creation, retrieval, listing,
status checking, cancellation, and refund workflows.

Covers:
    - Happy path scenarios
    - Input validation / error handling
    - Authentication & authorization
    - Edge cases (idempotency, pagination, filtering)
    - Refund logic
"""

import pytest
import json


class TestCreatePayment:
    """Tests for POST /v1/payments"""

    def test_create_payment_success(self, client, auth_headers, sample_payment_data):
        """TC-001: Create a payment with valid data returns 201."""
        resp = client.post("/v1/payments", json=sample_payment_data, headers=auth_headers)
        assert resp.status_code == 201

        data = resp.get_json()
        assert data["id"].startswith("pay_")
        assert data["amount"] == 49.99
        assert data["currency"] == "USD"
        assert data["status"] == "completed"
        assert data["customer_email"] == "customer@example.com"
        assert data["object"] == "payment"
        assert data["livemode"] is False

    def test_create_payment_all_currencies(self, client, auth_headers):
        """TC-002: Payments can be created in all supported currencies."""
        currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "INR"]
        for currency in currencies:
            payload = {
                "amount": 100.00,
                "currency": currency,
                "description": f"Test {currency} payment",
                "customer_email": "test@example.com",
            }
            resp = client.post("/v1/payments", json=payload, headers=auth_headers)
            assert resp.status_code == 201, f"Failed for {currency}"
            assert resp.get_json()["currency"] == currency

    def test_create_payment_missing_amount(self, client, auth_headers):
        """TC-003: Missing amount returns 422 with specific error."""
        payload = {
            "currency": "USD",
            "description": "Test",
            "customer_email": "test@example.com",
        }
        resp = client.post("/v1/payments", json=payload, headers=auth_headers)
        assert resp.status_code == 422

        errors = resp.get_json()["error"]["errors"]
        amount_errors = [e for e in errors if e["field"] == "amount"]
        assert len(amount_errors) == 1
        assert amount_errors[0]["code"] == "required"

    def test_create_payment_negative_amount(self, client, auth_headers):
        """TC-004: Negative amount returns 422."""
        payload = {
            "amount": -50.00,
            "currency": "USD",
            "description": "Negative test",
            "customer_email": "test@example.com",
        }
        resp = client.post("/v1/payments", json=payload, headers=auth_headers)
        assert resp.status_code == 422

        errors = resp.get_json()["error"]["errors"]
        assert any(e["code"] == "invalid_value" for e in errors)

    def test_create_payment_amount_below_minimum(self, client, auth_headers):
        """TC-005: Amount below currency minimum returns 422."""
        payload = {
            "amount": 0.10,
            "currency": "USD",
            "description": "Below min",
            "customer_email": "test@example.com",
        }
        resp = client.post("/v1/payments", json=payload, headers=auth_headers)
        assert resp.status_code == 422

        errors = resp.get_json()["error"]["errors"]
        assert any(e["code"] == "amount_too_small" for e in errors)

    def test_create_payment_invalid_currency(self, client, auth_headers):
        """TC-006: Unsupported currency returns 422."""
        payload = {
            "amount": 50.00,
            "currency": "XYZ",
            "description": "Bad currency",
            "customer_email": "test@example.com",
        }
        resp = client.post("/v1/payments", json=payload, headers=auth_headers)
        assert resp.status_code == 422

        errors = resp.get_json()["error"]["errors"]
        assert any(e["field"] == "currency" for e in errors)

    def test_create_payment_invalid_email(self, client, auth_headers):
        """TC-007: Malformed email returns 422."""
        payload = {
            "amount": 25.00,
            "currency": "USD",
            "description": "Bad email test",
            "customer_email": "not-an-email",
        }
        resp = client.post("/v1/payments", json=payload, headers=auth_headers)
        assert resp.status_code == 422

        errors = resp.get_json()["error"]["errors"]
        assert any(e["field"] == "customer_email" for e in errors)

    def test_create_payment_invalid_payment_method(self, client, auth_headers):
        """TC-008: Invalid payment method returns 422."""
        payload = {
            "amount": 25.00,
            "currency": "USD",
            "description": "Bad method",
            "customer_email": "test@example.com",
            "payment_method": "carrier_pigeon",
        }
        resp = client.post("/v1/payments", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_create_payment_empty_body(self, client, auth_headers):
        """TC-009: Empty request body returns 400."""
        resp = client.post(
            "/v1/payments",
            data="",
            headers={**auth_headers, "Content-Type": "text/plain"},
        )
        assert resp.status_code == 400

    def test_create_payment_simulated_decline(self, client, auth_headers):
        """TC-010: Amount ending in 13.00 triggers card decline (402)."""
        payload = {
            "amount": 13.00,
            "currency": "USD",
            "description": "Decline test",
            "customer_email": "test@example.com",
        }
        resp = client.post("/v1/payments", json=payload, headers=auth_headers)
        assert resp.status_code == 402

        data = resp.get_json()
        assert data["status"] == "failed"
        assert data["failure_reason"] == "card_declined"

    def test_create_payment_idempotency(self, client, auth_headers, sample_payment_data):
        """TC-011: Idempotency key returns same response on retry."""
        headers = {**auth_headers, "Idempotency-Key": "idem-key-12345"}

        resp1 = client.post("/v1/payments", json=sample_payment_data, headers=headers)
        resp2 = client.post("/v1/payments", json=sample_payment_data, headers=headers)

        assert resp1.status_code == 201
        assert resp2.status_code == 200

        data1 = resp1.get_json()
        data2 = resp2.get_json()
        assert data1["id"] == data2["id"]
        assert resp2.headers.get("X-Idempotent-Replayed") == "true"

    def test_create_payment_with_metadata(self, client, auth_headers):
        """TC-012: Payment metadata is stored and returned correctly."""
        payload = {
            "amount": 75.50,
            "currency": "EUR",
            "description": "Metadata test",
            "customer_email": "meta@example.com",
            "metadata": {
                "order_id": "ORD-999",
                "campaign": "summer_sale",
                "priority": True,
            },
        }
        resp = client.post("/v1/payments", json=payload, headers=auth_headers)
        assert resp.status_code == 201

        data = resp.get_json()
        assert data["metadata"]["order_id"] == "ORD-999"
        assert data["metadata"]["priority"] is True

    def test_create_payment_description_too_long(self, client, auth_headers):
        """TC-013: Description over 500 chars returns 422."""
        payload = {
            "amount": 10.00,
            "currency": "USD",
            "description": "x" * 501,
            "customer_email": "test@example.com",
        }
        resp = client.post("/v1/payments", json=payload, headers=auth_headers)
        assert resp.status_code == 422


class TestGetPayment:
    """Tests for GET /v1/payments/<id>"""

    def test_get_payment_success(self, client, auth_headers, create_completed_payment):
        """TC-014: Retrieve an existing payment by ID."""
        payment = create_completed_payment()
        payment_id = payment["id"]

        resp = client.get(f"/v1/payments/{payment_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["id"] == payment_id

    def test_get_payment_not_found(self, client, auth_headers):
        """TC-015: Non-existent payment ID returns 404."""
        resp = client.get(
            "/v1/payments/pay_000000000000000000000000",
            headers=auth_headers,
        )
        assert resp.status_code == 404
        assert resp.get_json()["error"]["type"] == "not_found"

    def test_get_payment_invalid_id_format(self, client, auth_headers):
        """TC-016: Malformed payment ID returns 400."""
        resp = client.get("/v1/payments/not-a-valid-id", headers=auth_headers)
        assert resp.status_code == 400
        assert resp.get_json()["error"]["type"] == "invalid_request"


class TestListPayments:
    """Tests for GET /v1/payments"""

    def test_list_payments_empty(self, client, auth_headers):
        """TC-017: Empty store returns empty list with pagination."""
        resp = client.get("/v1/payments", headers=auth_headers)
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["object"] == "list"
        assert data["data"] == []
        assert data["pagination"]["total"] == 0

    def test_list_payments_pagination(self, client, auth_headers, sample_payment_data):
        """TC-018: Pagination returns correct page size and metadata."""
        # Create 5 payments
        for i in range(5):
            payload = sample_payment_data.copy()
            payload["amount"] = 10.00 + i
            client.post("/v1/payments", json=payload, headers=auth_headers)

        resp = client.get("/v1/payments?page=1&per_page=2", headers=auth_headers)
        assert resp.status_code == 200

        data = resp.get_json()
        assert len(data["data"]) == 2
        assert data["pagination"]["total"] == 5
        assert data["pagination"]["has_more"] is True
        assert data["pagination"]["total_pages"] == 3

    def test_list_payments_filter_by_status(self, client, auth_headers):
        """TC-019: Filtering by status returns correct subset."""
        # Create a successful payment
        client.post("/v1/payments", json={
            "amount": 50.00, "currency": "USD",
            "description": "Success", "customer_email": "a@b.com",
        }, headers=auth_headers)

        # Create a failed payment (amount 13.00 triggers decline)
        client.post("/v1/payments", json={
            "amount": 13.00, "currency": "USD",
            "description": "Fail", "customer_email": "a@b.com",
        }, headers=auth_headers)

        resp = client.get("/v1/payments?status=completed", headers=auth_headers)
        data = resp.get_json()
        assert all(p["status"] == "completed" for p in data["data"])

    def test_list_payments_invalid_page(self, client, auth_headers):
        """TC-020: Non-numeric page parameter returns 422."""
        resp = client.get("/v1/payments?page=abc", headers=auth_headers)
        assert resp.status_code == 422


class TestPaymentStatus:
    """Tests for GET /v1/payments/<id>/status"""

    def test_check_status_success(self, client, auth_headers, create_completed_payment):
        """TC-021: Status endpoint returns compact status info."""
        payment = create_completed_payment()
        resp = client.get(
            f"/v1/payments/{payment['id']}/status",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "completed"
        assert "id" in data
        assert "updated_at" in data


class TestCancelPayment:
    """Tests for POST /v1/payments/<id>/cancel"""

    def test_cancel_completed_payment_fails(self, client, auth_headers, create_completed_payment):
        """TC-022: Cancelling a completed payment returns 409."""
        payment = create_completed_payment()
        resp = client.post(
            f"/v1/payments/{payment['id']}/cancel",
            headers=auth_headers,
        )
        assert resp.status_code == 409
        assert resp.get_json()["error"]["type"] == "invalid_request"


class TestRefunds:
    """Tests for POST /v1/payments/<id>/refund"""

    def test_full_refund_success(self, client, auth_headers, create_completed_payment):
        """TC-023: Full refund of completed payment returns 201."""
        payment = create_completed_payment()
        resp = client.post(
            f"/v1/payments/{payment['id']}/refund",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 201

        refund = resp.get_json()
        assert refund["object"] == "refund"
        assert refund["amount"] == payment["amount"]
        assert refund["status"] == "completed"

    def test_partial_refund(self, client, auth_headers, create_completed_payment):
        """TC-024: Partial refund for a subset of the payment amount."""
        payment = create_completed_payment({"amount": 100.00})
        resp = client.post(
            f"/v1/payments/{payment['id']}/refund",
            json={"amount": 30.00},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.get_json()["amount"] == 30.00

        # Verify payment status updated
        status_resp = client.get(
            f"/v1/payments/{payment['id']}",
            headers=auth_headers,
        )
        assert status_resp.get_json()["status"] == "partially_refunded"

    def test_refund_exceeds_available_amount(self, client, auth_headers, create_completed_payment):
        """TC-025: Refund larger than payment amount returns 400."""
        payment = create_completed_payment({"amount": 50.00})
        resp = client.post(
            f"/v1/payments/{payment['id']}/refund",
            json={"amount": 999.99},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_refund_failed_payment(self, client, auth_headers):
        """TC-026: Cannot refund a failed payment (409)."""
        # Create a failed payment
        resp = client.post("/v1/payments", json={
            "amount": 13.00, "currency": "USD",
            "description": "Will fail", "customer_email": "a@b.com",
        }, headers=auth_headers)
        payment_id = resp.get_json()["id"]

        refund_resp = client.post(
            f"/v1/payments/{payment_id}/refund",
            json={},
            headers=auth_headers,
        )
        assert refund_resp.status_code == 409

    def test_double_full_refund_fails(self, client, auth_headers, create_completed_payment):
        """TC-027: Second full refund after first returns 409."""
        payment = create_completed_payment()

        # First refund succeeds
        client.post(
            f"/v1/payments/{payment['id']}/refund",
            json={},
            headers=auth_headers,
        )

        # Second refund should fail (payment is now refunded)
        resp = client.post(
            f"/v1/payments/{payment['id']}/refund",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 409


class TestResponseHeaders:
    """Tests for standard response headers."""

    def test_request_id_header(self, client, auth_headers, sample_payment_data):
        """TC-028: X-Request-Id header is present in responses."""
        resp = client.post("/v1/payments", json=sample_payment_data, headers=auth_headers)
        assert "X-Request-Id" in resp.headers

    def test_custom_request_id_echoed(self, client, auth_headers, sample_payment_data):
        """TC-029: Custom X-Request-Id is echoed back."""
        custom_id = "my-custom-req-id-abc"
        headers = {**auth_headers, "X-Request-Id": custom_id}
        resp = client.post("/v1/payments", json=sample_payment_data, headers=headers)
        assert resp.headers.get("X-Request-Id") == custom_id

    def test_response_time_header(self, client):
        """TC-030: X-Response-Time header is included."""
        resp = client.get("/v1/health")
        assert "X-Response-Time" in resp.headers

    def test_api_version_header(self, client):
        """TC-031: X-API-Version header is present."""
        resp = client.get("/v1/health")
        assert resp.headers.get("X-API-Version") == "2024-01-15"


class TestHealthAndInfo:
    """Tests for utility endpoints."""

    def test_health_check(self, client):
        """TC-032: Health endpoint returns 200 with service info."""
        resp = client.get("/v1/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_api_info(self, client):
        """TC-033: API info returns version and endpoint list."""
        resp = client.get("/v1/api-info")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["version"] == "2.4.0"
        assert "endpoints" in data

    def test_404_returns_json(self, client):
        """TC-034: Unknown path returns JSON 404 error."""
        resp = client.get("/v1/nonexistent")
        assert resp.status_code == 404
        assert resp.get_json()["error"]["type"] == "not_found"
