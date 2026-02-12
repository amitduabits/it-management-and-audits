# Payment Processing API - Endpoint Reference

**Version:** 2.4.0
**Base URL:** `http://localhost:5000/v1`

---

## Authentication

All protected endpoints require an API key. Pass it using one of these methods:

```
Authorization: Bearer demo_key_4eC39HqLyjWDarjtT1zdp7dc
```

or

```
X-API-Key: demo_key_4eC39HqLyjWDarjtT1zdp7dc
```

### Available Test Keys

| Key | Name | Permissions |
|-----|------|-------------|
| `demo_key_4eC39HqLyjWDarjtT1zdp7dc` | Standard | payments:read, payments:write, refunds:write |
| `demo_key_BQokikJOvBiI2HlWgH4olfQ2` | Admin | All permissions including webhooks:manage, api:admin |
| `demo_key_readonly_9f8g7h6j5k4l3m2n` | Read Only | payments:read |
| `demo_key_expired_key_do_not_use` | Expired | None (inactive) |

---

## Rate Limiting

Every authenticated request includes rate limit headers:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed in the window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |

When the limit is exceeded, the API returns `429 Too Many Requests` with a `Retry-After` header.

---

## Standard Response Headers

| Header | Description |
|--------|-------------|
| `X-Request-Id` | Unique request identifier (echoes client-supplied value if present) |
| `X-Response-Time` | Server processing time in milliseconds |
| `X-API-Version` | API version (e.g., `2024-01-15`) |

---

## Error Format

All errors follow this structure:

```json
{
  "error": {
    "type": "not_found",
    "message": "Payment 'pay_abc123' not found.",
    "status": 404
  }
}
```

Validation errors include a detailed `errors` array:

```json
{
  "error": {
    "type": "validation_error",
    "message": "The request body contains invalid parameters.",
    "status": 422,
    "errors": [
      {
        "field": "amount",
        "code": "required",
        "message": "The 'amount' field is required."
      },
      {
        "field": "currency",
        "code": "invalid_value",
        "message": "'XYZ' is not a supported currency."
      }
    ]
  }
}
```

---

## Endpoints

### Health Check

**`GET /v1/health`** -- No authentication required.

**Response 200:**
```json
{
  "status": "healthy",
  "service": "payment-api",
  "version": "2.4.0",
  "timestamp": "2025-01-15T10:30:00.000000+00:00",
  "checks": {
    "database": "connected",
    "cache": "connected",
    "queue": "connected"
  }
}
```

---

### API Info

**`GET /v1/api-info`** -- No authentication required.

**Response 200:**
```json
{
  "name": "Payment Processing API",
  "version": "2.4.0",
  "api_version": "2024-01-15",
  "environment": "test",
  "documentation_url": "https://docs.paymentapi.example.com",
  "endpoints": {
    "payments": "/v1/payments",
    "refunds": "/v1/payments/{id}/refund",
    "webhooks": "/v1/webhooks",
    "health": "/v1/health",
    "oauth": "/v1/oauth"
  },
  "supported_currencies": ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "INR"],
  "supported_payment_methods": ["card", "bank_transfer", "wallet", "crypto"]
}
```

---

### Create Payment

**`POST /v1/payments`**

**Request Headers:**
```
Authorization: Bearer demo_key_...
Content-Type: application/json
Idempotency-Key: unique-key-123  (optional)
```

