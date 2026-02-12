"""
Data Models for Payment API
============================

Defines the core data structures used throughout the payment processing
system including Payment, Refund, and Transaction models.
"""

import uuid
import time
from datetime import datetime, timezone
from enum import Enum


class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class RefundStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class Currency(Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"
    INR = "INR"


CURRENCY_MIN_AMOUNTS = {
    "USD": 0.50,
    "EUR": 0.50,
    "GBP": 0.30,
    "JPY": 50,
    "CAD": 0.50,
    "AUD": 0.50,
    "INR": 1.00,
}

CURRENCY_MAX_AMOUNTS = {
    "USD": 999999.99,
    "EUR": 999999.99,
    "GBP": 999999.99,
    "JPY": 99999999,
    "CAD": 999999.99,
    "AUD": 999999.99,
    "INR": 99999999.99,
}


class Payment:
    """Represents a payment transaction."""

    def __init__(self, amount, currency, description, customer_email,
                 payment_method="card", metadata=None):
        self.id = f"pay_{uuid.uuid4().hex[:24]}"
        self.amount = round(float(amount), 2)
        self.currency = currency.upper()
        self.description = description
        self.customer_email = customer_email
        self.payment_method = payment_method
        self.metadata = metadata or {}
        self.status = PaymentStatus.PENDING.value
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.idempotency_key = None
        self.failure_reason = None
        self.refunded_amount = 0.0

    def to_dict(self):
        return {
            "id": self.id,
            "object": "payment",
            "amount": self.amount,
            "currency": self.currency,
            "description": self.description,
            "customer_email": self.customer_email,
            "payment_method": self.payment_method,
            "metadata": self.metadata,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "idempotency_key": self.idempotency_key,
            "failure_reason": self.failure_reason,
            "refunded_amount": self.refunded_amount,
            "livemode": False,
        }

    def process(self):
        """Simulate payment processing. Amounts ending in .99 simulate failures."""
        self.status = PaymentStatus.PROCESSING.value
        self.updated_at = datetime.now(timezone.utc).isoformat()

        amount_str = f"{self.amount:.2f}"
        if amount_str.endswith("13.00"):
            self.status = PaymentStatus.FAILED.value
            self.failure_reason = "card_declined"
        elif amount_str.endswith("66.60"):
            self.status = PaymentStatus.FAILED.value
            self.failure_reason = "insufficient_funds"
        elif amount_str.endswith("00.00") and self.amount > 9000:
            self.status = PaymentStatus.FAILED.value
            self.failure_reason = "amount_exceeds_limit"
        else:
            self.status = PaymentStatus.COMPLETED.value

        self.updated_at = datetime.now(timezone.utc).isoformat()
        return self.status


class Refund:
    """Represents a refund against a payment."""

    def __init__(self, payment_id, amount, reason="requested_by_customer"):
        self.id = f"ref_{uuid.uuid4().hex[:24]}"
        self.payment_id = payment_id
        self.amount = round(float(amount), 2)
        self.reason = reason
        self.status = RefundStatus.PENDING.value
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.failure_reason = None

    def to_dict(self):
        return {
            "id": self.id,
            "object": "refund",
            "payment_id": self.payment_id,
            "amount": self.amount,
            "reason": self.reason,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "failure_reason": self.failure_reason,
        }

    def process(self):
        """Simulate refund processing."""
        self.status = RefundStatus.PROCESSING.value
        self.updated_at = datetime.now(timezone.utc).isoformat()
        self.status = RefundStatus.COMPLETED.value
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return self.status


class Transaction:
    """Represents an individual transaction record in the ledger."""

    def __init__(self, payment_id, transaction_type, amount, currency):
        self.id = f"txn_{uuid.uuid4().hex[:24]}"
        self.payment_id = payment_id
        self.type = transaction_type  # "charge", "refund", "adjustment"
        self.amount = round(float(amount), 2)
        self.currency = currency.upper()
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.net_amount = self.amount
        self.fee = round(self.amount * 0.029 + 0.30, 2) if transaction_type == "charge" else 0.0

    def to_dict(self):
        return {
            "id": self.id,
            "object": "transaction",
            "payment_id": self.payment_id,
            "type": self.type,
            "amount": self.amount,
            "currency": self.currency,
            "fee": self.fee,
            "net_amount": round(self.amount - self.fee, 2),
            "created_at": self.created_at,
        }


# In-memory data store
class DataStore:
    """Simple in-memory data store for the mock API."""

    def __init__(self):
        self.payments = {}
        self.refunds = {}
        self.transactions = {}
        self.webhooks = []
        self.idempotency_cache = {}

    def add_payment(self, payment):
        self.payments[payment.id] = payment
        txn = Transaction(payment.id, "charge", payment.amount, payment.currency)
        self.transactions[txn.id] = txn
        return payment

    def get_payment(self, payment_id):
        return self.payments.get(payment_id)

    def list_payments(self, page=1, per_page=10, status=None, currency=None):
        items = list(self.payments.values())

        if status:
            items = [p for p in items if p.status == status]
        if currency:
            items = [p for p in items if p.currency == currency.upper()]

        items.sort(key=lambda p: p.created_at, reverse=True)

        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        page_items = items[start:end]

        return {
            "object": "list",
            "data": [p.to_dict() for p in page_items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": max(1, (total + per_page - 1) // per_page),
                "has_more": end < total,
            }
        }

    def add_refund(self, refund):
        self.refunds[refund.id] = refund
        txn = Transaction(refund.payment_id, "refund", -refund.amount, "USD")
        self.transactions[txn.id] = txn
        return refund

    def get_refund(self, refund_id):
        return self.refunds.get(refund_id)

    def reset(self):
        self.__init__()


# Singleton store instance
store = DataStore()
