#!/usr/bin/env python3
"""Render printables/manual.html to a print-ready A4 PDF.

Usage:  python3 printables/make_manual.py
Needs:  pip install playwright   (Chromium already present in this environment)
"""
import pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "manual.html"
OUT = HERE / "Steady-Voice-manual.pdf"
CHROMIUM = "/opt/pw-browsers/chromium"   # drop this arg to use a local install

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROMIUM)
    page = browser.new_page()
    page.goto(SRC.as_uri())
    page.wait_for_timeout(1200)
    page.emulate_media(media="print")
    page.pdf(path=str(OUT), format="A4", print_background=True,
             margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
    browser.close()
print(f"wrote {OUT}")
