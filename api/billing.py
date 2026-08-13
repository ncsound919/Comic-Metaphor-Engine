"""Stripe billing for the $1/mo Creator plan."""

from __future__ import annotations

import os
from typing import Any, Dict

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request

from api.auth import get_current_user
from api import db as dbmod

router = APIRouter(prefix="/api/billing")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
APP_URL = os.getenv("APP_URL", "http://localhost:5173")
PRICE_ID = os.getenv("STRIPE_PRICE_CREATOR_MONTHLY", "")

_ACTIVE_STATUSES = ("active", "trialing")


def _billing_enabled() -> bool:
    key = os.getenv("STRIPE_SECRET_KEY", "")
    price = os.getenv("STRIPE_PRICE_CREATOR_MONTHLY", "")
    stripe.api_key = key
    global PRICE_ID
    PRICE_ID = price
    return bool(key and price)


@router.post("/checkout")
def create_checkout(user: Dict[str, Any] = Depends(get_current_user)):
    if not _billing_enabled():
        raise HTTPException(status_code=503, detail="Billing not configured")
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": PRICE_ID, "quantity": 1}],
        client_reference_id=user["id"],
        customer_email=user.get("email") or None,
        metadata={"user_id": user["id"]},
        subscription_data={"metadata": {"user_id": user["id"]}},
        success_url=f"{APP_URL}/account?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{APP_URL}/pricing",
    )
    return {"url": session.url}


@router.post("/portal")
def create_portal(user: Dict[str, Any] = Depends(get_current_user)):
    if not _billing_enabled():
        raise HTTPException(status_code=503, detail="Billing not configured")
    row = dbmod.get_user(user["id"]) or {}
    customer_id = row.get("stripe_customer_id")
    if not customer_id:
        raise HTTPException(status_code=400, detail="No subscription on file")
    session = stripe.billing_portal.Session.create(
        customer=customer_id, return_url=f"{APP_URL}/account"
    )
    return {"url": session.url}


@router.post("/webhook")
async def webhook(request: Request):
    if not _billing_enabled():
        return {"received": True}

    payload = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, os.getenv("STRIPE_WEBHOOK_SECRET", "")
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid payload or signature")

    _handle_event(event)
    return {"received": True}


def _handle_event(event: Any) -> None:
    """Apply entitlement changes from a Stripe event (idempotent, last-write-wins)."""
    etype = event["type"]
    obj = event["data"]["object"]

    if etype == "checkout.session.completed":
        user_id = (obj.get("metadata") or {}).get("user_id") or obj.get("client_reference_id")
        if user_id:
            dbmod.set_subscription(user_id, stripe_customer_id=obj.get("customer"))
        return

    if etype in ("customer.subscription.created", "customer.subscription.updated"):
        user_id = (obj.get("metadata") or {}).get("user_id")
        if user_id:
            status = obj.get("status", "inactive")
            dbmod.set_subscription(
                user_id,
                plan="creator" if status in _ACTIVE_STATUSES else "free",
                subscription_status=status,
                current_period_end=obj.get("current_period_end"),
            )
        return

    if etype == "customer.subscription.deleted":
        user_id = (obj.get("metadata") or {}).get("user_id")
        if user_id:
            dbmod.set_subscription(user_id, plan="free", subscription_status="canceled")
