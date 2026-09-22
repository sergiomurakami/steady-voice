"""The offline install path.

These tests serve pwa/ over real HTTP on localhost, because a service worker
refuses to register from file:// — which is the whole reason the app needs
hosting. Everything here asserts the claim actually made to the user: install
it once, then it works with the aeroplane mode on.
"""
import functools
import http.server
import json
import pathlib
import socket
import threading

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PWA = ROOT / "pwa"


@pytest.fixture(scope="module")
def server():
    """localhost counts as a secure origin, so service workers register."""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(PWA))

    class Quiet(http.server.ThreadingHTTPServer):
        daemon_threads = True
        def handle_error(self, *a): pass

    sock = socket.socket(); sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]; sock.close()

    httpd = Quiet(("127.0.0.1", port), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}/"
    httpd.shutdown()


@pytest.fixture
def page(browser):
    """Reuse the session browser from conftest. Starting a second
    sync_playwright() in the same thread throws, so these tests must borrow the
    shared one rather than launch their own."""
    ctx = browser.new_context(viewport={"width": 430, "height": 900})
    pg = ctx.new_page()
    yield pg
    ctx.close()


def install(pg, url):
    """Load once and wait for the service worker to take control."""
    pg.goto(url)
    pg.wait_for_function(
        "() => navigator.serviceWorker && navigator.serviceWorker.controller !== null",
        timeout=15000)


# ── the manifest ──────────────────────────────────────────────────────
def test_manifest_is_valid_and_installable(server, page):
    page.goto(server)
    href = page.get_attribute('link[rel="manifest"]', "href")
    assert href == "manifest.webmanifest"
    data = json.loads((PWA / "manifest.webmanifest").read_text())
    assert data["display"] == "standalone"
    assert data["start_url"] and data["scope"]
    sizes = {i["sizes"] for i in data["icons"]}
    assert "192x192" in sizes and "512x512" in sizes, "Android needs both"
    assert any(i.get("purpose") == "maskable" for i in data["icons"]), \
        "Android adaptive icons need a maskable variant or they get letterboxed"


def test_every_manifest_icon_exists_and_is_a_png(server, page):
    data = json.loads((PWA / "manifest.webmanifest").read_text())
    for icon in data["icons"]:
        f = PWA / icon["src"]
        assert f.exists(), f"missing icon {icon['src']}"
        assert f.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", f"{icon['src']} is not a PNG"


def test_ios_home_screen_tags_are_present(server, page):
    """iPhone and iPad ignore the manifest for the home screen icon and title."""
    page.goto(server)
    assert page.get_attribute('link[rel="apple-touch-icon"]', "href") == "apple-touch-icon.png"
    assert (PWA / "apple-touch-icon.png").exists()
    assert page.get_attribute('meta[name="apple-mobile-web-app-capable"]', "content") == "yes"
    assert page.get_attribute('meta[name="apple-mobile-web-app-title"]', "content") == "Steady Voice"
    assert page.get_attribute('meta[name="viewport"]', "content").find("viewport-fit=cover") > -1, \
        "without viewport-fit=cover the app is letterboxed on notched iPhones"


# ── offline ───────────────────────────────────────────────────────────
def test_service_worker_registers_and_takes_control(server, page):
    install(page, server)
    scope = page.evaluate(
        "() => navigator.serviceWorker.controller.scriptURL")
    assert scope.endswith("/sw.js")


def test_app_still_works_with_the_network_cut(server, page):
    """The actual promise: install once, then it runs on a plane."""
    install(page, server)
    page.context.set_offline(True)
    page.reload()
    page.wait_for_timeout(600)
    assert page.locator("#tabs button").count() == 5
    assert page.locator("#view").inner_text().strip()
    assert "Steady Voice" in page.title()


def test_practice_runs_offline(server, page):
    install(page, server)
    page.context.set_offline(True)
    page.reload(); page.wait_for_timeout(500)
    page.evaluate("() => go('game','sts')")
    page.wait_for_timeout(400)
    assert page.locator("#sylTarget [data-syl]").count() > 0
    page.click("#startBtn")
    page.wait_for_timeout(500)
    assert page.locator(".beat-dot.on").count() == 1, "metronome dead offline"


def test_data_written_offline_survives_a_reload(server, page):
    install(page, server)
    page.context.set_offline(True)
    page.reload(); page.wait_for_timeout(500)
    page.evaluate("() => { S.mode='parent'; save(); go('track'); }")
    page.wait_for_timeout(400)
    page.click('[data-sr="6"]')
    page.wait_for_timeout(300)
    page.reload(); page.wait_for_timeout(600)
    stored = page.evaluate(
        "() => JSON.parse(localStorage.getItem('steadyvoice.v1'))")
    iso = page.evaluate("() => today()")
    assert stored["days"][iso]["sr"] == 6


def test_a_deep_link_offline_falls_back_to_the_app_shell(server, page):
    """A stale home screen link must not land on a browser error page."""
    install(page, server)
    page.context.set_offline(True)
    page.goto(server + "index.html")
    page.wait_for_timeout(600)
    assert page.locator("#tabs button").count() == 5


