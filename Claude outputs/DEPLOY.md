# Getting Steady Voice onto the phones and iPad, working offline

Three devices: a Galaxy S23 Ultra on Android 16, an iPhone 13, and an iPad mini 6. All three end up with a real app icon that opens full screen and works with no signal.

---

## Why this needs hosting at all

The honest answer to "can't I just copy the HTML file onto the phone": no, not well.

- **A service worker cannot register from `file://`.** That is the thing that makes an app work offline properly. Without it you are relying on the browser's ordinary HTTP cache, which is evicted whenever the browser feels like it.
- **`file://` pages get an opaque origin.** `localStorage` behaviour there is inconsistent across browsers and unreliable on iOS in particular. Every daily severity rating lives in `localStorage`. Losing it is not a cosmetic problem.
- **No home screen icon, no full screen.** It opens as a page in a browser tab, with browser chrome, and the child has to go find it in Files each time.

Hosting a few static files over HTTPS fixes all of that at once. **Nothing about this sends data anywhere** — the files are static, there is no server side, and every rating stays in the browser on the device. The URL being public just means the *app* is public, not the data.

---

## One-time setup: GitHub Pages

Free, HTTPS, permanent URL, no login on any device.

**1. Put the workflow file where GitHub expects it.**

The deploy workflow is in the folder as `deploy-workflow.yml`. It has to live at `.github/workflows/deploy.yml` — dot-folders cannot be written into Google Drive from here, so this one move is manual and it is the only manual step:

```bash
cd "AI Projects/Stuttering"
mkdir -p .github/workflows
mv deploy-workflow.yml .github/workflows/deploy.yml
```

**2. Create the repo and push.**

```bash
git init
git add .
git commit -m "Steady Voice"
git branch -M main
git remote add origin git@github.com:<you>/steady-voice.git
git push -u origin main
```

**3. Turn Pages on.** Repo → **Settings → Pages → Build and deployment → Source: GitHub Actions**. That is the only setting to change; the workflow in `.github/workflows/deploy.yml` does the rest.

**4. Wait for the green tick** on the Actions tab. Your URL will be:

```
https://<you>.github.io/steady-voice/
```

The workflow runs `build.py` on every push to `main`, so `pwa/index.html` and `pwa/sw.js` are always rebuilt from `app/steadyvoice.body.html`. You never commit a stale build.

**On the repo being public.** Pages on a private repo needs a paid plan. A public repo is fine here — there is no data in it, and no credentials. If you would rather it not be public, Cloudflare Pages gives free HTTPS from a private repo.

---

## Installing it

### Galaxy S23 Ultra (Android 16, Chrome)

1. Open the URL in **Chrome**.
2. Chrome will usually offer **Install app** in a banner. If not: **⋮ menu → Add to Home screen → Install**.
3. Say **Install**.

You get a real icon in the app drawer, no browser bars, and it appears in the Android app switcher as its own app. Chrome grants persistent storage readily once a PWA is installed, so the ratings are safe.

### iPhone 13 and iPad mini 6

**Use Safari.** Other browsers on iOS can add to the home screen, but Safari is the reliable path and the one Apple tests.

1. Open the URL in **Safari**.
2. Tap the **Share** button (square with the arrow).
3. Scroll down, tap **Add to Home Screen**.
4. Name it and tap **Add**.

**Adding it to the home screen is not optional on iOS.** Opened as an ordinary Safari tab it is just a website, and its storage is subject to eviction. Installed to the home screen it runs standalone, and WebKit grants persistent storage on heuristics that explicitly include "whether the website is opened as a Home Screen Web App". The app calls `navigator.storage.persist()` on every load; the home screen install is what makes WebKit likely to say yes.

---

## Check it actually works offline

Do this once per device, before you rely on it.

1. Open the installed app and use it for a moment — enough for the service worker to install.
2. **Close it completely** (swipe it away).
3. Turn on **aeroplane mode**.
4. Open it again from the icon.

It should open normally, the metronome should click, and the daily rating should save. If you get an error page, the service worker did not install — open it once more with a connection and try again.

---

## Updating it later

Push to `main`. The workflow rebuilds and redeploys.

The service worker cache name is stamped with a hash of the built app (`steady-voice-<hash>`), so a changed app always gets a new cache and the old one is deleted on activation. This is the step people forget when they hand-maintain a `v1`/`v2` string, and forgetting it means the phones keep serving the old app forever with no error to notice.

**On the device**, the new version is picked up on the next launch after the worker updates — usually the second launch, since the first one is still being served by the old worker while the new one installs in the background. If you want it immediately: close the app fully and reopen twice.

---

## What each platform will and will not do

| | Android / Chrome | iOS / Safari |
|---|---|---|
| Home screen icon, full screen | Yes | Yes |
| Works offline after install | Yes | Yes |
| Install prompt | Automatic banner | Manual, via Share menu |
| Persistent storage | Granted readily once installed | Granted on heuristics; home screen install is the main one |
| Microphone recording | Yes, WebM | Yes, **MP4** — the app now reads the container from the recorder instead of assuming |
| Metronome click | Yes | **Silenced by the hardware mute switch.** The app says so on the Syllable Time screen. The visual beat keeps working either way |
| Speech synthesis (Hear it) | Yes | Yes |
| Storage cap | Generous | Tighter; this app stores kilobytes, so not a concern |

---

## Things that will bite you

**The silent switch on the iPhone.** Web Audio obeys the physical mute switch. If the click is missing on the iPhone, that is almost always why — not a bug. The four dots and the highlighted syllable carry the beat visually regardless, so the exercise still works muted.

**Pick one URL and stick to it.** The app also exists as a Claude artifact link. That is a different origin, so it has a completely separate `localStorage` — ratings entered there will not appear in the Pages version and vice versa, silently, with no error. Use the Pages URL as the real one; it needs no Claude login on his device. Treat the artifact link as a preview only.

**Two devices do not share data.** Storage is per browser, per device. If the daily rating happens on your phone, keep doing it on your phone. Use **Export CSV** to move a copy anywhere.

**Clearing Safari history clears the app's data** on iOS. Export the CSV occasionally — that file is the backup, and it is the thing you take to appointments anyway.

**Private/incognito windows forget everything.** Not a place to keep ratings.

---

## If you would rather not use GitHub

**Cloudflare Pages** or **Netlify Drop**: run `python3 build.py`, then drag the `pwa/` folder into their web uploader. Free HTTPS, done in about two minutes, no git. Same install steps afterwards. The only thing you lose is the automatic rebuild on push — you would re-drag the folder after each change.
