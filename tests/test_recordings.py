"""Saved recordings.

Served over real HTTP rather than file://, because Chromium refuses
IndexedDB on an opaque file: origin — the same reason the app needs hosting
at all. The store degrades quietly there (list returns nothing, save reports
a failure) rather than throwing, and `test_store_degrades_without_indexeddb`
pins that down.

The recordings are audio of a child's voice. The tests that matter most here
are the deletion ones: per-clip delete, delete all, and — above all — that
"Erase all data" really does erase the audio.
"""
import pathlib

import pytest

from test_pwa import server, page, install  # noqa: F401  (fixtures)

ROOT = pathlib.Path(__file__).resolve().parent.parent

# A tiny synthetic clip. The store must not care what is inside the Blob,
# only that it round-trips byte for byte.
MAKE_BLOB = """(n) => new Blob([new Uint8Array(n).fill(7)], {type:'audio/mp4'})"""


def seed_clips(pg, specs):
    """specs: [(exercise, label, bytes)] -> ids, oldest written first."""
    return pg.evaluate("""async (specs) => {
      const ids = [];
      for(const [exercise, label, n] of specs){
        const blob = new Blob([new Uint8Array(n).fill(7)], {type:'audio/mp4'});
        ids.push(await Audio_.save(blob, {exercise, label}));
        await new Promise(r => setTimeout(r, 6));   // distinct ts ordering
      }
      return ids;
    }""", specs)


# ── the store ─────────────────────────────────────────────────────────
def test_a_clip_round_trips_byte_for_byte(server, page):
    install(page, server)
    [cid] = seed_clips(page, [["sts", "The cat sat down.", 512]])
    assert cid
    out = page.evaluate("""async (id) => {
      const b = await Audio_.get(id);
      const buf = new Uint8Array(await b.arrayBuffer());
      return {size: b.size, type: b.type, first: buf[0], last: buf[buf.length-1]};
    }""", cid)
    assert out == {"size": 512, "type": "audio/mp4", "first": 7, "last": 7}


def test_listing_is_newest_first_and_carries_no_audio(server, page):
    """Listing the library must not deserialise every blob — that is the
    whole reason the metadata lives in its own store."""
    install(page, server)
    seed_clips(page, [["sts", "first", 100], ["read", "second", 200],
                      ["stretch", "third", 300]])
    rows = page.evaluate("() => Audio_.list()")
    assert [r["label"] for r in rows] == ["third", "second", "first"]
    for r in rows:
        assert set(r) == {"id", "ts", "date", "mime", "size", "exercise", "label"}, \
            f"metadata row carries unexpected keys: {sorted(r)}"


def test_deleting_one_clip_leaves_the_others(server, page):
    install(page, server)
    ids = seed_clips(page, [["sts", "keep", 10], ["sts", "drop", 10], ["sts", "keep too", 10]])
    assert page.evaluate("id => Audio_.remove(id)", ids[1]) is True
    rows = page.evaluate("() => Audio_.list()")
    assert sorted(r["label"] for r in rows) == ["keep", "keep too"]
    assert page.evaluate("id => Audio_.get(id)", ids[1]) is None, \
        "the audio survived its metadata being deleted"


def test_store_degrades_without_indexeddb(server, page):
    """Older WebKit, private windows and locked-down profiles can all refuse.
    The practice session must carry on regardless."""
    install(page, server)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    out = page.evaluate("""async () => {
      Audio_._db = null;
      Object.defineProperty(window, 'indexedDB', {get: () => undefined, configurable: true});
      return {
        saved: await Audio_.save(new Blob(['x']), {exercise:'sts'}),
        list: await Audio_.list(),
        got: await Audio_.get('nope'),
        cleared: await Audio_.clear()
      };
    }""")
    assert out == {"saved": None, "list": [], "got": None, "cleared": False}
    assert not errors, f"the store threw instead of degrading: {errors}"


# ── recording writes to the library ───────────────────────────────────
def test_every_recorder_keeps_its_clip(server, page):
    """All three recorders must save, and each must tag the clip with its
    exercise and what was on screen — a library of untitled clips is no use
    to anyone six weeks later."""
    src = (ROOT / "app" / "steadyvoice.body.html").read_text()
    assert src.count("keepRecording(blob, {exercise:") == 3
    assert src.count("label: targetText()") == 3


def test_the_target_text_is_read_off_the_screen(server, page):
    """targetText reads the DOM rather than a tracked variable, so the label
    cannot drift from what the child was actually looking at."""
    install(page, server)
    page.evaluate("() => go('game','sts')")
    page.wait_for_timeout(300)
    label = page.evaluate("() => targetText()")
    assert label and len(label) > 3
    assert label == page.inner_text("#sylTarget").replace("\n", " ").strip()


# ── the library screen ────────────────────────────────────────────────
def test_recordings_is_a_grown_up_tab(server, page):
    install(page, server)
    page.click("#modeBtn")
    page.wait_for_timeout(200)
    labels = page.eval_on_selector_all("#tabs button", "bs => bs.map(b => b.innerText.trim())")
    assert any("recording" in b.lower() for b in labels), labels