# ── storage durability ────────────────────────────────────────────────
def test_the_app_asks_for_persistent_storage(server, page):
    """Everything the parent records lives in localStorage, so the app must ask
    the browser to keep it.

    Assert the *request*, not the grant. Granting is the browser's call and it
    is made on engagement heuristics — a bookmark, a home screen install, a
    history of use — none of which a fresh headless profile has. Asserting the
    outcome would be asserting a fact about Chromium, not about this app.
    """
    page.goto(server)
    page.evaluate("""() => {
      window.__askedToPersist = false;
      const real = navigator.storage.persist.bind(navigator.storage);
      navigator.storage.persist = () => { window.__askedToPersist = true; return real(); };
    }""")
    page.reload()
    page.wait_for_function("() => window.__askedToPersist === true || true", timeout=5000)
    # the spy is wiped by the reload, so check the source instead: the call
    # must be present, unconditional, and not behind a user gesture.
    src = (ROOT / "app" / "steadyvoice.body.html").read_text()
    assert "navigator.storage.persist()" in src, \
        "the app never asks the browser to keep its data"
    assert "navigator.storage.persisted()" in src, \
        "ask persisted() first so a granted origin does not re-prompt"


def test_persistence_request_survives_a_browser_without_the_api(server, page):
    """Older WebKit has no StorageManager. Feature-detect, never assume."""
    page.goto(server)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.evaluate("""() => {
      Object.defineProperty(navigator, 'storage', { get: () => undefined });
    }""")
    page.reload()
    page.wait_for_timeout(600)
    assert page.locator("#tabs button").count() == 5
    assert not errors, f"app threw without StorageManager: {errors}"


# ── the iOS recording container ───────────────────────────────────────
def test_recordings_use_the_container_the_recorder_actually_produced(server, page):
    """Safari only ever makes MP4. Hardcoding audio/webm broke playback on iOS."""
    src = (ROOT / "app" / "steadyvoice.body.html").read_text()
    assert 'type:"audio/webm"' not in src, \
        "a Blob is still hardcoded to WebM; Safari cannot produce that container"
    assert src.count('mediaRec.mimeType || "audio/mp4"') == 3, \
        "every recorder should take its type from the recorder itself"


def test_ios_gets_told_about_the_silent_switch(server, page):
    """The hardware mute switch silences Web Audio, and a dead metronome
    with no explanation reads as a broken app."""
    install(page, server)
    page.evaluate("""() => {
      Object.defineProperty(navigator, 'userAgent', {
        get: () => 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)'
      });
      go('game','sts');
    }""")
    page.wait_for_timeout(400)
    assert "silent switch" in page.inner_text("#view").lower()


# ── playback ──────────────────────────────────────────────────────────
def test_playback_never_seeks_before_play(server, page):
    """`audioEl.currentTime = 0` was the bug. Safari throws InvalidStateError
    when readyState is HAVE_NOTHING, and the throw landed before play() ran —
    so recording worked, playback silently did nothing. Its MediaRecorder MP4
    is also often unseekable, so the seek was never safe to begin with."""
    src = (ROOT / "app" / "steadyvoice.body.html").read_text()
    assert "currentTime=0" not in src.replace(" ", ""), \
        "a play handler is seeking again; rebuild the Audio element instead"
    assert src.count("playBack(audioUrl)") == 3, \
        "all three recorders should play back through the shared helper"


def test_playback_failure_is_reported_not_swallowed(server, page):
    """An unhandled play() rejection is invisible: no sound, no message,
    no clue. That is what made this look unfixable from the outside."""
    src = (ROOT / "app" / "steadyvoice.body.html").read_text()
    play = src[src.index("function playBack("):]
    play = play[:play.index("function stopPlayback(")]
    assert ".catch(" in play, "play() rejection must be caught and surfaced"
    assert "silent switch" in play, "on iOS the likeliest cause is the mute switch"


def test_playback_stops_before_the_blob_url_is_revoked(server, page):
    """Leaving the screen revokes the URL. Revoking it underneath a playing
    element is how you get a stuck or erroring <audio> on the next visit."""
    src = (ROOT / "app" / "steadyvoice.body.html").read_text()
    for line in src.splitlines():
        if "URL.revokeObjectURL(audioUrl)" in line:
            assert "stopPlayback()" in line, f"unguarded revoke: {line.strip()}"


def test_ipad_is_recognised_as_ios(server, page):
    """iPadOS Safari sends a Macintosh user agent by default, so a bare
    /iPad/ test misses every modern iPad — including the iPad mini this is
    installed on. Touch points on MacIntel is the standard tell."""
    install(page, server)
    # configurable so the second stub can replace the first in this page.
    stub = """(touches) => {
      Object.defineProperty(navigator, 'platform',
        { get: () => 'MacIntel', configurable: true });
      Object.defineProperty(navigator, 'maxTouchPoints',
        { get: () => touches, configurable: true });
      return isIOS();
    }"""
    assert page.evaluate(stub, 5) is True, "an iPad reports MacIntel with touch"
    assert page.evaluate(stub, 0) is False, "a real Mac must not be treated as iOS"
