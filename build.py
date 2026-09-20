#!/usr/bin/env python3
"""Build the two shipping forms of Steady Voice from one source.

    app/steadyvoice.body.html   the single source of truth (edit this)
      -> app/steadyvoice.html   standalone single file, opens from disk
      -> pwa/index.html         installable web app, needs HTTPS hosting

The only difference between the two outputs is the manifest and icon links in
the head. The service worker registration lives in the source and is guarded by
a secure-origin check, so it simply no-ops in the standalone file.
"""
import hashlib
import pathlib

ROOT = pathlib.Path(__file__).parent
BODY = ROOT / "app" / "steadyvoice.body.html"

HEAD_COMMON = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0E7C7B">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Steady Voice">
<meta name="description" content="Syllable-timed speech practice and daily severity tracking for a school-age child who stutters frequently. Companion to speech therapy, not a substitute.">
<style>html{color-scheme:light dark} img{max-width:100%} [hidden]{display:none!important}</style>"""

# Only the hosted build gets these — a manifest link in a file:// page just 404s.
HEAD_PWA = """<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="icon" href="icon-192.png" type="image/png">"""


def wrap(head_extra=""):
    body = BODY.read_text()
    i = body.index('<div id="app">')
    head, rest = body[:i], body[i:]
    extra = ("\n" + head_extra) if head_extra else ""
    return (
        f'<!doctype html>\n<html lang="en">\n<head>\n'
        f'{HEAD_COMMON}{extra}\n{head}</head>\n<body>\n{rest}\n</body>\n</html>\n'
    )


def main():
    standalone = ROOT / "app" / "steadyvoice.html"
    standalone.write_text(wrap())
    print(f"built {standalone.relative_to(ROOT)} ({standalone.stat().st_size:,} bytes)")

    pwa_index = ROOT / "pwa" / "index.html"
    pwa_index.parent.mkdir(exist_ok=True)
    html = wrap(HEAD_PWA)
    pwa_index.write_text(html)
    print(f"built {pwa_index.relative_to(ROOT)} ({pwa_index.stat().st_size:,} bytes)")

    # Stamp the service worker cache with a hash of what it will serve. Without
    # this, a redeploy leaves every installed phone serving the old cached app
    # indefinitely — the classic PWA failure, and invisible until someone asks
    # why their fix never arrived.
    template = (ROOT / "pwa" / "sw.template.js").read_text()
    digest = hashlib.sha256(html.encode() + template.encode()).hexdigest()[:12]
    sw = ROOT / "pwa" / "sw.js"
    sw.write_text(template.replace("__BUILD__", digest))
    print(f"built {sw.relative_to(ROOT)} (cache steady-voice-{digest})")


if __name__ == "__main__":
    main()
