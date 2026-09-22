# 7. Steady Voice — build notes and porting spec

The app in `app/`. A single self-contained HTML file so it runs offline from disk, from a hosted URL, or installed to a home screen — and so the whole thing ports cleanly to React Native later.

**Built for the profile in §8**: a child who stutters frequently in every context, including one-on-one with a parent, and who is socially confident, unafraid to speak and not ashamed of stuttering. That premise drives every decision below.

---

## What it does

**Two modes, one data store.** The person icon in the header switches between the child's view and the grown-up view. They share one history — the thing no existing app in this category does (§6).

### Child's view

| Tab | What it holds |
|---|---|
| **Today** | Streak, three rotating practice missions (always opening with a rhythm-and-rate one), today's out-loud job |
| **Practice** | Nine exercises grouped by what they train |
| **Read** | Four levels: words → phrases → sentences → passages. Recorder and device-voice model |
| **Out Loud** | Transfer jobs graded by how hard the situation is to hold technique in, plus a log |
| **Talk** | Question cards and a 10-minute timer for structured parent–child conversation |

**The nine exercises**

*Rhythm and rate* — the core for this profile

1. **Syllable Time** — syllable-timed speech per the Oakville Program. Real metronome (Web Audio click, 60–200 bpm), four-beat visual, and the target sentence lit syllable by syllable in time with the beat. Short and long sentence sets. The tempo persists between sessions.
2. **Hybrid Session** — the Oakville later-Stage-1 structure. A two-phase timer: first half syllable talking, second half natural speech, with an adjustable ratio slider (30–80% STS) and session length (6–20 min). Chimes at the changeover. Full run-it instructions on the same screen.
3. **Stretchy Speech** — prolonged speech with an animated travelling-waveform pacer, rate adjustable.

*Smooth mechanics*

4. **Gentle Starts** — easy onset, vowel-initial words and sentences
5. **Feather Touch** — light articulatory contact, plosive-initial words
6. **Wave Breathing** — regulated breathing, 4s in / 1.5s hold / 5.5s speak-out

*Building up*

7. **Word Ladder** — GILCU, one word to six. A bumpy rung drops back one
8. **Stepping Stones** — pausing and phrasing, sentences marked with pause points

*When a word gets stuck*

9. **Rescue Moves** — pull-outs, cancellations, preparatory sets

Every exercise carries a "why this one" panel naming the technique and its evidence.

### Grown-up view

| Tab | What it holds |
|---|---|
| **Today** | Daily severity rating (0–10 Oakville, switchable to 0–9 Lidcombe), optional per-situation ratings across eight contexts, technique-in-real-talk counter, notes, practice summary |
| **Progress** | 28-day severity chart with 7-day rolling average, **severity by situation** bar chart, technique-transfer vs practice-days chart, appointment table, CSV export, print |
| **Guides** | Oakville explained in full, why it bumps everywhere, what school age changes, keeping an eye on the emotional side, five clinician questions, school accommodations, rating consistently, funding |
| **Find help** | Directory from §5, plus settings and data erase |

---

## What changed from the first build, and why

The first version assumed the common presentation: an anxious, avoidant, embarrassed child. That was the wrong target. §8 has the clinical argument; this is the mechanical diff.

| Removed | Replaced with |
|---|---|
| **Super Bumps** (voluntary stuttering) | **Syllable Time** — there is no fear response to desensitise, and STS is the treatment that actually fits |
| **Brave missions**, graded by nerve | **Out Loud** jobs, graded by how hard the situation is to *hold technique in* |
| **Avoidance event counter** | **Situation ratings** — severity by context, to test whether context matters at all |
| **Brave moments counter** | **Technique used in real conversation** counter |
| Guides centred on shame, teasing and self-disclosure | Oakville explained properly; the motor-vs-anxiety argument; a light-touch section on monitoring the emotional side without manufacturing worry |
| — | **Hybrid Session**, the Oakville later-Stage-1 structure |
| Lidcombe 0–9 scale, fixed | Oakville 0–10 default, switchable in settings |

