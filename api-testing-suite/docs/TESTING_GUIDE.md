# API Testing Guide

A practical guide to writing effective API integration tests for the Payment Processing API.

---

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Categories](#test-categories)
3. [Setting Up Your Environment](#setting-up-your-environment)
4. [Writing Tests with Pytest](#writing-tests-with-pytest)
5. [Writing Tests with Requests](#writing-tests-with-requests)
6. [Test Design Patterns](#test-design-patterns)
7. [Common Pitfalls](#common-pitfalls)
8. [Continuous Integration](#continuous-integration)

---

## Testing Philosophy

Effective API testing validates that an API:

- **Returns correct HTTP status codes** for all scenarios (2xx, 4xx, 5xx)
- **Returns well-structured responses** that match the documented schema
- **Handles invalid input gracefully** with informative error messages
- **Enforces authentication and authorization** rules correctly
- **Behaves consistently** under concurrent or repeated requests
- **Respects rate limits** and communicates them via headers

The goal is not to test every permutation but to cover the critical paths that your application depends on.

---

## Test Categories

### 1. Happy Path Tests
Verify the primary success scenario for each endpoint.

```python
def test_create_payment_success(client, auth_headers):
    """The most basic test: can we create a payment?"""
    resp = client.post("/v1/payments", json={
        "amount": 49.99,
        "currency": "USD",
        "description": "Test order",
        "customer_email": "user@example.com",
    }, headers=auth_headers)

    assert resp.status_code == 201
    data = resp.get_json()
    assert data["status"] == "completed"
    assert data["id"].startswith("pay_")
```

### 2. Validation Tests
Verify that the API rejects malformed or incomplete input.

```python
def test_missing_required_field(client, auth_headers):
    """Omit a required field and expect 422 with specific error detail."""
    resp = client.post("/v1/payments", json={
        "currency": "USD",
        "description": "No amount",
        "customer_email": "user@example.com",
    }, headers=auth_headers)

    assert resp.status_code == 422
    errors = resp.get_json()["error"]["errors"]
    assert any(e["field"] == "amount" for e in errors)
```

### 3. Authentication Tests
Verify that protected endpoints reject unauthorized requests.

```python
def test_no_api_key_returns_401(client):
    resp = client.get("/v1/payments")
    assert resp.status_code == 401

def test_invalid_key_returns_401(client):
    headers = {"Authorization": "Bearer demo_key_invalid"}
    resp = client.get("/v1/payments", headers=headers)
    assert resp.status_code == 401
```

### 4. Authorization Tests
Verify that keys with limited permissions are correctly restricted.

```python
def test_readonly_key_cannot_write(client, readonly_headers):
    resp = client.post("/v1/payments", json={...}, headers=readonly_headers)
    assert resp.status_code == 403
```

### 5. Edge Case Tests
Cover boundary conditions, race conditions, and unusual input.

```python
def test_minimum_amount(client, auth_headers):
    """USD minimum is 0.50"""
    resp = client.post("/v1/payments", json={
        "amount": 0.50,
        "currency": "USD",
        "description": "Minimum",
        "customer_email": "min@test.com",
    }, headers=auth_headers)
    assert resp.status_code == 201

def test_below_minimum_amount(client, auth_headers):
    resp = client.post("/v1/payments", json={
        "amount": 0.10,
        "currency": "USD",
        "description": "Below min",
        "customer_email": "min@test.com",
    }, headers=auth_headers)
    assert resp.status_code == 422
```

### 6. State Transition Tests
Verify that resources move through states correctly.

```python
def test_payment_lifecycle(client, auth_headers):
    # Create
    create_resp = client.post("/v1/payments", json={...}, headers=auth_headers)
    payment_id = create_resp.get_json()["id"]

    # Retrieve
    get_resp = client.get(f"/v1/payments/{payment_id}", headers=auth_headers)
    assert get_resp.get_json()["status"] == "completed"

    # Refund
    refund_resp = client.post(
        f"/v1/payments/{payment_id}/refund",
        json={"amount": 10.00},
        headers=auth_headers,
    )
    assert refund_resp.status_code == 201

    # Verify final state
    final = client.get(f"/v1/payments/{payment_id}", headers=auth_headers)
    assert final.get_json()["status"] == "partially_refunded"
```

---

## Setting Up Your Environment

### Prerequisites

- Python 3.9 or later
- pip package manager

### Installation

```bash
# Clone the repository and install dependencies
pip install -r requirements.txt

# Start the mock API server
python -m api.app
```

### Running Tests

```bash
# Run all tests with pytest
pytest tests/ -v

# Run a specific test file
pytest tests/test_payments.py -v

# Run tests matching a pattern
pytest tests/ -k "refund" -v

# Run with coverage report
pytest tests/ --cov=api --cov-report=term-missing
```

---

## Writing Tests with Pytest

### Using Fixtures

The test suite provides shared fixtures in `tests/conftest.py`:

```python
@pytest.fixture
def auth_headers():
    return {
        "Authorization": "Bearer demo_key_4eC39HqLyjWDarjtT1zdp7dc",
        "Content-Type": "application/json",
    }

@pytest.fixture
def sample_payment_data():
    return {
        "amount": 49.99,
        "currency": "USD",
        "description": "Test payment",
        "customer_email": "test@example.com",
    }
```

### Using Factory Fixtures

For tests that need a pre-created payment:

```python
def test_refund(client, auth_headers, create_completed_payment):
    payment = create_completed_payment({"amount": 100.00})
    resp = client.post(
        f"/v1/payments/{payment['id']}/refund",
        json={"amount": 50.00},
        headers=auth_headers,
    )
    assert resp.status_code == 201
```

---

## Writing Tests with Requests

For black-box testing against a running server:

```python
import requests

BASE_URL = "http://localhost:5000/v1"
HEADERS = {
    "Authorization": "Bearer demo_key_4eC39HqLyjWDarjtT1zdp7dc",
    "Content-Type": "application/json",
}

def test_create_and_retrieve():
    # Create
    payload = {
        "amount": 25.00,
        "currency": "EUR",
        "description": "Integration test",
        "customer_email": "integration@test.com",
    }
    create_resp = requests.post(f"{BASE_URL}/payments", json=payload, headers=HEADERS)
    assert create_resp.status_code == 201

    payment_id = create_resp.json()["id"]

    # Retrieve
    get_resp = requests.get(f"{BASE_URL}/payments/{payment_id}", headers=HEADERS)
    assert get_resp.status_code == 200
    assert get_resp.json()["amount"] == 25.00
```

---

## Test Design Patterns

### Arrange-Act-Assert (AAA)

```python
def test_example(client, auth_headers):
    # Arrange: set up preconditions
    payload = {"amount": 50.00, "currency": "USD", ...}

    # Act: perform the operation
    resp = client.post("/v1/payments", json=payload, headers=auth_headers)

    # Assert: verify outcomes
    assert resp.status_code == 201
    assert resp.get_json()["amount"] == 50.00
```

### Test Isolation

Each test should be independent. The `conftest.py` fixture resets all data before each test:

```python
@pytest.fixture(autouse=True)
def reset_state():
    store.reset()
    rate_limiter.reset()
    yield
```

### Parameterized Tests

Use `pytest.mark.parametrize` for testing multiple inputs:

```python
@pytest.mark.parametrize("currency", ["USD", "EUR", "GBP", "JPY"])
def test_supported_currencies(client, auth_headers, currency):
    resp = client.post("/v1/payments", json={
        "amount": 100.00,
        "currency": currency,
        "description": f"{currency} test",
        "customer_email": "test@example.com",
    }, headers=auth_headers)
    assert resp.status_code == 201
```

### Negative Testing Matrix

| Scenario | Expected Status | Error Type |
|----------|----------------|------------|
| Missing auth header | 401 | authentication_error |
| Invalid API key | 401 | authentication_error |
| Expired API key | 403 | authentication_error |
| Insufficient permissions | 403 | authorization_error |
| Missing required field | 422 | validation_error |
| Invalid field value | 422 | validation_error |
| Resource not found | 404 | not_found |
| Conflict (wrong state) | 409 | invalid_request |
| Rate limit exceeded | 429 | rate_limit_error |
| Malformed JSON body | 400 | invalid_request |

---

## Common Pitfalls

1. **Not resetting state between tests.** Tests that depend on order will produce flaky results. Always reset the data store.

2. **Hardcoding IDs.** Payment IDs are generated dynamically. Create the resource first, then use the returned ID.

3. **Ignoring response headers.** Rate limit headers, request IDs, and response times provide important metadata. Validate them.

4. **Only testing happy paths.** The majority of bugs live in error handling. Dedicate at least half your tests to negative scenarios.

5. **Testing implementation details.** Test behavior, not internal state. Use the API surface as your contract.

6. **Skipping idempotency tests.** Payment APIs must handle retries safely. Always test that duplicate requests with the same idempotency key return the same result.

---

## Continuous Integration

### Sample CI Configuration

```yaml
# .github/workflows/api-tests.yml
name: API Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --tb=short --cov=api
```

### Running in Docker

```bash
# Build and run the API
docker build -t payment-api .
docker run -d -p 5000:5000 payment-api

# Run integration tests against the container
python -m tests.test_runner
```
