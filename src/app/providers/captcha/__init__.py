"""Import cac provider de chung tu dang ky vao registry."""

from app.providers.captcha import anticaptcha, capsolver, manual, twocaptcha  # noqa: F401
from app.providers.captcha.factory import build_solver, available_solvers

__all__ = ["available_solvers", "build_solver"]
