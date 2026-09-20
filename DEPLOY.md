# Deploying Steady Voice, and installing it offline

Live at **https://sergiomurakami.github.io/steady-voice/**

Three target devices: a Galaxy S23 Ultra on Android 16, an iPhone 13, and an iPad mini 6. All three end up with a real app icon that opens full screen and works with no signal.

---

## Why this needs hosting at all

The honest answer to "can't I just copy the HTML file onto the phone": no, not well.

- **A service worker cannot register from `file://`.** That is what makes the app work offline properly. Without it you are relying on the browser's ordinary HTTP cache, which is evicted whenever the browser feels like it.
- **`file://` pages get an opaque origin.** `localStorage` behaviour there is inconsistent across browsers and unreliable on iOS in particular. Every daily severity rating lives in `localStorage`. Losing it is not a cosmetic problem.
- **No home screen icon, no full screen.** It opens as a page in a browser tab, with browser chrome, and has to be found in Files each time.

Hosting a few static files over HTTPS fixes all of that at once. **Nothing about this sends data anywhere** — the files are static, there is no server side, and every rating stays in the browser on the device. The URL being public means the *app* is public, not the data.

On a computer, `app/steadyvoice.html` still opens straight from disk. That is fine for a quick look; it is not the install path.

---

## What lives where

The Google Drive folder is the complete project. The GitHub repo is a **subset** — only what Pages needs to build and serve the app.

| | In the repo | In Drive only |
|---|---|---|
| `app/`, `pwa/`, `build.py`, `tests/`, workflow | yes | yes |
| `README.md`, `DEPLOY.md` | yes | yes |
| `knowledge-base/` | **no** | yes |
| `printables/` (both PDF manuals) | **no** | yes |

`.gitignore` enforces the split. **Do not remove those two lines.** The knowledge base is clinical material about a specific child and the manuals are derived from it; the repo is public, and anything committed to a public repo stays in its history even after you delete the file.

Because those folders are outside git, Drive is their only copy. Drive is a sync service, not a backup — a bad sync propagates everywhere. Keep a copy of `knowledge-base/` and `printables/` somewhere else.

---

## How deployment works

`.github/workflows/deploy.yml` runs on every push to `main`:

1. Checks out the repo, sets up Python 3.12.
2. Runs `python3 build.py` — stdlib only, no dependencies to install.
3. Uploads `pwa/` as a Pages artifact and deploys it.

Building in CI rather than trusting the committed build means `pwa/index.html` and `pwa/sw.js` can never drift from `app/steadyvoice.body.html`, and the cache-busting hash is always computed from what is actually being shipped.

**Pages setting, one time only:** Settings → Pages → Build and deployment → Source: **GitHub Actions**. Nothing else on that page needs touching — no branch, no folder, no custom domain. Ignore the "GitHub Pages Jekyll" and "Static HTML" suggested workflows; the repo already has its own.

### The ordering trap

If you push *before* setting the source to GitHub Actions, the build job succeeds and the **deploy job fails** — Pages is not yet accepting deployments. Setting the source afterwards does not retry it on its own. Trigger a fresh run:

**Actions** tab → **Deploy Steady Voice** in the left sidebar → **Run workflow** → **Run workflow**. (The workflow declares `workflow_dispatch`, so that button is there.) Or push any commit.

Green tick on the Actions tab means it is live. Until the first successful deploy, the Pages URL returns 404 and the Pages settings page says "Workflow details will appear here once your site has been deployed."

---

## Updating it later

Edit `app/steadyvoice.body.html` — **never** `app/steadyvoice.html` or `pwa/index.html`, both of which are generated. Then:

```bash
cd "AI Projects/Stuttering"
python3 -m pytest        # optional, but it has caught nine real bugs
git add -A
git commit -m "what changed"
git push
```

