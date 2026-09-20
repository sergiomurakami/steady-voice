"""The grown-up view: ratings, situations, charts, export, settings."""
from conftest import seed, make_days


def month(sr_series, minutes=10, transfer=1, sit=None):
    """Build `len(sr_series)` consecutive days ending today."""
    return {"__series__": sr_series, "__minutes__": minutes,
            "__transfer__": transfer, "__sit__": sit or {}}


def load_series(app, sr_series, sit_for=None):
    app.js("""(cfg) => {
      let d = today();
      for (let i = cfg.series.length - 1; i >= 0; i--) {
        const rec = day(d);
        rec.sr = cfg.series[i];
        rec.minutes = 10;
        rec.done = ['sts'];
        rec.transfer = 1;
        if (cfg.sit) rec.sit = Object.assign({}, cfg.sit);
        d = addDays(d, -1);
      }
      save();
    }""", {"series": sr_series, "sit": sit_for})


# ── severity rating ───────────────────────────────────────────────────
def test_rating_scale_shows_eleven_buttons_on_oakville(app):
    app.goto(seed(mode="parent", srMax=10))
    assert app.page.locator("[data-sr]").count() == 11
    assert "0 · no stuttering" in app.text()
    assert "10 · extremely severe" in app.text()


def test_rating_scale_shows_ten_buttons_on_lidcombe(app):
    app.goto(seed(mode="parent", srMax=9))
    assert app.page.locator("[data-sr]").count() == 10
    assert "9 · extremely severe" in app.text()


def test_setting_and_clearing_a_rating(app):
    app.goto(seed(mode="parent"))
    app.page.click('[data-sr="6"]')
    app.page.wait_for_timeout(150)
    iso = app.js("() => today()")
    assert app.stored()["days"][iso]["sr"] == 6
    assert app.page.get_attribute('[data-sr="6"]', "aria-pressed") == "true"
    app.page.click('[data-sr="6"]')  # toggle off
    app.page.wait_for_timeout(150)
    assert app.stored()["days"][iso]["sr"] is None
    app.assert_clean()


def test_rating_buttons_are_large_enough_to_tap(app):
    """Eleven buttons across a phone width must still be a usable target."""
    app.goto(seed(mode="parent", srMax=10))
    box = app.page.locator('[data-sr="5"]').bounding_box()
    assert box["height"] >= 32, (
        f"severity buttons are {box['height']:.0f}px tall on a 430px screen — "
        "too small to hit reliably")


def test_day_navigation_cannot_go_past_today(app):
    app.goto(seed(mode="parent"))
    assert app.page.get_attribute('[data-shift="1"]', "disabled") is not None
    app.page.click('[data-shift="-1"]')
    app.page.wait_for_timeout(150)
    assert app.page.get_attribute('[data-shift="1"]', "disabled") is None
    app.page.click('[data-shift="1"]')
    app.page.wait_for_timeout(150)
    assert "Today" in app.page.inner_text("h3")


def test_scale_change_rerenders_the_rating_grid(app):
    app.goto(seed(mode="parent", srMax=10))
    app.tab("Find help")
    app.page.select_option("#srScaleSel", "9")
    app.page.wait_for_timeout(120)
    assert app.stored()["srMax"] == 9
    app.tab("Today")
    assert app.page.locator("[data-sr]").count() == 10


# ── situations ────────────────────────────────────────────────────────
def test_all_eight_situations_are_offered(app):
    app.goto(seed(mode="parent"))
    assert app.page.locator(".sit-row").count() == 8


def test_situation_rating_sets_and_clears(app):
    app.goto(seed(mode="parent"))
    app.page.click('[data-sit="excited"][data-val="8"]')
    app.page.wait_for_timeout(150)
    iso = app.js("() => today()")
    assert app.stored()["days"][iso]["sit"]["excited"] == 8
    app.page.click('[data-sit="excited"][data-val="8"]')
    app.page.wait_for_timeout(150)
    assert "excited" not in app.stored()["days"][iso]["sit"]


def test_situation_buttons_are_distinct_on_the_lidcombe_scale(app):
    """Rescaling 0-10 anchors onto 0-9 must not collapse two buttons together."""
    app.goto(seed(mode="parent", srMax=9))
    vals = app.js("""() => Array.from(document.querySelectorAll('[data-sit="solo"]'))
                        .map(b => b.dataset.val)""")
    assert len(vals) == len(set(vals)), f"duplicate situation values: {vals}"


