# Steady Voice

A practice and progress-tracking web app for school-age children who stutter. Offline-capable, installable, no account, no server.

Built around **syllable-timed speech** as specified in the [Oakville Program](https://www.uts.edu.au/asrc) — the Australian Stuttering Research Centre's school-age treatment. Its Phase II trial in 6–11 year olds reported a 77% group mean reduction in stuttering severity 12 months post-treatment. That is Phase II evidence, not a randomised controlled trial, and the app says so on its home screen.

**This is practice scaffolding, not treatment.** There is essentially no high-quality efficacy evidence for stuttering apps in children. The honest job of one is adherence support and measurement alongside a speech pathologist.

---

## What it does

**Nine exercises**, grouped by what they train:

| Group | Exercises |
|---|---|
| Rhythm and rate | Syllable Time (STS, with metronome), Hybrid Session, Stretchy Speech (prolonged speech with a visual pacer) |
| Smooth mechanics | Gentle Starts (easy onset), Feather Touch (light articulatory contact), Wave Breathing |
| Building up | Word Ladder (GILCU), Stepping Stones (pausing and phrasing) |
| When a word gets stuck | Rescue Moves (pull-outs, cancellations, preparatory sets) |

Plus graded reading practice with a recorder, a conversation timer with prompts, and transfer tasks that take the technique out of the practice room.

**Saved recordings.** Every clip is kept on the device with its date, exercise and the words that were on screen, so an early recording can be played against a recent one — usually more convincing than any chart — and a single clip can be handed to a speech pathologist through the system share sheet. Stored in IndexedDB, listed and deleted under a Recordings tab in the grown-up view.

**A grown-up view** with daily severity ratings on either the Oakville 0–10 or Lidcombe 0–9 scale, per-situation ratings, 28-day trend charts, a practice log, and CSV export.

## Privacy

Everything stays on the device — ratings and settings in `localStorage`, saved audio in IndexedDB. No account, no upload, no analytics, no speech recognition anywhere. The only network requests the app makes are for the page itself and Google Fonts — [asserted by a test](tests/test_safety.py). Data leaves the device only when you deliberately export a CSV or share a recording. Recordings are the most sensitive thing here, so each has its own delete, the library has a delete-all, and **Erase all data** wipes the audio store as well as the ratings — with a test that proves it.

## Build and deploy

```bash
python3 build.py       # stdlib only, no dependencies
```

Emits two things from the single source `app/steadyvoice.body.html`:

- `app/steadyvoice.html` — standalone file, opens from disk on a computer
- `pwa/` — the installable app: built HTML, manifest, service worker, icons

The service worker's cache name is stamped with a hash of the build, so a redeploy always invalidates the old cache on every installed device.

Pushing to `main` builds and deploys `pwa/` to GitHub Pages via `.github/workflows/deploy.yml`. **[DEPLOY.md](DEPLOY.md)** covers installing it on Android and iOS so it works offline, and why a copied HTML file will not do the job on iOS.

## Tests

```bash
pip install pytest playwright
python3 -m pytest
```

122 tests. Playwright drives the real page in Chromium. `tests/test_safety.py` is the unusual one: it guards clinical content that would be harmful if it silently drifted — the practice dose, the prompting rules, the severity anchors. See [tests/README.md](tests/README.md), which also lists the nine real bugs the suite caught.

## Editing

`app/steadyvoice.body.html` is the source of truth — one self-contained file in four labelled layers (Storage, State, Content, Views). Storage is the only browser-coupled layer, so a React Native port replaces that one adapter. Never edit `app/steadyvoice.html` or `pwa/index.html`; both are generated.

## Licence

No licence granted. Published so it can be installed from a URL, not as an invitation to reuse.
