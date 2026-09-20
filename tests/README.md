# Steady Voice test suite

122 tests. Playwright drives the real page in Chromium; pure logic is exercised through `page.evaluate` against the live globals, because the app is one self-contained HTML file with no module system to import from.

## Running

```bash
pip install pytest playwright --break-system-packages
python3 -m pytest              # builds app/steadyvoice.html first, then runs
python3 -m pytest -v           # per-test names
python3 -m pytest tests/test_safety.py
```

The `build_app` fixture runs `build.py` before the session, so the tests always exercise the current `app/steadyvoice.body.html` rather than a stale build. Edit the `.body.html` file, not the built one.

## Layout

| File | Covers |
|---|---|
| `conftest.py` | Build fixture, browser fixture, the `App` page wrapper, seed helpers |
| `test_core.py` | Storage adapter, date maths, day records, streaks, `last(n)`, mode routing, theme |
| `test_practice.py` | All nine exercises, the metronome, hybrid session, word ladder, reading, talk timer |
| `test_parent.py` | Severity scales, situation ratings, charts, CSV export, settings, erase |
| `test_safety.py` | Escaping, the privacy claim, and the clinical content that must not drift |
| `test_pwa.py` | The offline install path — serves `pwa/` over real HTTP, because a service worker will not register from `file://` |

## What the safety tests are for

`test_safety.py` is the unusual one, and it is deliberate. Some of it is ordinary security — user-entered names, notes and log entries are checked for HTML injection in every place they render.

The rest guards **content that would be actively harmful if it silently drifted**:

- The Oakville practice dose (four to six sessions a day, five to ten minutes) is stated correctly.
- The prompting rules appear where a parent will actually see them, including "never as a response to a bump".
- Syllable Time warns against staccato, not just "say it to the beat".
- Every severity value has anchor text, on both the 0–10 and 0–9 scales.
- The MBS item numbers are all present.
- Clinic contact details are intact.
- The app still says it does not replace a speech pathologist.
- **No desensitisation exercise or courage-ladder framing has crept back in** — that was the wrong design for this child, and a test is a cheaper way to keep it out than remembering.

`test_privacy_claim_is_true_no_network_calls_are_made` asserts the app makes no requests beyond the page itself and Google Fonts. The app tells a parent nothing is uploaded; that claim is worth a test.

## Bugs this suite caught

Nine real ones, all now fixed:

1. **Erase all data did not erase.** `Object.assign({}, DEFAULTS, stored)` left `S.days` and `S.profile` pointing at the `DEFAULTS` objects on a fresh install, so every rating written also mutated `DEFAULTS` — and the wipe, which restores from `DEFAULTS`, handed the data straight back. Now deep-clones on boot.
2. **The streak reset every midnight.** `streak()` counted from today, so a child who had practised four days running saw a 0 the moment they opened the app before practising. Now counts from yesterday when today is still empty.
3. **The 28-day shift was computed from overlapping windows.** With fewer than 14 ratings, `slice(0,7)` and `slice(-7)` are largely the same rows, so three days of data reported a confident trend. Now compares non-overlapping halves and shows nothing below 8 ratings.
4. **Severity buttons were unusably small.** Eleven `aspect-ratio: 1` buttons across a 430px screen came out ~30px tall. Now `min-height: 44px`.
5. **Syllable sentences had no spaces in their text content.** The word gap was an empty `inline-block` spacer, which renders as zero-width whitespace — so the sentence reached a screen reader and the clipboard as "Thecatsatdown". Now real spaces with `word-spacing`.
6. **Recordings were unplayable on iPhone and iPad.** Every blob was hardcoded `audio/webm`, but Safari's MediaRecorder only ever produces MP4/AAC — it cannot make WebM. Now takes the type from `mediaRec.mimeType`.
7. **The app never asked to keep its data.** Everything the parent records is in `localStorage`, which browsers evict under space pressure or long disuse. Now calls `navigator.storage.persist()`, which WebKit grants on heuristics that include being installed to the home screen.
8. **Offline availability depended on Google Fonts loading.** The service worker registered on `window.load`, so a slow or unreachable font host delayed it — or lost it entirely if the app was closed first. Now registers immediately.
9. **The secure-origin guard missed `127.0.0.1`.** It compared `location.hostname` against the string `"localhost"`, so the worker silently never registered when served from a loopback IP. Now uses `window.isSecureContext`, which is the actual test.

Numbers 6 to 9 were all found by `test_pwa.py`. Number 8 surfaced only because this container blocks the font CDN — an environment quirk that happened to expose a real robustness bug.

## Notes

- Audio is not asserted directly. `AudioContext` is created but produces no audible output in headless Chromium, so the metronome tests assert the visual beat and the syllable highlight advancing instead.
- Tests that read on-screen copy use `app.text()`, which returns *rendered* text — `text-transform: uppercase` on `.eyebrow` headings applies, so those comparisons are case-insensitive. `app.all_text()` expands collapsed `<details>` first.
- The suite takes about two minutes. Each test gets a fresh browser context, so `localStorage` never leaks between them.
