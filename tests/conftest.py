"""Shared fixtures for the Steady Voice test suite.

The app is a single self-contained HTML file with no build step and no
module system, so the tests drive the real page in a real browser rather
than importing anything. Pure logic (state, date maths, CSV, charts) is
exercised through page.evaluate against the live globals.
"""
import pathlib
import subprocess
import sys

import pytest
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
APP_FILE = ROOT / "app" / "steadyvoice.html"
APP_URL = APP_FILE.as_uri()
# The cloud container ships a Chromium at a fixed path; a normal machine
# uses the one `playwright install` puts in the user cache. Pin the first
# if it exists, otherwise let Playwright find its own.
_PINNED = pathlib.Path("/opt/pw-browsers/chromium")
CHROMIUM = str(_PINNED) if _PINNED.exists() else None

# A fixed "now" so date-dependent behaviour (streaks, rotation, charts) is
# deterministic. Tuesday 8 September 2026, mid-morning local time.
FIXED_NOW_MS = 1788826800000  # 2026-09-08T10:00:00+10:00


@pytest.fixture(scope="session", autouse=True)
def build_app():
    """Always test the current source, not a stale build."""
    subprocess.run([sys.executable, str(ROOT / "build.py")], check=True,
                   capture_output=True)
    assert APP_FILE.exists()


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": CHROMIUM} if CHROMIUM else {}))
        yield b
        b.close()


class App:
    """Thin wrapper around the page with helpers the tests reuse."""

    def __init__(self, page):
        self.page = page
        self.errors = []
        page.on("pageerror", lambda e: self.errors.append(f"PAGEERROR: {e}"))
        page.on("console", lambda m: self.errors.append(f"CONSOLE: {m.text}")
                if m.type == "error" and "ERR_TUNNEL" not in m.text
                and "fonts.googleapis" not in m.text else None)

    # ── navigation ───────────────────────────────────────────────────
    def goto(self, seed=None):
        self.page.goto(APP_URL)
        self.page.wait_for_function("() => typeof window.go === 'function' || document.getElementById('view').children.length > 0")
        if seed is not None:
            self.page.evaluate(
                "s => localStorage.setItem('steadyvoice.v1', JSON.stringify(s))", seed)
            self.page.reload()
        self.page.wait_for_timeout(150)
        return self

    def tab(self, label):
        self.page.click(f'#tabs button:has-text("{label}")')
        self.page.wait_for_timeout(120)

    def switch_mode(self):
        self.page.click("#modeBtn")
        self.page.wait_for_timeout(150)

    def open_game(self, game_id):
        self.page.evaluate(f"go('game', {game_id!r})")
        self.page.wait_for_timeout(150)

    # ── state ────────────────────────────────────────────────────────
    def state(self):
        return self.page.evaluate("() => JSON.parse(JSON.stringify(S))")

    def stored(self):
        return self.page.evaluate(
            "() => { const r = localStorage.getItem('steadyvoice.v1');"
            "return r ? JSON.parse(r) : null; }")

    def js(self, expr, arg=None):
        return self.page.evaluate(expr, arg)

    def text(self):
        """Rendered text. Note text-transform applies, so compare case-insensitively."""
        return self.page.inner_text("#view")

    def all_text(self):
        """Rendered text including collapsed <details> panels."""
        self.page.evaluate(
            "() => document.querySelectorAll('#view details').forEach(d => d.open = true)")
        self.page.wait_for_timeout(80)
        return self.page.inner_text("#view")

    def assert_clean(self):
        assert not self.errors, "JS errors: " + " | ".join(self.errors)


@pytest.fixture
def app(browser):
    ctx = browser.new_context(viewport={"width": 430, "height": 900})
    page = ctx.new_page()
    a = App(page)
    yield a
    ctx.close()


def make_days(specs):
    """{ '2026-09-01': (sr, minutes, transfer) } -> app day records."""
    out = {}
    for iso, spec in specs.items():
        sr, minutes, transfer = (list(spec) + [0, 0])[:3]
        out[iso] = {"sr": sr, "minutes": minutes, "done": ["sts"] if minutes else [],
                    "notes": "", "transfer": transfer, "sit": {}}
    return out


def seed(**overrides):
    base = {
        "profile": {"name": "Sam", "startedOn": "2026-08-01"},
        "mode": "kid", "theme": None, "srMax": 10, "bpm": 120,
        "days": {}, "outLoud": [], "lastOpen": None,
    }
    base.update(overrides)
    return base
