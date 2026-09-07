import pytest

from app.core.errors import InsufficientPoints


class FakeWallet:
    def __init__(self):
        self.id = "w1"
        self.balance = 0


def _billing(monkeypatch):
    from app.modules.billing.service import BillingService

    svc = BillingService.__new__(BillingService)
    wallet = FakeWallet()

    class FakeRepo:
        def by_user(self, uid):
            return wallet

        def add_transaction(self, tx):
            return tx

    svc.wallets = FakeRepo()
    return svc, wallet


def test_topup_then_charge(monkeypatch):
    svc, wallet = _billing(monkeypatch)
    assert svc.topup("u", 100) == 100
    assert svc.charge("u", 30, ref_type="order", ref_id="o1") == 70
    assert wallet.balance == 70


def test_charge_insufficient(monkeypatch):
    svc, _ = _billing(monkeypatch)
    svc.topup("u", 10)
    with pytest.raises(InsufficientPoints):
        svc.charge("u", 50)