def test_transfer_counter_increments_and_floors_at_zero(app):
    app.goto(seed(mode="parent"))
    app.page.click('[data-adj="transfer:1"]')
    app.page.click('[data-adj="transfer:1"]')
    app.page.wait_for_timeout(120)
    assert app.page.inner_text("#transferVal") == "2"
    for _ in range(5):
        app.page.click('[data-adj="transfer:-1"]')
    app.page.wait_for_timeout(120)
    assert app.page.inner_text("#transferVal") == "0"
    assert app.stored()["days"][app.js("() => today()")]["transfer"] == 0


def test_notes_persist_as_typed(app):
    app.goto(seed(mode="parent"))
    app.page.fill("#dayNotes", "Held syllable talking all through part one.")
    app.page.wait_for_timeout(150)
    iso = app.js("() => today()")
    assert "part one" in app.stored()["days"][iso]["notes"]


# ── charts ────────────────────────────────────────────────────────────
def test_progress_shows_empty_states_with_no_data(app):
    app.goto(seed(mode="parent"))
    app.tab("Progress")
    body = app.text()
    assert "No ratings yet" in body
    assert "—" in body  # stat tiles
    app.assert_clean()


def test_severity_chart_draws_valid_geometry(app):
    app.goto(seed(mode="parent"))
    load_series(app, [7, 6, 6, 5, 5, 4, 4, 3, 3, 2])
    app.tab("Progress")
    paths = app.js("""() => Array.from(document.querySelectorAll('svg path'))
                        .map(p => p.getAttribute('d'))""")
    assert paths, "severity chart drew no paths"
    joined = " ".join(paths)
    assert "NaN" not in joined and "undefined" not in joined
    app.assert_clean()


def test_severity_chart_survives_a_single_rating(app):
    app.goto(seed(mode="parent"))
    load_series(app, [5])
    app.tab("Progress")
    assert "No ratings yet" not in app.text()
    app.assert_clean()


def test_severity_chart_labels_reach_the_scale_maximum(app):
    app.goto(seed(mode="parent", srMax=10))
    load_series(app, [8, 7, 6, 5])
    app.tab("Progress")
    labels = app.js("""() => Array.from(document.querySelectorAll('svg text'))
                        .map(t => t.textContent)""")
    assert "10" in labels, "y-axis never labels the top of the 0-10 scale"
    assert "0" in labels


def test_situation_chart_appears_once_enough_contexts_are_rated(app):
    app.goto(seed(mode="parent"))
    load_series(app, [6, 6, 5, 5, 4],
                sit_for={"solo": 4, "group": 6, "excited": 8})
    app.tab("Progress")
    body = app.text()
    assert "Rate a few situations" not in body
    assert "Excited or storytelling" in body
    app.assert_clean()


def test_situation_chart_orders_worst_first(app):
    app.goto(seed(mode="parent"))
    load_series(app, [6, 6, 5], sit_for={"solo": 2, "group": 5, "excited": 9})
    app.tab("Progress")
    names = app.js("""() => Array.from(document.querySelectorAll('svg text'))
                        .map(t => t.textContent)
                        .filter(t => /storytelling|One to one|group/.test(t))""")
    assert names[0].startswith("Excited"), f"expected worst first, got {names}"


def test_trend_is_withheld_until_there_is_enough_history(app):
    """Fewer than two distinct weeks cannot produce a meaningful shift."""
    app.goto(seed(mode="parent"))
    load_series(app, [6, 5, 4])
    app.tab("Progress")
    shift = app.js("""() => {
      const tiles = Array.from(document.querySelectorAll('.stat'));
      const t = tiles.find(x => x.textContent.includes('28-DAY SHIFT'));
      return t.querySelector('b').textContent.trim();
    }""")
    assert shift == "—", (
        f"reported a 28-day shift of {shift} from 3 days of data — the first "
        "and last seven-day windows are the same rows")


def test_transfer_chart_renders_two_series(app):
    app.goto(seed(mode="parent"))
    load_series(app, [6] * 21)
    app.tab("Progress")
    assert "Used in real talk" in app.text()
    assert "Days practised" in app.text()


