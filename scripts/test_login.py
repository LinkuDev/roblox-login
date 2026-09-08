#!/usr/bin/env python
"""Chay thu flow roblox.login (Chrome for Testing + extension YesCaptcha, headful).

Dung user/pass (KHONG dung cookie). Extension tu giai Arkose in-page; flow tu bam
Continue o man "Account locked" (/not-approved).

Vi du:
  .venv/bin/python scripts/test_login.py <user> <pass>
  .venv/bin/python scripts/test_login.py --line 1                  # dong 1 trong file acc
  .venv/bin/python scripts/test_login.py --count 3 --start 0       # 3 acc dau
  .venv/bin/python scripts/test_login.py --file .data/accounts.txt --count 5

File acc: moi dong "user:pass:cookie" (cookie co the chua ':' -> chi tach 2 ':' dau).
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from robloxnode.pool import Record
from robloxnode.realflow import real_flow

DEFAULT_FILE = Path(__file__).resolve().parent.parent / ".data" / "captcha_lock_cookies.txt"


def parse_line(line: str) -> tuple[str, str] | None:
    parts = line.rstrip("\n").split(":", 2)
    if len(parts) < 2:
        return None
    return parts[0].strip(), parts[1].strip()


def collect(args: argparse.Namespace) -> list[tuple[str, str]]:
    if args.user and args.password:
        return [(args.user, args.password)]
    path = Path(args.file) if args.file else DEFAULT_FILE
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if args.line is not None:
        creds = [parse_line(lines[args.line])]
    else:
        creds = [parse_line(x) for x in lines[args.start : args.start + args.count]]
    return [c for c in creds if c]


def main() -> None:
    ap = argparse.ArgumentParser(description="Test flow roblox.login (CfT + extension)")
    ap.add_argument("user", nargs="?", help="username (bo trong -> doc tu file)")
    ap.add_argument("password", nargs="?", help="password")
    ap.add_argument("--file", help=f"file acc (mac dinh: {DEFAULT_FILE})")
    ap.add_argument("--line", type=int, help="chay 1 dong cu the trong file (0-based)")
    ap.add_argument("--start", type=int, default=0, help="dong bat dau (mac dinh 0)")
    ap.add_argument("--count", type=int, default=1, help="so acc chay (mac dinh 1)")
    args = ap.parse_args()

    creds = collect(args)
    if not creds:
        raise SystemExit("Khong co account nao. Truyen user pass, hoac --line/--count.")

    print(f"== Test {len(creds)} account (CfT + extension YesCaptcha, headful) ==\n")
    for i, (user, pw) in enumerate(creds, 1):
        print(f"[{i}/{len(creds)}] {user}")
        t0 = time.time()
        try:
            res = real_flow(Record(id=f"t{i}", username=user, password=pw))
        except Exception as exc:  # noqa: BLE001
            res = {"success": False, "error": "exception", "reason": repr(exc)}
        dt = round(time.time() - t0, 1)
        cookie = (res.get("cookies") or {}).get(".ROBLOSECURITY")
        print(
            f"    -> success={res.get('success')} error={res.get('error')} "
            f"reason={res.get('reason')} cookie={'yes' if cookie else 'no'}  {dt}s\n"
        )


if __name__ == "__main__":
    main()
