"""
Payment Processing API - Flask Application
=============================================

A mock payment processing API designed for integration testing.
Implements realistic payment flows, authentication, rate limiting,
pagination, refunds, webhooks, and comprehensive error handling.

Run with:
    python -m api.app
    # or
    flask --app api.app run --port 5000
"""

import os
import time
from datetime import datetime, timezone

from flask import Flask, request, jsonify, g

from api.models import Payment, Refund, store
from api.auth import (
    require_auth, require_permission,
    oauth2_authorize, oauth2_token,
    extract_api_key, validate_api_key,
)
from api.validators import (
    validate_payment_creation,
    validate_refund_request,
    validate_pagination_params,
)
from api.rate_limiter import rate_limit_middleware, rate_limiter
from api.webhooks import webhooks_bp, create_webhook_event, reset_webhooks


def create_app(testing=False):
    """Application factory."""
    app = Flask(__name__)
    app.config["TESTING"] = testing

    # Register webhook blueprint
    app.register_blueprint(webhooks_bp, url_prefix="/v1")

    # ------------------------------------------------------------------
    # Error handlers
    # ------------------------------------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "error": {
                "type": "not_found",
                "message": (
                    f"The requested resource was not found. "
                    f"Verify the URL path and HTTP method. "
                    f"Requested: {request.method} {request.path}"
                ),
                "status": 404,
            }
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({
            "error": {
                "type": "method_not_allowed",
                "message": (
                    f"HTTP method '{request.method}' is not allowed "
                    f"for '{request.path}'. Check the API documentation "
                    f"for supported methods."
                ),
                "status": 405,
            }
        }), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({
            "error": {
                "type": "internal_server_error",
                "message": "An unexpected error occurred on the server. "
                           "Please try again later.",
                "status": 500,
            }
        }), 500

    # ------------------------------------------------------------------
    # Middleware: set request timing and common headers
    # ------------------------------------------------------------------
    @app.before_request
    def before_request():
        g.request_start = time.time()
        # Pre-authenticate for routes that need it
        api_key = extract_api_key()
        if api_key:
            key_data, _ = validate_api_key(api_key)
            if key_data:
                g.api_key = api_key
                g.key_data = key_data

    @app.after_request
    def after_request(response):
        response.headers["X-Request-Id"] = request.headers.get(
            "X-Request-Id", f"req_{int(time.time() * 1000)}"
        )
        elapsed = time.time() - getattr(g, "request_start", time.time())
        response.headers["X-Response-Time"] = f"{elapsed * 1000:.1f}ms"
        response.headers["X-API-Version"] = "2024-01-15"
        return response

    # ==================================================================
    # HEALTH & INFO ENDPOINTS
    # ==================================================================

    @app.route("/v1/health", methods=["GET"])
    def health_check():
        """Health check endpoint -- no authentication required."""
        return jsonify({
            "status": "healthy",
            "service": "payment-api",
            "version": "2.4.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "database": "connected",
                "cache": "connected",
                "queue": "connected",
            },
        })

    @app.route("/v1/api-info", methods=["GET"])
    def api_info():
        """Return metadata about the API."""
        return jsonify({
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
                "oauth": "/v1/oauth",
            },
            "supported_currencies": ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "INR"],
            "supported_payment_methods": ["card", "bank_transfer", "wallet", "crypto"],
            "rate_limits": {
                "standard": "100 requests/minute",
                "admin": "500 requests/minute",
                "read_only": "50 requests/minute",
            },
        })

    # ==================================================================
    # OAUTH2 ENDPOINTS
    # ==================================================================

    @app.route("/v1/oauth/authorize", methods=["GET"])
    def authorize():
        return oauth2_authorize()

    @app.route("/v1/oauth/token", methods=["POST"])
    def token():
        return oauth2_token()

    # ==================================================================
    # PAYMENT ENDPOINTS
    # ==================================================================

    @app.route("/v1/payments", methods=["POST"])
    @require_auth
    @require_permission("payments:write")
    @rate_limit_middleware
    def create_payment():
        """Create a new payment."""
        data = request.get_json(silent=True)

        if data is None:
            return jsonify({
                "error": {
                    "type": "invalid_request",
                    "message": "Request body must be valid JSON. "
                               "Ensure the Content-Type header is set to "
                               "'application/json'.",
                    "status": 400,
                }
            }), 400

        # Check idempotency key
        idempotency_key = request.headers.get("Idempotency-Key")
        if idempotency_key:
            cached = store.idempotency_cache.get(idempotency_key)
            if cached:
                response = jsonify(cached)
                response.headers["X-Idempotent-Replayed"] = "true"
                return response, 200

        # Validate input
        validation = validate_payment_creation(data)
        if not validation.is_valid:
            return jsonify(validation.to_response()), 422

        # Create payment
        payment = Payment(
            amount=data["amount"],
            currency=data["currency"],
            description=data["description"],
            customer_email=data["customer_email"],
            payment_method=data.get("payment_method", "card"),
            metadata=data.get("metadata"),
        )

        if idempotency_key:
            payment.idempotency_key = idempotency_key

        # Process the payment (simulate)
        payment.process()
        store.add_payment(payment)

        # Cache for idempotency
        if idempotency_key:
            store.idempotency_cache[idempotency_key] = payment.to_dict()

        # Fire webhook
        event_type = (
            "payment.completed" if payment.status == "completed"
            else "payment.failed"
        )
        create_webhook_event(event_type, {"payment": payment.to_dict()})

        status_code = 201 if payment.status == "completed" else 402
        return jsonify(payment.to_dict()), status_code

    @app.route("/v1/payments", methods=["GET"])
    @require_auth
    @require_permission("payments:read")
    @rate_limit_middleware
    def list_payments():
        """List payments with pagination and filtering."""
        # Validate pagination
        pag_validation = validate_pagination_params(request.args)
        if not pag_validation.is_valid:
            return jsonify(pag_validation.to_response()), 422

        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        status = request.args.get("status")
        currency = request.args.get("currency")

        result = store.list_payments(
            page=page,
            per_page=per_page,
            status=status,
            currency=currency,
        )
        return jsonify(result)

    @app.route("/v1/payments/<payment_id>", methods=["GET"])
    @require_auth
    @require_permission("payments:read")
    @rate_limit_middleware
    def get_payment(payment_id):
        """Retrieve a single payment by ID."""
        if not payment_id.startswith("pay_"):
            return jsonify({
                "error": {
                    "type": "invalid_request",
                    "message": (
                        f"Invalid payment ID format: '{payment_id}'. "
                        f"Payment IDs start with 'pay_' followed by "
                        f"24 hexadecimal characters."
                    ),
                    "status": 400,
                }
            }), 400

        payment = store.get_payment(payment_id)
        if not payment:
            return jsonify({
                "error": {
                    "type": "not_found",
                    "message": f"Payment '{payment_id}' not found. "
                               f"Verify the payment ID is correct.",
                    "status": 404,
                }
            }), 404

        return jsonify(payment.to_dict())

    @app.route("/v1/payments/<payment_id>/status", methods=["GET"])
    @require_auth
    @require_permission("payments:read")
    @rate_limit_middleware
    def get_payment_status(payment_id):
        """Check the status of a payment."""
        payment = store.get_payment(payment_id)
        if not payment:
            return jsonify({
                "error": {
                    "type": "not_found",
                    "message": f"Payment '{payment_id}' not found.",
                    "status": 404,
                }
            }), 404

        return jsonify({
            "id": payment.id,
            "status": payment.status,
            "failure_reason": payment.failure_reason,
            "updated_at": payment.updated_at,
        })

    @app.route("/v1/payments/<payment_id>/cancel", methods=["POST"])
    @require_auth
    @require_permission("payments:write")
    @rate_limit_middleware
    def cancel_payment(payment_id):
        """Cancel a pending payment."""
        payment = store.get_payment(payment_id)
        if not payment:
            return jsonify({
                "error": {
                    "type": "not_found",
                    "message": f"Payment '{payment_id}' not found.",
                    "status": 404,
                }
            }), 404

        if payment.status not in ("pending", "processing"):
            return jsonify({
                "error": {
                    "type": "invalid_request",
                    "message": (
                        f"Payment '{payment_id}' cannot be cancelled. "
                        f"Current status: '{payment.status}'. Only payments "
                        f"with status 'pending' or 'processing' can be "
                        f"cancelled."
                    ),
                    "status": 409,
                }
            }), 409

        payment.status = "cancelled"
        payment.updated_at = datetime.now(timezone.utc).isoformat()
        create_webhook_event("payment.cancelled", {"payment": payment.to_dict()})

        return jsonify(payment.to_dict())

    # ==================================================================
    # REFUND ENDPOINTS
    # ==================================================================

    @app.route("/v1/payments/<payment_id>/refund", methods=["POST"])
    @require_auth
    @require_permission("refunds:write")
    @rate_limit_middleware
    def create_refund(payment_id):
        """Create a refund for a completed payment."""
        payment = store.get_payment(payment_id)
        if not payment:
            return jsonify({
                "error": {
                    "type": "not_found",
                    "message": f"Payment '{payment_id}' not found.",
                    "status": 404,
                }
            }), 404

        if payment.status not in ("completed", "partially_refunded"):
            return jsonify({
                "error": {
                    "type": "invalid_request",
                    "message": (
                        f"Payment '{payment_id}' cannot be refunded. "
                        f"Current status: '{payment.status}'. Only "
                        f"completed or partially refunded payments "
                        f"are eligible for refunds."
                    ),
                    "status": 409,
                }
            }), 409

        data = request.get_json(silent=True) or {}
        validation = validate_refund_request(data)
        if not validation.is_valid:
            return jsonify(validation.to_response()), 422

        refund_amount = data.get("amount", payment.amount - payment.refunded_amount)
        refund_amount = float(refund_amount)

        available = payment.amount - payment.refunded_amount
        if refund_amount > available:
            return jsonify({
                "error": {
                    "type": "invalid_request",
                    "message": (
                        f"Refund amount {refund_amount} exceeds the "
                        f"available refundable amount of {available:.2f}. "
                        f"Original payment: {payment.amount}, "
                        f"already refunded: {payment.refunded_amount}."
                    ),
                    "status": 400,
                }
            }), 400

        reason = data.get("reason", "requested_by_customer")
        refund = Refund(payment_id, refund_amount, reason)
        refund.process()
        store.add_refund(refund)

        # Update payment
        payment.refunded_amount += refund_amount
        if payment.refunded_amount >= payment.amount:
            payment.status = "refunded"
        else:
            payment.status = "partially_refunded"
        payment.updated_at = datetime.now(timezone.utc).isoformat()

        create_webhook_event("refund.completed", {
            "refund": refund.to_dict(),
            "payment": payment.to_dict(),
        })

        return jsonify(refund.to_dict()), 201

    # ==================================================================
    # DATA RESET (testing utility)
    # ==================================================================

    @app.route("/v1/test/reset", methods=["POST"])
    @require_auth
    @require_permission("api:admin")
    def reset_data():
        """Reset all data in the store. Admin-only testing utility."""
        store.reset()
        rate_limiter.reset()
        reset_webhooks()
        return jsonify({
            "message": "All test data has been reset.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    return app


# ---------------------------------------------------------------------------
# Development server entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    print(f"Payment API starting on http://localhost:{port}")
    print(f"Health check: http://localhost:{port}/v1/health")
    print(f"API info:     http://localhost:{port}/v1/api-info")
    app.run(host="0.0.0.0", port=port, debug=True)