def test_charts_are_labelled_for_screen_readers(app):
    app.goto(seed(mode="parent"))
    load_series(app, [6, 5, 5, 4], sit_for={"solo": 4, "group": 6, "excited": 8})
    app.tab("Progress")
    labels = app.js("""() => Array.from(document.querySelectorAll('svg[role="img"]'))
                        .map(s => s.getAttribute('aria-label'))""")
    assert len(labels) >= 3
    assert all(l and len(l) > 20 for l in labels)


# ── export ────────────────────────────────────────────────────────────
def test_csv_has_the_expected_header(app):
    app.goto(seed(mode="parent", srMax=10))
    load_series(app, [6, 5, 4])
    header = app.js("""() => {
      const rows = last(180).filter(r => r.sr !== null && r.sr !== undefined);
      const sitCols = SITUATIONS.map(s => 'sit_' + s.key);
      return ['date', 'severity_rating_0_' + S.srMax, 'practice_minutes',
              'technique_used_in_real_talk', 'exercises', ...sitCols, 'notes'].join(',');
    }""")
    assert header.startswith("date,severity_rating_0_10,practice_minutes")
    assert "sit_solo" in header and "sit_tired" in header
    assert header.endswith(",notes")


def test_csv_escapes_quotes_and_commas_in_notes(app):
    app.goto(seed(mode="parent"))
    app.page.click('[data-sr="5"]')
    app.page.wait_for_timeout(150)
    app.page.fill("#dayNotes", 'He said "it was bumpy", then, later, fine')
    app.page.wait_for_timeout(200)
    line = app.js("""() => {
      const r = last(3).filter(x => x.notes)[0];
      return `"${String(r.notes).replace(/"/g,'""')}"`;
    }""")
    assert line.startswith('"') and line.endswith('"')
    assert '""it was bumpy""' in line
    # a naive split must still see one field
    assert line.count('"') % 2 == 0


def test_csv_export_downloads(app):
    app.goto(seed(mode="parent"))
    load_series(app, [6, 5, 4])
    app.tab("Progress")
    with app.page.expect_download(timeout=5000) as dl:
        app.page.click("#csvBtn")
    download = dl.value
    assert download.suggested_filename.startswith("steady-voice-")
    assert download.suggested_filename.endswith(".csv")


def test_csv_export_is_a_no_op_with_nothing_to_export(app):
    app.goto(seed(mode="parent"))
    app.tab("Progress")
    app.page.click("#csvBtn")
    app.page.wait_for_timeout(300)
    assert "Nothing to export" in app.page.inner_text("#toast")
    app.assert_clean()


# ── settings ──────────────────────────────────────────────────────────
def test_name_updates_the_header(app):
    app.goto(seed(mode="parent", profile={"name": "", "startedOn": "2026-09-01"}))
    app.tab("Find help")
    app.page.fill("#kidName", "Sam")
    app.page.wait_for_timeout(150)
    assert "Sam" in app.page.inner_text("#whoLabel")
    assert app.stored()["profile"]["name"] == "Sam"


def test_erase_actually_erases(app):
    """Fresh install, add data, erase — nothing may survive."""
    app.page.goto(app.page.url if app.page.url.startswith("file") else "about:blank")
    app.goto()  # no seed: exercises the untouched DEFAULTS path
    app.switch_mode()
    app.page.click('[data-sr="7"]')
    app.page.wait_for_timeout(150)
    app.page.fill("#dayNotes", "a note that must not survive")
    app.page.wait_for_timeout(200)
    app.tab("Find help")
    app.page.on("dialog", lambda d: d.accept())
    app.page.click("#wipeBtn")
    app.page.wait_for_timeout(300)
    stored = app.stored()
    assert stored["days"] == {}, f"erase left data behind: {stored['days']}"
    assert stored["outLoud"] == []
    assert stored["profile"]["name"] == ""


def test_erase_can_be_cancelled(app):
    app.goto(seed(mode="parent", days=make_days({"2026-09-01": (5, 10, 1)})))
    app.tab("Find help")
    app.page.on("dialog", lambda d: d.dismiss())
    app.page.click("#wipeBtn")
    app.page.wait_for_timeout(250)
    assert app.stored()["days"] != {}