---

## Design decisions, and why

**The metronome is real, not decorative.** Web Audio oscillator click, accented on beat one, with a four-dot visual and syllable-by-syllable highlighting of the target sentence. Tempo starts slow and the copy is explicit that speed only comes once slow is effortless. This is the exercise the whole app is built around, so it got the engineering.

**Legato is enforced by copy, not by code.** The guide's warning about staccato is the easiest thing to get wrong at home, so it appears on the exercise screen, in the "getting it right" panel, and in the guides.

**Situation ratings answer the actual open question.** The child bumps in public *and* one-on-one. Over a few weeks the severity-by-situation chart either shows level bars — confirming a motor driver and simplifying the plan — or one context standing clear, which is worth naming to a clinician. Oakville explicitly permits situation-specific ratings, so this is sanctioned, not invented.

**Self-rating, never machine scoring.** No speech recognition. Automatic stutter detection is not reliably solved, and telling a child they failed when they did not is worse than useless.

**Recording is for listening back.** Blob URL, revoked on leaving the screen. On the Syllable Time screen the prompt is specifically "is it even and joined up, or chopped?" — which is what the recording is actually for.

**Transfer gets equal billing with practice.** Its own tab, its own counter, its own chart. Clinic fluency is easy; carrying it into ordinary talk is where programs succeed or fail, and this child is unusually well placed to do it.

**The prompting rules are in the app.** No more than one prompt an hour, comfortable settings only, never right after a bump. That last one is the rule most likely to be broken by a well-meaning parent, and breaking it is how a child learns to hate the technique.

**No account, no cloud, no analytics.** `localStorage`, keyed `steadyvoice.v1`, one device. CSV export is the backup. There is an erase-everything button.

**It says what it isn't.** Disclaimers on the child's home screen and in the guides: the Oakville treatment guide is explicit that it is not designed to be run by a parent without clinician supervision.

**Visual identity.** Marine palette — deep teal ink, amber accent, neutrals biased green. The signature mark is a waveform: the header rule (which gains amplitude with the streak), the Stretchy Speech pacer, the breathing orb, the area fill under the severity chart. A waveform is literally the child's voice, and it can be even or ragged.

Typography: Bricolage Grotesque for display, Source Serif 4 for the guides, IBM Plex Sans for UI, syllable targets and tabular figures. Chart colours were validated for colour-blind separation and contrast in both themes rather than picked by eye.

---

## Porting to React Native

Four labelled layers, in this order in the file:

1. **`Storage`** — the *only* browser-coupled layer. Two methods, both wrapped in try/catch. Swap for `AsyncStorage`; nothing else changes.
2. **State** — plain functions over a plain object. `day(iso)`, `setDay()`, `streak()`, `last(n)`. Pure. Moves across untouched.
3. **Content** — `STS_SHORT`, `STS_LONG`, `EASY_ONSET`, `LIGHT_CONTACT`, `STRETCHY`, `PHRASING`, `LADDER`, `RESCUE`, `TALK_PROMPTS`, `READING`, `OUT_LOUD`, `SITUATIONS`, `GAMES`, `WHY`. Plain arrays and objects. Moves across untouched.
4. **Views** — functions returning `{html, mount}`. The only things to rewrite as components.

| Web | React Native |
|---|---|
| `localStorage` | `@react-native-async-storage/async-storage` |
| `MediaRecorder` + `getUserMedia` | `expo-av` `Audio.Recording` |
| `speechSynthesis` | `expo-speech` |
| Web Audio metronome click | `expo-av` short sound, or `react-native-sound` — **use a scheduled audio clock, not `setInterval`**, if you want tight timing |
| Inline SVG charts | `react-native-svg` (the path maths is already framework-free) |
| `Blob` + anchor download for CSV | `expo-file-system` + `expo-sharing` |

