"""
Pytest Fixtures & Configuration
=================================

Shared fixtures for the API integration test suite. Provides a
configured Flask test client, authentication headers, and helper
functions used across all test modules.
"""

import pytest
from api.app import create_app
from api.models import store
from api.rate_limiter import rate_limiter
from api.webhooks import reset_webhooks


# ---------------------------------------------------------------------------
# API Keys used in tests
# ---------------------------------------------------------------------------
STANDARD_API_KEY = "demo_key_4eC39HqLyjWDarjtT1zdp7dc"
ADMIN_API_KEY = "demo_key_BQokikJOvBiI2HlWgH4olfQ2"
EXPIRED_API_KEY = "demo_key_expired_key_do_not_use"
READONLY_API_KEY = "demo_key_readonly_9f8g7h6j5k4l3m2n"
INVALID_API_KEY = "demo_key_this_key_does_not_exist"


@pytest.fixture(scope="session")
def app():
    """Create the Flask application in testing mode."""
    application = create_app(testing=True)
    return application


@pytest.fixture(autouse=True)
def reset_state():
    """Reset all in-memory stores before each test."""
    store.reset()
    rate_limiter.reset()
    reset_webhooks()
    yield
    # Teardown: reset again
    store.reset()
    rate_limiter.reset()
    reset_webhooks()


@pytest.fixture
def client(app):
    """Provide a Flask test client."""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Standard authentication headers with write permissions."""
    return {
        "Authorization": f"Bearer {STANDARD_API_KEY}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def admin_headers():
    """Admin authentication headers with full permissions."""
    return {
        "Authorization": f"Bearer {ADMIN_API_KEY}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def readonly_headers():
    """Read-only authentication headers."""
    return {
        "Authorization": f"Bearer {READONLY_API_KEY}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def expired_headers():
    """Headers with an expired/inactive API key."""
    return {
        "Authorization": f"Bearer {EXPIRED_API_KEY}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def no_auth_headers():
    """Headers without any authentication."""
    return {
        "Content-Type": "application/json",
    }


@pytest.fixture
def sample_payment_data():
    """Valid payment creation payload."""
    return {
        "amount": 49.99,
        "currency": "USD",
        "description": "Order #12345 - Premium Widget",
        "customer_email": "customer@example.com",
        "payment_method": "card",
        "metadata": {
            "order_id": "12345",
            "sku": "WIDGET-PRO-001",
        },
    }


@pytest.fixture
def sample_large_payment_data():
    """Payment data designed to trigger failure (amount ending in 13.00)."""
    return {
        "amount": 13.00,
        "currency": "USD",
        "description": "Test failing payment",
        "customer_email": "test@example.com",
    }


@pytest.fixture
def create_completed_payment(client, auth_headers, sample_payment_data):
    """Helper that creates a completed payment and returns its data."""
    def _create(override=None):
        data = sample_payment_data.copy()
        if override:
            data.update(override)
        resp = client.post("/v1/payments", json=data, headers=auth_headers)
        return resp.get_json()
    return _create
