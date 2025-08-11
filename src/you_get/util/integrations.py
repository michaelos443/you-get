#!/usr/bin/env python
"""Optional integrations (Sentry, Stripe) guarded by environment variables and optional imports.

- Sentry: initialize if SENTRY_DSN or YOU_GET_SENTRY_DSN is set and sentry_sdk is installed.
- Stripe: run dummy product/customer creation if STRIPE_API_KEY is set and stripe is installed.
"""
from __future__ import annotations

import os
from typing import Optional, Tuple

from .log import i as log_i, w as log_w


def init_sentry_and_test(quiet_flag_used: bool) -> bool:
    """Initialize Sentry and capture a test exception tagged to the quiet flag.

    Returns True if an attempt was made (SDK found and DSN present), False otherwise.
    """
    dsn = os.getenv("YOU_GET_SENTRY_DSN") or os.getenv("SENTRY_DSN")
    if not dsn:
        log_w("Sentry DSN not provided; skip Sentry init (set SENTRY_DSN).")
        return False
    try:
        import sentry_sdk  # type: ignore
    except Exception:
        log_w("sentry_sdk not installed; skip Sentry init.")
        return False

    try:
        sentry_sdk.init(dsn=dsn, environment=os.getenv("SENTRY_ENV", "development"))
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("feature", "quiet_flag")
            scope.set_tag("quiet_flag_used", str(quiet_flag_used).lower())
        # Log a test exception tied to the feature
        try:
            raise RuntimeError("you-get test exception for quiet flag integration")
        except Exception as exc:  # noqa: BLE001
            sentry_sdk.capture_exception(exc)
            log_i("Sentry test exception captured.")
        return True
    except Exception as e:  # pragma: no cover
        log_w(f"Failed to initialize Sentry: {e}")
        return False


def stripe_simulate_create() -> Optional[Tuple[str, str]]:
    """Create a dummy Stripe product and customer using test API key.

    Returns (product_id, customer_id) if successful; otherwise None.
    """
    api_key = os.getenv("STRIPE_API_KEY")
    if not api_key:
        log_w("STRIPE_API_KEY not provided; skip Stripe simulation.")
        return None

    try:
        import stripe  # type: ignore
    except Exception:
        log_w("stripe package not installed; skip Stripe simulation.")
        return None

    try:
        stripe.api_key = api_key
        product = stripe.Product.create(name="you-get test product - quiet flag")
        customer = stripe.Customer.create(
            name="you-get Test Customer",
            email="test-customer@example.com",
            description="Created by you-get --stripe-simulate"
        )
        prod_id = getattr(product, "id", None) or product.get("id")
        cust_id = getattr(customer, "id", None) or customer.get("id")
        log_i(f"Stripe simulation created product={prod_id}, customer={cust_id}")
        return str(prod_id), str(cust_id)
    except Exception as e:  # pragma: no cover
        log_w(f"Stripe simulation failed: {e}")
        return None