**Metronome caveat.** The web version drives the beat with `setInterval` and fires a fresh oscillator per tick. That is fine at 60–200 bpm for a speech pacer, where a few milliseconds of jitter is inaudible against a spoken syllable — but it is not sample-accurate. If you ever want it tighter, schedule ahead against `AudioContext.currentTime` rather than firing on the timer.

---

## The state shape

```js
{
  profile: { name: "", startedOn: "2026-09-08" },
  mode: "kid" | "parent",
  theme: "light" | "dark" | null,
  srMax: 10,             // 10 = Oakville 0–10 · 9 = Lidcombe 0–9
  bpm: 120,              // syllable-timed speech tempo, persisted
  days: {
    "2026-09-08": {
      sr: 0..srMax | null,   // whole-day severity rating
      minutes: 0,            // practice logged
      done: ["sts", ...],    // exercise ids completed today
      notes: "",             // for the speech pathologist
      transfer: 0,           // technique used in real conversation
      sit: { solo: 4, group: 6, excited: 8 }   // optional per-situation ratings
    }
  },
  outLoud: [ { date, text } ],
  lastOpen: "2026-09-08"
}
```

CSV columns: `date, severity_rating_0_N, practice_minutes, technique_used_in_real_talk, exercises, sit_solo … sit_tired, notes`.

Situation keys: `solo, group, excited, reading, school, public, phone, tired`.

---

## Tests

110 tests in `tests/`, Playwright driving the real page. `python3 -m pytest` from the project root — the suite rebuilds `app/steadyvoice.html` from the body file first, so it always tests current source. `tests/README.md` has the detail.

Five real bugs it caught, all fixed:

1. **Erase all data did not erase** — a shallow `Object.assign` over `DEFAULTS` left `S.days` aliasing the defaults object on a fresh install, so the wipe restored the data it was meant to destroy.
2. **The streak reset every midnight** — counting from today showed a 0 to a child who opened the app before practising.
3. **The 28-day shift used overlapping windows** — three days of ratings produced a confident-looking trend computed from the same rows twice.
4. **Severity buttons were ~30px tall** on a phone. Now 44px minimum.
5. **Syllable sentences had no spaces in their text content** — the word gap was a zero-width `inline-block`, so a screen reader got "Thecatsatdown".

`tests/test_safety.py` also pins the clinical content: the Oakville practice dose, the prompting rules, the staccato warning, severity anchors on both scales, the MBS item numbers, clinic contact details, and a check that no desensitisation exercise or courage-ladder framing has crept back in.

---

## Known limits

- **No service worker.** Opened from a file or installed to a home screen it works offline anyway; a hosted copy needs a network hit on first load.
- **`speechSynthesis` voice quality varies by device**, and it cannot demonstrate syllable-timed speech — it is a model for the ordinary-speech exercises only. The metronome is what models STS.
- **`MediaRecorder` is unavailable in some iOS browser contexts.** The app says so rather than failing silently.
- **The %SS estimator was deliberately left out.** Approximating it at home is noisy enough to be misleading, and severity ratings are what clinicians actually ask parents for.
- **Syllable splits are hand-authored** in `STS_SHORT` / `STS_LONG`. There is no automatic syllabifier, because English syllabification by algorithm is wrong often enough to teach the child the wrong thing. Add sentences by hand, with hyphens.
- **Content is fixed.** Edit the content layer directly as the child outgrows it.

---

## Worth adding next, in order of value

1. **A self-rating mode for the child.** The Oakville guide says children from about age 9 can be trained to rate their own severity alongside the parent, which surfaces school and peer information a parent never sees. Two series on the same chart — parent rating and child rating — with the gap between them as its own signal.
2. **A "coming up" module** — prepare for a named speaking situation (an oral presentation Thursday, a phone call) with rehearsal in technique.
3. **Clinician-set targets** — let a speech pathologist set the week's practice schedule and have the parent view report against it.
4. **PDF export of the appointment summary**, so it can be emailed rather than opened as a CSV.
