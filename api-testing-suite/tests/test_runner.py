"""
Automated Test Runner
======================

Standalone test runner that exercises the Payment API using the
``requests`` library against a running server instance. This is
designed for black-box integration testing where the API is running
as a separate process (e.g., in a container or staging environment).

Usage:
    1. Start the API server:    python -m api.app
    2. Run this script:         python -m tests.test_runner

The runner will execute all test cases, collect results, and print
a summary report.
"""

import sys
import json
import time
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = "http://localhost:5000/v1"
API_KEY = "demo_key_4eC39HqLyjWDarjtT1zdp7dc"
ADMIN_KEY = "demo_key_BQokikJOvBiI2HlWgH4olfQ2"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

ADMIN_HEADERS = {
    "Authorization": f"Bearer {ADMIN_KEY}",
    "Content-Type": "application/json",
}


class TestResult:
    def __init__(self, name, passed, message="", duration_ms=0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration_ms = duration_ms


results = []


def run_test(name, func):
    """Execute a single test function and record the result."""
    start = time.time()
    try:
        func()
        elapsed = (time.time() - start) * 1000
        results.append(TestResult(name, True, duration_ms=elapsed))
        print(f"  [PASS] {name} ({elapsed:.0f}ms)")
    except AssertionError as e:
        elapsed = (time.time() - start) * 1000
        results.append(TestResult(name, False, str(e), elapsed))
        print(f"  [FAIL] {name} -- {e}")
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        results.append(TestResult(name, False, str(e), elapsed))
        print(f"  [ERROR] {name} -- {e}")


# ===================================================================
# Test Functions
# ===================================================================

def test_health_check():
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert data["status"] == "healthy"


def test_api_info():
    resp = requests.get(f"{BASE_URL}/api-info")
    assert resp.status_code == 200
    data = resp.json()
    assert "version" in data
    assert "endpoints" in data


def test_create_payment_success():
    payload = {
        "amount": 49.99,
        "currency": "USD",
        "description": "Integration test payment",
        "customer_email": "runner@test.com",
    }
    resp = requests.post(f"{BASE_URL}/payments", json=payload, headers=HEADERS)
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["id"].startswith("pay_")
    assert data["status"] == "completed"


def test_create_payment_validation_error():
    payload = {"amount": -10, "currency": "FAKE"}
    resp = requests.post(f"{BASE_URL}/payments", json=payload, headers=HEADERS)
    assert resp.status_code == 422
    assert resp.json()["error"]["type"] == "validation_error"


def test_create_payment_no_auth():
    payload = {
        "amount": 10, "currency": "USD",
        "description": "No auth", "customer_email": "a@b.com",
    }
    resp = requests.post(f"{BASE_URL}/payments", json=payload,
                         headers={"Content-Type": "application/json"})
    assert resp.status_code == 401


def test_get_payment():
    # Create first
    payload = {
        "amount": 25.00, "currency": "USD",
        "description": "Get test", "customer_email": "get@test.com",
    }
    create_resp = requests.post(f"{BASE_URL}/payments", json=payload, headers=HEADERS)
    payment_id = create_resp.json()["id"]

    # Retrieve
    resp = requests.get(f"{BASE_URL}/payments/{payment_id}", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["id"] == payment_id


def test_get_payment_not_found():
    resp = requests.get(
        f"{BASE_URL}/payments/pay_000000000000000000000000",
        headers=HEADERS,
    )
    assert resp.status_code == 404


def test_list_payments_pagination():
    # Create a few payments
    for i in range(3):
        requests.post(f"{BASE_URL}/payments", json={
            "amount": 10 + i, "currency": "USD",
            "description": f"Page test {i}", "customer_email": "page@test.com",
        }, headers=HEADERS)

    resp = requests.get(f"{BASE_URL}/payments?page=1&per_page=2", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) <= 2
    assert "pagination" in data


def test_create_refund():
    # Create a completed payment
    create_resp = requests.post(f"{BASE_URL}/payments", json={
        "amount": 80.00, "currency": "USD",
        "description": "Refund test", "customer_email": "refund@test.com",
    }, headers=HEADERS)
    payment_id = create_resp.json()["id"]

    # Refund it
    resp = requests.post(
        f"{BASE_URL}/payments/{payment_id}/refund",
        json={"amount": 40.00, "reason": "requested_by_customer"},
        headers=HEADERS,
    )
    assert resp.status_code == 201
    assert resp.json()["amount"] == 40.0


def test_payment_status():
    create_resp = requests.post(f"{BASE_URL}/payments", json={
        "amount": 15.00, "currency": "EUR",
        "description": "Status test", "customer_email": "status@test.com",
    }, headers=HEADERS)
    payment_id = create_resp.json()["id"]

    resp = requests.get(f"{BASE_URL}/payments/{payment_id}/status", headers=HEADERS)
    assert resp.status_code == 200
    assert "status" in resp.json()


def test_idempotency():
    payload = {
        "amount": 55.00, "currency": "USD",
        "description": "Idempotency test", "customer_email": "idem@test.com",
    }
    idem_headers = {**HEADERS, "Idempotency-Key": "runner-idem-001"}

    resp1 = requests.post(f"{BASE_URL}/payments", json=payload, headers=idem_headers)
    resp2 = requests.post(f"{BASE_URL}/payments", json=payload, headers=idem_headers)

    assert resp1.json()["id"] == resp2.json()["id"]


def test_oauth_authorize():
    resp = requests.get(
        f"{BASE_URL}/oauth/authorize?"
        "client_id=runner_client&"
        "redirect_uri=https://example.com/cb&"
        "response_type=code"
    )
    assert resp.status_code == 200
    assert "authorization_code" in resp.json()


def test_oauth_token_exchange():
    # Get code
    auth_resp = requests.get(
        f"{BASE_URL}/oauth/authorize?"
        "client_id=runner_client&"
        "redirect_uri=https://example.com/cb&"
        "response_type=code"
    )
    code = auth_resp.json()["authorization_code"]

    # Exchange
    resp = requests.post(f"{BASE_URL}/oauth/token", json={
        "grant_type": "authorization_code",
        "code": code,
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_simulated_card_decline():
    payload = {
        "amount": 13.00, "currency": "USD",
        "description": "Decline", "customer_email": "decline@test.com",
    }
    resp = requests.post(f"{BASE_URL}/payments", json=payload, headers=HEADERS)
    assert resp.status_code == 402
    assert resp.json()["failure_reason"] == "card_declined"


def test_rate_limit_headers():
    resp = requests.get(f"{BASE_URL}/payments", headers=HEADERS)
    assert "X-RateLimit-Limit" in resp.headers
    assert "X-RateLimit-Remaining" in resp.headers


def test_404_json_response():
    resp = requests.get(f"{BASE_URL}/nonexistent", headers=HEADERS)
    assert resp.status_code == 404
    assert resp.json()["error"]["type"] == "not_found"


# ===================================================================
# Main Runner
# ===================================================================

def main():
    print("=" * 60)
    print("Payment API - Integration Test Runner")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print()

    # Verify API is reachable
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code != 200:
            print(f"API health check failed with status {resp.status_code}")
            sys.exit(1)
    except requests.ConnectionError:
        print(f"Cannot connect to {BASE_URL}. Is the API server running?")
        print("Start it with: python -m api.app")
        sys.exit(1)

    print("API is healthy. Running tests...\n")

    # Reset test data
    try:
        requests.post(f"{BASE_URL}/test/reset", headers=ADMIN_HEADERS)
    except Exception:
        pass

    # Run all tests
    tests = [
        ("Health Check", test_health_check),
        ("API Info", test_api_info),
        ("Create Payment - Success", test_create_payment_success),
        ("Create Payment - Validation Error", test_create_payment_validation_error),
        ("Create Payment - No Auth", test_create_payment_no_auth),
        ("Get Payment", test_get_payment),
        ("Get Payment - Not Found", test_get_payment_not_found),
        ("List Payments - Pagination", test_list_payments_pagination),
        ("Create Refund", test_create_refund),
        ("Payment Status", test_payment_status),
        ("Idempotency Key", test_idempotency),
        ("OAuth2 Authorize", test_oauth_authorize),
        ("OAuth2 Token Exchange", test_oauth_token_exchange),
        ("Simulated Card Decline", test_simulated_card_decline),
        ("Rate Limit Headers", test_rate_limit_headers),
        ("404 JSON Response", test_404_json_response),
    ]

    for name, func in tests:
        run_test(name, func)

    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    total = len(results)
    total_time = sum(r.duration_ms for r in results)

    print(f"Results: {passed}/{total} passed, {failed} failed")
    print(f"Total time: {total_time:.0f}ms")

    if failed > 0:
        print(f"\nFailed tests:")
        for r in results:
            if not r.passed:
                print(f"  - {r.name}: {r.message}")
        sys.exit(1)
    else:
        print("\nAll tests passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
