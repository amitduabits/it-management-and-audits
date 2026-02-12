"""
Input Validation Module
========================

Provides comprehensive request validation with detailed,
developer-friendly error messages following consistent error
formatting conventions.
"""

import re
from api.models import Currency, CURRENCY_MIN_AMOUNTS, CURRENCY_MAX_AMOUNTS


class ValidationError:
    """Represents a single field validation error."""

    def __init__(self, field, code, message):
        self.field = field
        self.code = code
        self.message = message

    def to_dict(self):
        return {
            "field": self.field,
            "code": self.code,
            "message": self.message,
        }


class ValidationResult:
    """Collects and reports validation errors."""

    def __init__(self):
        self.errors = []

    def add_error(self, field, code, message):
        self.errors.append(ValidationError(field, code, message))

    @property
    def is_valid(self):
        return len(self.errors) == 0

    def to_response(self):
        return {
            "error": {
                "type": "validation_error",
                "message": "The request body contains invalid parameters.",
                "status": 422,
                "errors": [e.to_dict() for e in self.errors],
            }
        }


# ---------------------------------------------------------------------------
# Email validation
# ---------------------------------------------------------------------------
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


def is_valid_email(email):
    """Check if a string is a plausible email address."""
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email))


# ---------------------------------------------------------------------------
# Payment validation
# ---------------------------------------------------------------------------
VALID_PAYMENT_METHODS = ["card", "bank_transfer", "wallet", "crypto"]

VALID_REFUND_REASONS = [
    "requested_by_customer",
    "duplicate",
    "fraudulent",
    "product_not_received",
    "product_unacceptable",
    "other",
]


def validate_payment_creation(data):
    """
    Validate the request body for creating a new payment.
    Returns a ValidationResult with any errors found.
    """
    result = ValidationResult()

    if not data or not isinstance(data, dict):
        result.add_error(
            "body", "invalid_body",
            "Request body must be a valid JSON object."
        )
        return result

    # --- amount ---
    amount = data.get("amount")
    if amount is None:
        result.add_error(
            "amount", "required",
            "The 'amount' field is required. Provide the payment "
            "amount as a positive number."
        )
    else:
        try:
            amount_val = float(amount)
            currency = data.get("currency", "USD").upper()

            if amount_val <= 0:
                result.add_error(
                    "amount", "invalid_value",
                    "Amount must be a positive number greater than zero."
                )
            else:
                min_amt = CURRENCY_MIN_AMOUNTS.get(currency, 0.50)
                max_amt = CURRENCY_MAX_AMOUNTS.get(currency, 999999.99)

                if amount_val < min_amt:
                    result.add_error(
                        "amount", "amount_too_small",
                        f"Amount {amount_val} is below the minimum of "
                        f"{min_amt} for currency {currency}."
                    )
                elif amount_val > max_amt:
                    result.add_error(
                        "amount", "amount_too_large",
                        f"Amount {amount_val} exceeds the maximum of "
                        f"{max_amt} for currency {currency}."
                    )
        except (ValueError, TypeError):
            result.add_error(
                "amount", "invalid_type",
                "Amount must be a numeric value (integer or float). "
                f"Received: {type(amount).__name__}"
            )

    # --- currency ---
    currency = data.get("currency")
    if currency is None:
        result.add_error(
            "currency", "required",
            "The 'currency' field is required. Supported currencies: "
            + ", ".join(c.value for c in Currency)
        )
    elif not isinstance(currency, str):
        result.add_error(
            "currency", "invalid_type",
            "Currency must be a three-letter ISO 4217 code string."
        )
    else:
        try:
            Currency(currency.upper())
        except ValueError:
            result.add_error(
                "currency", "invalid_value",
                f"'{currency}' is not a supported currency. "
                f"Supported: {', '.join(c.value for c in Currency)}"
            )

    # --- description ---
    description = data.get("description")
    if description is None:
        result.add_error(
            "description", "required",
            "The 'description' field is required. Provide a short "
            "description of the payment purpose."
        )
    elif not isinstance(description, str):
        result.add_error(
            "description", "invalid_type",
            "Description must be a string."
        )
    elif len(description.strip()) == 0:
        result.add_error(
            "description", "empty_value",
            "Description cannot be an empty string."
        )
    elif len(description) > 500:
        result.add_error(
            "description", "too_long",
            f"Description must be 500 characters or fewer. "
            f"Current length: {len(description)}"
        )

    # --- customer_email ---
    email = data.get("customer_email")
    if email is None:
        result.add_error(
            "customer_email", "required",
            "The 'customer_email' field is required."
        )
    elif not is_valid_email(email):
        result.add_error(
            "customer_email", "invalid_format",
            f"'{email}' is not a valid email address. "
            "Provide an email in the format: user@example.com"
        )

    # --- payment_method (optional) ---
    method = data.get("payment_method")
    if method is not None:
        if method not in VALID_PAYMENT_METHODS:
            result.add_error(
                "payment_method", "invalid_value",
                f"'{method}' is not a valid payment method. "
                f"Accepted values: {', '.join(VALID_PAYMENT_METHODS)}"
            )

    # --- metadata (optional) ---
    metadata = data.get("metadata")
    if metadata is not None:
        if not isinstance(metadata, dict):
            result.add_error(
                "metadata", "invalid_type",
                "Metadata must be a JSON object (key-value pairs)."
            )
        else:
            if len(metadata) > 20:
                result.add_error(
                    "metadata", "too_many_keys",
                    f"Metadata may contain at most 20 keys. "
                    f"Received: {len(metadata)}"
                )
            for key, value in metadata.items():
                if not isinstance(key, str) or len(key) > 40:
                    result.add_error(
                        f"metadata.{key}", "invalid_key",
                        "Metadata keys must be strings of 40 characters "
                        "or fewer."
                    )
                    break
                if not isinstance(value, (str, int, float, bool)):
                    result.add_error(
                        f"metadata.{key}", "invalid_value_type",
                        "Metadata values must be strings, numbers, or booleans."
                    )
                    break

    return result


