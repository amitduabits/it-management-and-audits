"""
Webhook Simulation Module
===========================

Provides endpoints for registering webhook URLs, viewing webhook
event logs, and simulating webhook delivery for payment events.
"""

import uuid
import time
import hmac
import hashlib
import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, g

from api.auth import require_auth, require_permission

webhooks_bp = Blueprint("webhooks", __name__)

# ---------------------------------------------------------------------------
# In-memory webhook store
# ---------------------------------------------------------------------------
_registered_webhooks = {}
_webhook_events = []

WEBHOOK_SECRET = "whsec_test_abc123def456ghi789"

SUPPORTED_EVENT_TYPES = [
    "payment.created",
    "payment.completed",
    "payment.failed",
    "payment.cancelled",
    "refund.created",
    "refund.completed",
    "refund.failed",
]


def generate_webhook_signature(payload_str, secret):
    """Generate HMAC-SHA256 signature for a webhook payload."""
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.{payload_str}"
    signature = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


def create_webhook_event(event_type, data):
    """Create a webhook event payload and store it in the event log."""
    event = {
        "id": f"evt_{uuid.uuid4().hex[:24]}",
        "object": "event",
        "type": event_type,
        "data": data,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "livemode": False,
        "pending_webhooks": len(_registered_webhooks),
        "api_version": "2024-01-15",
    }
    _webhook_events.append(event)

    # In a real system, we would POST to each registered URL here.
    # For the mock, we just log the event.
    return event


@webhooks_bp.route("/webhooks/endpoints", methods=["POST"])
@require_auth
@require_permission("webhooks:manage")
def register_webhook():
    """Register a new webhook endpoint."""
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": {
                "type": "validation_error",
                "message": "Request body must be valid JSON.",
                "status": 422,
            }
        }), 422

    url = data.get("url")
    events = data.get("events", SUPPORTED_EVENT_TYPES)

    if not url:
        return jsonify({
            "error": {
                "type": "validation_error",
                "message": "The 'url' field is required.",
                "status": 422,
                "errors": [{
                    "field": "url",
                    "code": "required",
                    "message": "Provide the HTTPS URL where webhook events "
                               "should be delivered.",
                }],
            }
        }), 422

    if not url.startswith("https://"):
        return jsonify({
            "error": {
                "type": "validation_error",
                "message": "Webhook URLs must use HTTPS.",
                "status": 422,
                "errors": [{
                    "field": "url",
                    "code": "invalid_scheme",
                    "message": "Webhook endpoint URL must start with "
                               "'https://'. HTTP is not accepted for "
                               "security reasons.",
                }],
            }
        }), 422

    invalid_events = [e for e in events if e not in SUPPORTED_EVENT_TYPES]
    if invalid_events:
        return jsonify({
            "error": {
                "type": "validation_error",
                "message": "One or more event types are invalid.",
                "status": 422,
                "errors": [{
                    "field": "events",
                    "code": "invalid_value",
                    "message": (
                        f"Invalid event types: {', '.join(invalid_events)}. "
                        f"Supported: {', '.join(SUPPORTED_EVENT_TYPES)}"
                    ),
                }],
            }
        }), 422

    webhook_id = f"we_{uuid.uuid4().hex[:24]}"
    endpoint = {
        "id": webhook_id,
        "object": "webhook_endpoint",
        "url": url,
        "events": events,
        "status": "active",
        "secret": WEBHOOK_SECRET,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _registered_webhooks[webhook_id] = endpoint

    return jsonify(endpoint), 201


@webhooks_bp.route("/webhooks/endpoints", methods=["GET"])
@require_auth
@require_permission("webhooks:manage")
def list_webhooks():
    """List all registered webhook endpoints."""
    endpoints = list(_registered_webhooks.values())
    return jsonify({
        "object": "list",
        "data": endpoints,
        "total": len(endpoints),
    })


@webhooks_bp.route("/webhooks/endpoints/<webhook_id>", methods=["DELETE"])
@require_auth
@require_permission("webhooks:manage")
def delete_webhook(webhook_id):
    """Delete a registered webhook endpoint."""
    if webhook_id not in _registered_webhooks:
        return jsonify({
            "error": {
                "type": "not_found",
                "message": f"Webhook endpoint '{webhook_id}' not found.",
                "status": 404,
            }
        }), 404

    deleted = _registered_webhooks.pop(webhook_id)
    return jsonify({
        "id": webhook_id,
        "object": "webhook_endpoint",
        "deleted": True,
    })


@webhooks_bp.route("/webhooks/events", methods=["GET"])
@require_auth
def list_webhook_events():
    """List recent webhook events."""
    event_type = request.args.get("type")
    limit = min(int(request.args.get("limit", "20")), 100)

    events = _webhook_events.copy()
    if event_type:
        events = [e for e in events if e["type"] == event_type]

    events.sort(key=lambda e: e["created_at"], reverse=True)
    events = events[:limit]

    return jsonify({
        "object": "list",
        "data": events,
        "total": len(events),
    })


@webhooks_bp.route("/webhooks/simulate", methods=["POST"])
@require_auth
@require_permission("webhooks:manage")
def simulate_webhook():
    """
    Simulate firing a webhook event.
    Useful for testing webhook handler implementations.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "error": {
                "type": "validation_error",
                "message": "Request body is required.",
                "status": 422,
            }
        }), 422

    event_type = data.get("event_type")
    payload = data.get("payload", {})

    if not event_type:
        return jsonify({
            "error": {
                "type": "validation_error",
                "message": "event_type is required.",
                "status": 422,
            }
        }), 422

    if event_type not in SUPPORTED_EVENT_TYPES:
        return jsonify({
            "error": {
                "type": "validation_error",
                "message": (
                    f"'{event_type}' is not a supported event type. "
                    f"Supported: {', '.join(SUPPORTED_EVENT_TYPES)}"
                ),
                "status": 422,
            }
        }), 422

    event = create_webhook_event(event_type, payload)
    payload_str = json.dumps(event, sort_keys=True)
    signature = generate_webhook_signature(payload_str, WEBHOOK_SECRET)

    return jsonify({
        "message": "Webhook event simulated successfully.",
        "event": event,
        "signature": signature,
        "webhook_secret": WEBHOOK_SECRET,
        "delivery_targets": len(_registered_webhooks),
    }), 200


def reset_webhooks():
    """Reset all webhook data. Used in tests."""
    _registered_webhooks.clear()
    _webhook_events.clear()