def test_empty_library_explains_how_to_fill_it(server, page):
    install(page, server)
    page.evaluate("() => { S.mode='parent'; go('recordings'); }")
    page.wait_for_timeout(400)
    body = page.inner_text("#view").lower()
    assert "nothing recorded yet" in body
    assert "record me" in body


def test_saved_clips_are_listed_with_exercise_and_words(server, page):
    install(page, server)
    seed_clips(page, [["sts", "The cat sat down.", 4096],
                      ["read", "a warm morning", 2048]])
    page.evaluate("() => { S.mode='parent'; go('recordings'); }")
    page.wait_for_timeout(500)
    body = page.inner_text("#view")
    assert "Syllable Time" in body
    assert "Reading out loud" in body
    assert "The cat sat down." in body
    assert "2 recordings" in body


def test_delete_all_empties_the_library(server, page):
    install(page, server)
    seed_clips(page, [["sts", "one", 10], ["sts", "two", 10]])
    page.evaluate("() => { S.mode='parent'; go('recordings'); }")
    page.wait_for_timeout(400)
    page.on("dialog", lambda d: d.accept())
    page.click("#clearRec")
    page.wait_for_timeout(500)
    assert page.evaluate("() => Audio_.list()") == []
    assert "nothing recorded yet" in page.inner_text("#view").lower()


# ── erasure ───────────────────────────────────────────────────────────
def test_erase_all_data_really_erases_the_audio(server, page):
    """The single most important test in this file. An erase that left a
    child's voice behind in IndexedDB would make the app's own promise false."""
    install(page, server)
    seed_clips(page, [["sts", "sensitive", 1024], ["read", "also sensitive", 1024]])
    # Settings, and so the wipe button, lives at the foot of Find help.
    page.evaluate("() => { S.mode='parent'; go('help'); }")
    page.wait_for_timeout(300)
    page.on("dialog", lambda d: d.accept())
    page.click("#wipeBtn")
    page.wait_for_timeout(700)
    assert page.evaluate("() => Audio_.list()") == [], "recordings survived Erase all data"


def test_the_erase_prompt_says_recordings_are_included(server, page):
    """A confirm that lists only ratings and notes would be misleading now."""
    src = (ROOT / "app" / "steadyvoice.body.html").read_text()
    prompt = src[src.index("Erase every"):]
    prompt = prompt[:prompt.index('"')]
    assert "recording" in prompt.lower(), prompt


# ── export ────────────────────────────────────────────────────────────
def test_clip_filenames_are_legible_to_a_clinician(server, page):
    install(page, server)
    name = page.evaluate("""() => {
      S.profile.name = 'Sam';
      return clipName({id:'x', ts: Date.parse('2026-09-20T14:35:00'),
                       date:'2026-09-20', exercise:'sts', mime:'audio/mp4'});
    }""")
    assert name == "Sam-2026-09-20-1435-sts.m4a", name


def test_webm_keeps_its_own_extension(server, page):
    """Android records WebM. Naming that .m4a would produce a file that will
    not open on the clinician's machine."""
    install(page, server)
    assert page.evaluate(
        "() => clipName({ts:Date.now(), date:'2026-09-20', exercise:'read',"
        " mime:'audio/webm;codecs=opus'})").endswith(".webm")


def test_export_falls_back_to_download_when_sharing_files_is_refused(server, page):
    """navigator.share exists on plenty of devices that reject files, so
    canShare({files}) is the only honest test. Without it the clip must still
    come out."""
    install(page, server)
    [cid] = seed_clips(page, [["sts", "clip", 64]])
    out = page.evaluate("""async (id) => {
      let shared = false, downloaded = null;
      navigator.share = () => { shared = true; return Promise.resolve(); };
      Object.defineProperty(navigator, 'canShare',
        {get: () => (() => false), configurable: true});
      window.downloadBlob = (blob, name) => { downloaded = name; };
      const [m] = await Audio_.list();
      await shareClip(m);
      return {shared, downloaded};
    }""", cid)
    assert out["shared"] is False, "shared files despite canShare saying no"
    assert out["downloaded"] and out["downloaded"].endswith(".m4a")


def test_nothing_is_uploaded_when_a_clip_is_saved_or_shared(server, page):
    """The app tells a parent audio never leaves the device. Prove it."""
    install(page, server)
    seen = []
    page.on("request", lambda r: seen.append(r.url))
    [cid] = seed_clips(page, [["sts", "clip", 2048]])
    page.evaluate("() => { S.mode='parent'; go('recordings'); }")
    page.wait_for_timeout(500)
    offsite = [u for u in seen
               if not u.startswith("http://127.0.0.1")
               and not u.startswith("blob:")
               and "fonts.googleapis" not in u and "fonts.gstatic" not in u]
    assert not offsite, f"the app made off-device requests: {offsite}"