def validate_refund_request(data):
    """Validate the request body for creating a refund."""
    result = ValidationResult()

    if not data or not isinstance(data, dict):
        result.add_error(
            "body", "invalid_body",
            "Request body must be a valid JSON object."
        )
        return result

    # --- amount (optional -- full refund if omitted) ---
    amount = data.get("amount")
    if amount is not None:
        try:
            amount_val = float(amount)
            if amount_val <= 0:
                result.add_error(
                    "amount", "invalid_value",
                    "Refund amount must be a positive number."
                )
        except (ValueError, TypeError):
            result.add_error(
                "amount", "invalid_type",
                "Refund amount must be a numeric value."
            )

    # --- reason (optional) ---
    reason = data.get("reason")
    if reason is not None and reason not in VALID_REFUND_REASONS:
        result.add_error(
            "reason", "invalid_value",
            f"'{reason}' is not a valid refund reason. "
            f"Accepted values: {', '.join(VALID_REFUND_REASONS)}"
        )

    return result


def validate_pagination_params(args):
    """Validate query-string pagination parameters."""
    result = ValidationResult()

    page = args.get("page", "1")
    try:
        page_int = int(page)
        if page_int < 1:
            result.add_error(
                "page", "invalid_value",
                "Page number must be a positive integer >= 1."
            )
    except ValueError:
        result.add_error(
            "page", "invalid_type",
            f"Page must be an integer. Received: '{page}'"
        )

    per_page = args.get("per_page", "10")
    try:
        pp_int = int(per_page)
        if pp_int < 1 or pp_int > 100:
            result.add_error(
                "per_page", "invalid_value",
                "per_page must be between 1 and 100."
            )
    except ValueError:
        result.add_error(
            "per_page", "invalid_type",
            f"per_page must be an integer. Received: '{per_page}'"
        )

    return result
