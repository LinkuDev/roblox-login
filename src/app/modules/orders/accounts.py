"""Parse + validate payload `user:pass` cho order.

Payload luon la text, moi dong 1 account:

    user:pass
    user:pass
    user:pass:totp   # totp la tuy chon

Dung chung boi OrderService.create (reject neu co dong sai) va endpoint
/orders/validate (form goi truoc khi submit de bao truoc so diem / dong loi).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from app.domain.models import Credential


@dataclass(slots=True)
class LineError:
    line: int          # so dong (1-based) trong payload goc
    raw: str           # noi dung dong (da cat khoang trang)
    error: str         # ly do khong hop le

    def to_dict(self) -> dict:
        return asdict(self)


def parse_accounts(text: str) -> tuple[list[Credential], list[LineError]]:
    """Tra ve (credentials hop le, danh sach dong loi).

    Bo qua dong trong va dong bat dau bang '#'. Moi dong con lai bat buoc dang
    `user:pass` - user va pass khong duoc rong.
    """
    creds: list[Credential] = []
    errors: list[LineError] = []

    for idx, raw in enumerate((text or "").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        if len(parts) < 2 or not parts[0].strip() or not parts[1].strip():
            errors.append(LineError(idx, line, "sai dinh dang, can user:pass"))
            continue
        try:
            creds.append(Credential.parse(line))
        except ValueError as exc:
            errors.append(LineError(idx, line, str(exc)))

    return creds, errors
