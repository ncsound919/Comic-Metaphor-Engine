"""Tests for api.billing (Stripe checkout/portal/webhook logic)."""
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT, _ROOT / "engine"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


@pytest.fixture(autouse=True)
def billing_env(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_CREATOR_MONTHLY", "price_123")
    monkeypatch.setenv("APP_URL", "http://localhost:5173")


def test_checkout_503_when_unconfigured(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    from api.billing import create_checkout

    with pytest.raises(HTTPException) as exc:
        create_checkout({"id": "u1", "email": "a@b.c"})
    assert exc.value.status_code == 503


def test_portal_400_without_customer(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    from api import db
    from api.billing import create_portal

    monkeypatch.setattr(db, "get_user", lambda uid: {"plan": "creator"})
    with pytest.raises(HTTPException) as exc:
        create_portal({"id": "u1", "email": "a@b.c"})
    assert exc.value.status_code == 400


def test_handle_subscription_updated_sets_creator(monkeypatch):
    from api import db
    from api.billing import _handle_event

    calls = []
    monkeypatch.setattr(db, "set_subscription", lambda uid, **kw: calls.append((uid, kw)))

    _handle_event(
        {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "metadata": {"user_id": "u1"},
                    "status": "active",
                    "current_period_end": 1700000000,
                }
            },
        }
    )
    assert calls[0][0] == "u1"
    assert calls[0][1]["plan"] == "creator"
    assert calls[0][1]["subscription_status"] == "active"


def test_handle_subscription_deleted_sets_free(monkeypatch):
    from api import db
    from api.billing import _handle_event

    calls = []
    monkeypatch.setattr(db, "set_subscription", lambda uid, **kw: calls.append((uid, kw)))

    _handle_event(
        {
            "type": "customer.subscription.deleted",
            "data": {"object": {"metadata": {"user_id": "u1"}}},
        }
    )
    assert calls[0][1]["plan"] == "free"
    assert calls[0][1]["subscription_status"] == "canceled"


def test_handle_checkout_completed_sets_customer(monkeypatch):
    from api import db
    from api.billing import _handle_event

    calls = []
    monkeypatch.setattr(db, "set_subscription", lambda uid, **kw: calls.append((uid, kw)))

    _handle_event(
        {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "metadata": {"user_id": "u1"},
                    "client_reference_id": "u1",
                    "customer": "cus_123",
                }
            },
        }
    )
    assert calls[0][1]["stripe_customer_id"] == "cus_123"


def test_handle_unknown_event_ignored(monkeypatch):
    from api import db
    from api.billing import _handle_event

    monkeypatch.setattr(db, "set_subscription", lambda uid, **kw: pytest.fail("should not call"))
    _handle_event({"type": "invoice.paid", "data": {"object": {}}})


def test_checkout_creates_subscription_session(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_CREATOR_MONTHLY", "price_123")
    monkeypatch.setenv("APP_URL", "http://localhost:5173")
    import stripe as stripe_mod
    from api.billing import create_checkout

    captured = {}

    class FakeSession:
        url = "https://checkout.stripe.com/c/pay/x"

    def fake_create(**kwargs):
        captured.update(kwargs)
        return FakeSession()

    monkeypatch.setattr(stripe_mod.checkout.Session, "create", fake_create)
    result = create_checkout({"id": "u1", "email": "a@b.c"})
    assert result["url"] == FakeSession.url
    assert captured["mode"] == "subscription"
    assert captured["metadata"] == {"user_id": "u1"}
    assert captured["subscription_data"] == {"metadata": {"user_id": "u1"}}
    assert captured["line_items"] == [{"price": "price_123", "quantity": 1}]
    assert captured["client_reference_id"] == "u1"


def test_webhook_bad_signature_returns_400(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    import asyncio

    import stripe as stripe_mod
    from api.billing import webhook
    from starlette.requests import Request

    def boom(payload, signature, secret):
        raise stripe_mod.error.SignatureVerificationError("bad signature", signature)

    monkeypatch.setattr(stripe_mod.Webhook, "construct_event", boom)

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/billing/webhook",
            "headers": [(b"stripe-signature", b"t=1,v1=x")],
        },
        receive=receive,
    )

    async def run():
        try:
            await webhook(request)
            return None
        except HTTPException as exc:
            return exc

    result = asyncio.run(run())
    assert result is not None and result.status_code == 400


def test_handle_subscription_without_metadata_noop(monkeypatch):
    from api import db
    from api.billing import _handle_event

    monkeypatch.setattr(db, "set_subscription", lambda uid, **kw: pytest.fail("should not call"))
    _handle_event(
        {"type": "customer.subscription.updated", "data": {"object": {"metadata": {}, "status": "active"}}}
    )
