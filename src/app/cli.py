"""CLI: chay thu flow truc tiep, khong can DB/API.

Vi du:
  rlx services                       # liet ke service
  rlx providers                      # liet ke provider co san
  rlx balance                        # so du captcha
  rlx run roblox.login -u USER -p PASS --no-headless
  rlx run roblox.login --file accounts.txt   # chay hang loat
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.domain.models import Credential

app = typer.Typer(add_completion=False, help="Automation service runner")
log = get_logger("cli")


@app.command()
def services():
    """Liet ke cac service dang co."""
    from app.services import list_services

    for spec in list_services():
        typer.echo(f"  {spec.id:20} {spec.price_points:>3} diem  - {spec.description}")


@app.command()
def providers():
    """Liet ke provider captcha / browser / proxy."""
    from app.providers.browser import available_browsers
    from app.providers.captcha import available_solvers
    from app.providers.proxy import available_proxy_providers

    typer.echo(f"captcha : {available_solvers()}")
    typer.echo(f"browser : {available_browsers()}")
    typer.echo(f"proxy   : {available_proxy_providers()}")


@app.command()
def balance(provider: str = typer.Option(None, help="ghi de CAPTCHA_PROVIDER")):
    """Kiem tra so du tai khoan captcha."""
    from app.providers.captcha import build_solver

    solver = build_solver(provider)
    typer.echo(f"{solver.name}: {solver.balance()} USD")
    solver.close()


@app.command()
def run(
    service: str = typer.Argument(..., help="vd roblox.login"),
    username: str = typer.Option(None, "-u", "--username"),
    password: str = typer.Option(None, "-p", "--password"),
    totp: str = typer.Option(None, "--totp", help="TOTP secret cho 2FA"),
    file: Path = typer.Option(None, "--file", help="file accounts user:pass moi dong"),
    headless: bool = typer.Option(True, "--headless/--no-headless"),
    solver: str = typer.Option(None, "--solver", help="ghi de provider captcha"),
    out: Path = typer.Option(None, "--out", help="ghi ket qua JSON"),
):
    """Chay 1 service cho 1 hoac nhieu account."""
    setup_logging()
    from app.automation.runner import run_service
    from app.providers.captcha import build_solver

    creds: list[Credential] = []
    if file:
        for line in Path(file).read_text().splitlines():
            if line.strip() and not line.startswith("#"):
                creds.append(Credential.parse(line))
    elif username and password:
        creds.append(Credential(username=username, password=password, totp_secret=totp))
    else:
        raise typer.BadParameter("can -u/-p hoac --file")

    shared_solver = build_solver(solver) if solver else None
    results = []
    for i, cred in enumerate(creds, 1):
        typer.echo(f"[{i}/{len(creds)}] {cred.username} ...")
        result = run_service(
            service,
            cred,
            job_id=f"cli-{i}",
            headless=headless,
            solver=shared_solver,
        )
        status = "OK" if result.success else f"FAIL ({result.error_code})"
        typer.echo(f"    -> {status}  {result.duration}s")
        results.append(result.to_dict())

    if out:
        Path(out).write_text(json.dumps(results, indent=2, ensure_ascii=False))
        typer.echo(f"da ghi ket qua vao {out}")
    else:
        typer.echo(json.dumps(results, indent=2, ensure_ascii=False))


@app.command()
def initdb():
    """Tao bang trong DB (idempotent). Chay 1 lan sau khi dung Postgres o prod.

    Dev (APP_ENV=dev) app tu tao bang luc khoi dong; prod thi KHONG -> dung lenh nay
    (hoac alembic sau nay). `create_all` bo qua bang da co nen chay lai an toan.
    """
    from app.db.session import init_db

    s = get_settings()
    init_db()
    typer.echo(f"initdb OK -> {s.db.database_url.split('@')[-1]}")


@app.command()
def config():
    """In cau hinh hien tai (an secret)."""
    s = get_settings()
    typer.echo(
        json.dumps(
            {
                "env": s.app.env,
                "captcha_provider": s.captcha.provider,
                "browser_provider": s.browser.provider,
                "proxy_provider": s.proxy.provider,
                "database": s.db.database_url.split("@")[-1],
                "queue": s.queue.queue_backend,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    app()