The service worker's cache name is stamped with a hash of the built app (`steady-voice-<hash>`), so a changed app always gets a new cache and the old one is deleted on activation. This is the step people forget when they hand-maintain a `v1`/`v2` string, and forgetting it means the phones keep serving the old app forever with no error to notice.

**On the device**, the new version appears on the next launch after the worker updates — usually the second launch, since the first is still being served by the old worker while the new one installs in the background. To force it: close the app fully and reopen twice.

---

## Installing it

### Galaxy S23 Ultra (Android 16, Chrome)

1. Open the URL in **Chrome**.
2. Chrome usually offers **Install app** in a banner. If not: **⋮ menu → Add to Home screen → Install**.
3. Tap **Install**.

You get a real icon in the app drawer, no browser bars, and its own entry in the app switcher. Chrome grants persistent storage readily once a PWA is installed, so the ratings are safe.

### iPhone 13 and iPad mini 6

**Use Safari.** Other iOS browsers can add to the home screen, but Safari is the reliable path and the one Apple tests.

1. Open the URL in **Safari**.
2. Tap **Share** (the square with the arrow).
3. Scroll down, tap **Add to Home Screen**.
4. Name it, tap **Add**.

**Adding it to the home screen is not optional on iOS.** Opened as an ordinary Safari tab it is just a website and its storage is subject to eviction. Installed to the home screen it runs standalone, and WebKit grants persistent storage on heuristics that explicitly include "whether the website is opened as a Home Screen Web App". The app calls `navigator.storage.persist()` on every load; the home screen install is what makes WebKit likely to say yes.

---

## Check it actually works offline

Do this once per device, before relying on it.

1. Open the installed app and use it for a moment — enough for the service worker to install.
2. **Close it completely** (swipe it away).
3. Turn on **aeroplane mode**.
4. Open it again from the icon.

It should open normally, the metronome should click, and the daily rating should save. An error page means the service worker did not install — open it once more with a connection and try again.

---

## What each platform will and will not do

| | Android / Chrome | iOS / Safari |
|---|---|---|
| Home screen icon, full screen | Yes | Yes |
| Works offline after install | Yes | Yes |
| Install prompt | Automatic banner | Manual, via Share menu |
| Persistent storage | Granted readily once installed | Granted on heuristics; home screen install is the main one |
| Microphone recording | Yes, WebM | Yes, **MP4** — the app reads the container from the recorder rather than assuming |
| Metronome click | Yes | **Silenced by the hardware mute switch.** The app says so on the Syllable Time screen; the visual beat works either way |
| Speech synthesis (Hear it) | Yes | Yes |
| Storage cap | Generous | Tighter; this app stores kilobytes, so not a concern |

---

## Things that will bite you

**Pick one URL and stick to it.** The app also exists as a Claude artifact link. That is a different origin, so it has a completely separate `localStorage` — ratings entered there will never appear in the Pages version, silently, with no error. The Pages URL is the real one; it needs no Claude login on the child's device. Treat the artifact link as a preview only.

**The silent switch on the iPhone.** Web Audio obeys the physical mute switch. A missing click on the iPhone is almost always that, not a bug. The four dots and the highlighted syllable carry the beat visually regardless, so the exercise still works muted.

**Two devices do not share data.** Storage is per browser, per device. If the daily rating happens on your phone, keep doing it on your phone. **Export CSV** moves a copy anywhere.

**Clearing Safari history clears the app's data** on iOS. Export the CSV occasionally — that file is the backup, and it is what you take to appointments anyway.

**Private/incognito windows forget everything.** Not a place to keep ratings.

---

## If you ever move off GitHub

**Cloudflare Pages** or **Netlify Drop**: run `python3 build.py`, then drag the `pwa/` folder into their uploader. Free HTTPS, about two minutes, no git. Same install steps afterwards. You lose the automatic rebuild on push — you would re-drag the folder after each change. Cloudflare Pages also serves from a private repo for free, which GitHub Pages does not.

Moving hosts changes the origin, which means a new, empty `localStorage` on every installed device. Export the CSV first.
