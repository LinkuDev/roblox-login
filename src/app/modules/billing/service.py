"""Nghiep vu diem (point). Tach rieng de sau cam cong thanh toan tu dong vao.

Nguyen tac: KHONG bao gio sua Wallet.balance truc tiep - moi thay doi phai qua
`_apply` de ghi kem 1 PointTransaction (audit + tranh lech so).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.enums import PointTxType
from app.core.errors import InsufficientPoints, NotFoundError
from app.db.models import PointTransaction, Wallet
from app.db.repositories import WalletRepository


class BillingService:
    def __init__(self, session: Session):
        self.session = session
        self.wallets = WalletRepository(session)

    def ensure_wallet(self, user_id: str) -> Wallet:
        wallet = self.wallets.by_user(user_id)
        if wallet is None:
            wallet = Wallet(user_id=user_id, balance=0)
            self.wallets.add(wallet)
        return wallet

    def balance(self, user_id: str) -> int:
        wallet = self.wallets.by_user(user_id)
        if wallet is None:
            raise NotFoundError("chua co vi")
        return wallet.balance

    def topup(
        self,
        user_id: str,
        amount: int,
        note: str = "",
        tx_type=PointTxType.TOPUP,
        ref_type: str = "",
        ref_id: str = "",
    ) -> int:
        if amount <= 0:
            raise ValueError("so diem nap phai > 0")
        wallet = self.ensure_wallet(user_id)
        return self._apply(wallet, tx_type, amount, ref_type, ref_id, note)

    def charge(self, user_id: str, amount: int, ref_type: str = "", ref_id: str = "", note: str = "") -> int:
        """Tru diem. Raise InsufficientPoints neu khong du."""
        if amount <= 0:
            raise ValueError("so diem tru phai > 0")
        wallet = self.ensure_wallet(user_id)
        if wallet.balance < amount:
            raise InsufficientPoints(
                f"can {amount} diem, con {wallet.balance}", need=amount, have=wallet.balance
            )
        return self._apply(wallet, PointTxType.SPEND, -amount, ref_type, ref_id, note)

    def refund(self, user_id: str, amount: int, ref_type: str = "", ref_id: str = "", note: str = "") -> int:
        wallet = self.ensure_wallet(user_id)
        return self._apply(wallet, PointTxType.REFUND, amount, ref_type, ref_id, note)

    # --- noi bo ------------------------------------------------------------
    def _apply(
        self,
        wallet: Wallet,
        tx_type: PointTxType,
        delta: int,
        ref_type: str = "",
        ref_id: str = "",
        note: str = "",
    ) -> int:
        wallet.balance += delta
        self.wallets.add_transaction(
            PointTransaction(
                wallet_id=wallet.id,
                type=tx_type,
                amount=delta,
                balance_after=wallet.balance,
                ref_type=ref_type,
                ref_id=ref_id,
                note=note,
            )
        )
        return wallet.balance