**Request Body:**
```json
{
  "amount": 49.99,
  "currency": "USD",
  "description": "Order #12345 - Premium Widget",
  "customer_email": "customer@example.com",
  "payment_method": "card",
  "metadata": {
    "order_id": "12345",
    "sku": "WIDGET-PRO-001"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `amount` | number | Yes | Payment amount (positive, subject to currency min/max) |
| `currency` | string | Yes | ISO 4217 code: USD, EUR, GBP, JPY, CAD, AUD, INR |
| `description` | string | Yes | Payment description (max 500 chars) |
| `customer_email` | string | Yes | Valid email address |
| `payment_method` | string | No | `card`, `bank_transfer`, `wallet`, `crypto` (default: `card`) |
| `metadata` | object | No | Key-value pairs (max 20 keys) |

**Response 201 (Success):**
```json
{
  "id": "pay_a1b2c3d4e5f6789012345678",
  "object": "payment",
  "amount": 49.99,
  "currency": "USD",
  "description": "Order #12345 - Premium Widget",
  "customer_email": "customer@example.com",
  "payment_method": "card",
  "metadata": {"order_id": "12345"},
  "status": "completed",
  "created_at": "2025-01-15T10:30:00.000000+00:00",
  "updated_at": "2025-01-15T10:30:00.000000+00:00",
  "idempotency_key": null,
  "failure_reason": null,
  "refunded_amount": 0.0,
  "livemode": false
}
```

**Response 402 (Payment Failed):**
```json
{
  "id": "pay_...",
  "status": "failed",
  "failure_reason": "card_declined"
}
```

**Simulated Failure Triggers:**
- Amount ending in `13.00` -- card_declined
- Amount ending in `66.60` -- insufficient_funds
- Amount > 9000 ending in `00.00` -- amount_exceeds_limit

---

### Get Payment

**`GET /v1/payments/{payment_id}`**

**Response 200:**
```json
{
  "id": "pay_a1b2c3d4e5f6789012345678",
  "object": "payment",
  "amount": 49.99,
  "currency": "USD",
  "status": "completed",
  "..."
}
```

**Response 404:**
```json
{
  "error": {
    "type": "not_found",
    "message": "Payment 'pay_000...' not found.",
    "status": 404
  }
}
```

---

### List Payments

**`GET /v1/payments?page=1&per_page=10&status=completed&currency=USD`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (>= 1) |
| `per_page` | integer | 10 | Items per page (1-100) |
| `status` | string | -- | Filter by payment status |
| `currency` | string | -- | Filter by currency |

**Response 200:**
```json
{
  "object": "list",
  "data": [
    {"id": "pay_...", "amount": 49.99, "...": "..."}
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 42,
    "total_pages": 5,
    "has_more": true
  }
}
```

---

### Get Payment Status

**`GET /v1/payments/{payment_id}/status`**

**Response 200:**
```json
{
  "id": "pay_a1b2c3d4e5f6789012345678",
  "status": "completed",
  "failure_reason": null,
  "updated_at": "2025-01-15T10:30:00.000000+00:00"
}
```

---

### Cancel Payment

**`POST /v1/payments/{payment_id}/cancel`**

Only pending or processing payments can be cancelled.

**Response 200 (Cancelled):**
```json
{
  "id": "pay_...",
  "status": "cancelled",
  "..."
}
```

**Response 409 (Cannot Cancel):**
```json
{
  "error": {
    "type": "invalid_request",
    "message": "Payment 'pay_...' cannot be cancelled. Current status: 'completed'.",
    "status": 409
  }
}
```

---

### Create Refund

**`POST /v1/payments/{payment_id}/refund`**

**Request Body (optional -- omit for full refund):**
```json
{
  "amount": 25.00,
  "reason": "requested_by_customer"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `amount` | number | No | Refund amount (default: full remaining balance) |
| `reason` | string | No | One of: `requested_by_customer`, `duplicate`, `fraudulent`, `product_not_received`, `product_unacceptable`, `other` |

**Response 201:**
```json
{
  "id": "ref_a1b2c3d4e5f6789012345678",
  "object": "refund",
  "payment_id": "pay_...",
  "amount": 25.00,
  "reason": "requested_by_customer",
  "status": "completed",
  "created_at": "2025-01-15T10:35:00.000000+00:00",
  "updated_at": "2025-01-15T10:35:00.000000+00:00",
  "failure_reason": null
}
```

---

### OAuth2 Authorize

**`GET /v1/oauth/authorize`** -- No authentication required.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `client_id` | Yes | Your application's client ID |
| `redirect_uri` | Yes | Callback URL |
| `response_type` | Yes | Must be `code` |
| `scope` | No | Space-separated scopes |
| `state` | No | CSRF protection value |

**Response 200:**
```json
{
  "authorization_code": "authcode_abc123def456",
  "redirect_uri": "https://example.com/callback?code=authcode_abc123def456&state=...",
  "expires_in": 600
}
```

---

### OAuth2 Token Exchange

**`POST /v1/oauth/token`** -- No authentication required.

**Request Body (authorization_code):**
```json
{
  "grant_type": "authorization_code",
  "code": "authcode_abc123def456",
  "client_id": "my_app",
  "client_secret": "my_secret"
}
```

**Response 200:**
```json
{
  "access_token": "tok_abc123...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "rtok_def456...",
  "scope": "payments:read"
}
```

---

### Webhook Endpoints

**Register:** `POST /v1/webhooks/endpoints` (requires admin key)

```json
{
  "url": "https://example.com/webhooks/payments",
  "events": ["payment.completed", "refund.completed"]
}
```

**List:** `GET /v1/webhooks/endpoints`

**Delete:** `DELETE /v1/webhooks/endpoints/{webhook_id}`

**List Events:** `GET /v1/webhooks/events?type=payment.completed&limit=20`

**Simulate:** `POST /v1/webhooks/simulate`

```json
{
  "event_type": "payment.completed",
  "payload": {"payment": {"id": "pay_test", "amount": 99.99}}
}
```

---

### Reset Test Data

**`POST /v1/test/reset`** -- Requires admin API key.

Clears all payments, refunds, webhooks, and rate limit counters.

**Response 200:**
```json
{
  "message": "All test data has been reset.",
  "timestamp": "2025-01-15T10:40:00.000000+00:00"
}
```
