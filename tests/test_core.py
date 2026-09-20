"""Core logic: storage, dates, streaks, day records, mode routing."""
from conftest import seed, make_days


# ── boot ──────────────────────────────────────────────────────────────
def test_boots_clean_with_no_stored_data(app):
    app.goto()
    assert "Steady Voice" in app.page.title()
    assert app.page.locator("#tabs button").count() == 5
    app.assert_clean()


def test_boots_with_corrupt_storage(app):
    app.page.goto(app.page.url if app.page.url.startswith("file") else "about:blank")
    app.goto()
    app.page.evaluate("() => localStorage.setItem('steadyvoice.v1', '{not json')")
    app.page.reload()
    app.page.wait_for_timeout(200)
    assert app.page.locator("#tabs button").count() == 5
    app.assert_clean()


def test_survives_storage_being_unavailable(app):
    """Private windows and blocked site data make localStorage throw."""
    app.goto()
    app.page.evaluate("""() => {
      const boom = () => { throw new Error('SecurityError'); };
      Object.defineProperty(window, 'localStorage', {
        configurable: true,
        get(){ return { getItem: boom, setItem: boom, removeItem: boom }; }
      });
    }""")
    app.page.reload()
    app.page.wait_for_timeout(250)
    assert app.page.locator("#tabs button").count() == 5
    app.assert_clean()


# ── date helpers ──────────────────────────────────────────────────────
def test_add_days_crosses_month_and_year_boundaries(app):
    app.goto()
    assert app.js("() => addDays('2026-01-31', 1)") == "2026-02-01"
    assert app.js("() => addDays('2026-03-01', -1)") == "2026-02-28"
    assert app.js("() => addDays('2026-12-31', 1)") == "2027-01-01"
    assert app.js("() => addDays('2027-01-01', -1)") == "2026-12-31"
    assert app.js("() => addDays('2028-02-28', 1)") == "2028-02-29"  # leap year


def test_add_days_is_stable_across_dst_style_shifts(app):
    """Anchoring at noon keeps a +/-1 hour shift from moving the date."""
    app.goto()
    assert app.js("() => addDays(addDays('2026-04-05', 1), -1)") == "2026-04-05"
    assert app.js("() => addDays(addDays('2026-10-04', 1), -1)") == "2026-10-04"


def test_today_matches_local_calendar_date(app):
    app.goto()
    same = app.js("""() => {
      const d = new Date();
      const local = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
      return today() === local;
    }""")
    assert same, "today() drifts from the local calendar date near midnight (UTC slice bug)"


# ── day records ───────────────────────────────────────────────────────
def test_day_creates_a_complete_default_record(app):
    app.goto(seed())
    rec = app.js("() => day('2026-09-01')")
    assert rec["sr"] is None
    assert rec["minutes"] == 0
    assert rec["done"] == []
    assert rec["transfer"] == 0
    assert rec["sit"] == {}


def test_day_backfills_sit_on_records_written_by_an_older_version(app):
    old = seed(days={"2026-09-01": {"sr": 4, "minutes": 10, "done": [], "notes": ""}})
    app.goto(old)
    rec = app.js("() => day('2026-09-01')")
    assert rec["sit"] == {}
    app.assert_clean()


def test_setday_persists_to_storage(app):
    app.goto(seed())
    app.js("() => setDay('2026-09-01', {sr: 6})")
    assert app.stored()["days"]["2026-09-01"]["sr"] == 6


# ── streak ────────────────────────────────────────────────────────────
def test_streak_is_zero_with_no_history(app):
    app.goto(seed())
    assert app.js("() => streak()") == 0


def test_streak_counts_consecutive_practice_days(app):
    app.goto(seed())
    app.js("""() => {
      let d = today();
      for (let i = 0; i < 5; i++) { day(d).minutes = 10; d = addDays(d, -1); }
      save();
    }""")
    assert app.js("() => streak()") == 5


def test_streak_stops_at_a_gap(app):
    app.goto(seed())
    app.js("""() => {
      day(today()).minutes = 10;
      day(addDays(today(), -1)).minutes = 10;
      // -2 skipped
      day(addDays(today(), -3)).minutes = 10;
      save();
    }""")
    assert app.js("() => streak()") == 2


def test_streak_survives_a_day_not_yet_practised(app):
    """Opening the app in the morning must not read as a broken streak."""
    app.goto(seed())
    app.js("""() => {
      let d = addDays(today(), -1);
      for (let i = 0; i < 4; i++) { day(d).minutes = 10; d = addDays(d, -1); }
      save();
    }""")
    assert app.js("() => streak()") == 4, (
        "streak resets to 0 before the child has practised today, which "
        "punishes them for opening the app in the morning")


def test_streak_does_not_count_a_rating_only_day(app):
    """A parent rating is not practice."""
    app.goto(seed())
    app.js("() => { day(today()).sr = 5; save(); }")
    assert app.js("() => streak()") == 0


# ── last(n) ───────────────────────────────────────────────────────────
def test_last_returns_n_rows_oldest_first_ending_today(app):
    app.goto(seed())
    rows = app.js("() => last(28)")
    assert len(rows) == 28
    assert rows[-1]["date"] == app.js("() => today()")
    dates = [r["date"] for r in rows]
    assert dates == sorted(dates)


def test_last_fills_missing_days_with_blanks(app):
    app.goto(seed(days=make_days({"2026-09-01": (5, 10, 1)})))
    rows = app.js("() => last(7)")
    assert all("sr" in r for r in rows)
    assert all(r.get("minutes") is not None for r in rows)


# ── mode + routing ────────────────────────────────────────────────────
def test_mode_switch_swaps_the_tab_bar_and_persists(app):
    app.goto(seed())
    assert "Practice" in app.page.inner_text("#tabs")
    app.switch_mode()
    assert "Progress" in app.page.inner_text("#tabs")
    assert app.stored()["mode"] == "parent"
    app.switch_mode()
    assert "Practice" in app.page.inner_text("#tabs")
    app.assert_clean()


def test_parent_route_is_rejected_in_kid_mode(app):
    app.goto(seed())
    app.js("() => go('progress')")
    app.page.wait_for_timeout(120)
    assert app.page.locator("#view .greet").count() == 1   # bounced to Today
    assert "Progress" not in app.text()


def test_kid_route_is_rejected_in_parent_mode(app):
    app.goto(seed(mode="parent"))
    app.js("() => go('practice')")
    app.page.wait_for_timeout(120)
    assert "Daily rating" in app.page.inner_text("h2.view-title")


def test_every_kid_tab_renders(app):
    app.goto(seed())
    for label in ["Today", "Practice", "Read", "Out Loud", "Talk"]:
        app.tab(label)
        assert app.page.locator("#view").inner_text().strip()
    app.assert_clean()


def test_every_parent_tab_renders(app):
    app.goto(seed(mode="parent"))
    for label in ["Today", "Progress", "Guides", "Find help"]:
        app.tab(label)
        assert app.page.locator("#view").inner_text().strip()
    app.assert_clean()


def test_theme_toggle_cycles_and_persists(app):
    app.goto(seed())
    app.page.click("#themeBtn")
    assert app.page.get_attribute("html", "data-theme") == "dark"
    assert app.stored()["theme"] == "dark"
    app.page.click("#themeBtn")
    assert app.page.get_attribute("html", "data-theme") == "light"
    app.page.click("#themeBtn")
    assert app.page.get_attribute("html", "data-theme") is None
    assert app.stored()["theme"] is None
    app.assert_clean()
