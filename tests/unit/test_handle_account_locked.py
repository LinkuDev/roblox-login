from unittest.mock import MagicMock, patch
import pytest

from app.automation.context import ExecutionContext
from app.domain.models import Credential
from app.services.roblox.steps.handle_account_locked import HandleAccountLockedStep


def _ctx():
    browser = MagicMock()
    browser.current_url.return_value = "https://www.roblox.com/not-approved"
    browser.option.return_value = None
    settings = MagicMock()
    settings.captcha.timeout = 2
    ctx = ExecutionContext(
        credential=Credential("user", "pass"),
        browser=browser,
        solver=MagicMock(),
        settings=settings,
    )
    return ctx


def test_handle_account_locked_should_run():
    step = HandleAccountLockedStep()
    step.redirect_wait = 1
    ctx = _ctx()
    assert step.should_run(ctx) is True


def test_handle_account_locked_waits_for_continue_and_unlocks():
    step = HandleAccountLockedStep()
    step.poll = 0.1
    ctx = _ctx()

    # Simulate page loading at first (no button), then continueClickable appears, then unlocked
    state_sequence = [
        {"notApproved": True, "modal": True, "continueClickable": False},
        {"notApproved": True, "modal": True, "continueClickable": True},
        {"notApproved": False, "appPromo": True},
        {"notApproved": False, "appPromo": True},  # debounce check
    ]

    def mock_run_js(code):
        if "document.querySelectorAll" in code and "click()" in code:
            return True
        if "location.href" in code:
            if state_sequence:
                return state_sequence.pop(0)
            return {"notApproved": False, "appPromo": True}
        return None

    ctx.browser.run_js.side_effect = mock_run_js

    res = step.run(ctx)
    assert res.outcome.value == "ok"
