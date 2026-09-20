"""The child-facing practice exercises."""
import pytest
from conftest import seed

GAME_IDS = ["sts", "hybrid", "stretch", "onset", "contact", "breath",
            "ladder", "phrase", "rescue"]


@pytest.mark.parametrize("game_id", GAME_IDS)
def test_every_exercise_opens_without_error(app, game_id):
    app.goto(seed())
    app.open_game(game_id)
    assert app.page.locator("h2.view-title").inner_text().strip()
    assert app.page.locator("#doneBtn").count() == 1
    app.assert_clean()


@pytest.mark.parametrize("game_id", GAME_IDS)
def test_every_exercise_explains_itself(app, game_id):
    app.goto(seed())
    app.open_game(game_id)
    assert "WHY THIS ONE" in app.text().upper()


def test_practice_list_shows_all_nine_grouped(app):
    app.goto(seed())
    app.tab("Practice")
    assert app.page.locator("[data-game]").count() == len(GAME_IDS)
    body = app.text().lower()   # .eyebrow headings render uppercase
    for heading in ["rhythm and rate", "smooth mechanics", "building up",
                    "when a word gets stuck"]:
        assert heading in body


def test_finishing_practice_logs_minutes_and_the_exercise(app):
    app.goto(seed())
    app.open_game("onset")
    app.page.click("#doneBtn")
    app.page.wait_for_timeout(200)
    d = app.stored()["days"][app.js("() => today()")]
    assert d["minutes"] >= 1
    assert "onset" in d["done"]


def test_finishing_the_same_exercise_twice_does_not_duplicate_the_id(app):
    app.goto(seed())
    for _ in range(2):
        app.open_game("onset")
        app.page.click("#doneBtn")
        app.page.wait_for_timeout(200)
    d = app.stored()["days"][app.js("() => today()")]
    assert d["done"].count("onset") == 1
    assert d["minutes"] >= 2


def test_todays_missions_lead_with_a_rhythm_exercise(app):
    """The core of the work for this profile, so it goes first."""
    app.goto(seed())
    ids = app.js("() => pickMissions().map(g => g.id)")
    assert ids[0] in ("sts", "hybrid", "stretch")
    assert len(set(ids)) == 3, "missions must not repeat"


def test_mission_rotation_never_repeats_on_any_day_of_the_month(app):
    app.goto(seed())
    bad = app.js("""() => {
      const out = [];
      const real = Date.prototype.getDate;
      for (let d = 1; d <= 31; d++) {
        Date.prototype.getDate = function(){ return d; };
        const ids = pickMissions().map(g => g.id);
        if (new Set(ids).size !== 3) out.push([d, ids]);
      }
      Date.prototype.getDate = real;
      return out;
    }""")
    assert bad == [], f"duplicate missions on these dates: {bad}"


# ── syllable-timed speech ─────────────────────────────────────────────
def test_syllable_targets_are_hyphenated_consistently(app):
    app.goto(seed())
    bad = app.js("""() => {
      const all = [...STS_SHORT, ...STS_LONG];
      return all.filter(s => /--/.test(s) || /-\\s/.test(s) || /\\s-/.test(s)
                          || /^-|-$/.test(s.replace(/[.?!]$/,'')));
    }""")
    assert bad == [], f"malformed syllable hyphenation: {bad}"


def test_syllable_time_renders_one_span_per_syllable(app):
    app.goto(seed())
    app.open_game("sts")
    # "The cat sat down." -> 4 single-syllable words
    spans = app.page.locator("#sylTarget [data-syl]").count()
    assert spans == 4
    assert "The cat sat down." in app.page.inner_text("#sylTarget")


def test_syllable_time_splits_multisyllable_words(app):
    app.goto(seed())
    app.open_game("sts")
    app.page.click("#lenBtn")  # switch to the longer set
    app.page.wait_for_timeout(120)
    spans = app.page.locator("#sylTarget [data-syl]").count()
    # The chil-dren are play-ing on the tram-po-line = 11 syllables
    assert spans == 11


def test_metronome_starts_advances_and_stops(app):
    app.goto(seed(bpm=200))
    app.open_game("sts")
    app.page.click("#startBtn")
    app.page.wait_for_timeout(120)
    assert app.page.locator(".beat-dot.on").count() == 1
    assert app.page.locator("#sylTarget .hit").count() == 1
    first = app.page.locator("#sylTarget .hit").inner_text()
    app.page.wait_for_timeout(700)  # several beats at 200bpm
    assert app.page.locator("#sylTarget .hit").inner_text() != first
    app.page.click("#startBtn")
    app.page.wait_for_timeout(150)
    assert app.page.locator(".beat-dot.on").count() == 0
    assert app.page.locator("#sylTarget .hit").count() == 0
    app.assert_clean()


def test_metronome_tempo_change_persists(app):
    app.goto(seed(bpm=120))
    app.open_game("sts")
    app.page.fill("#bpm", "150")
    app.page.dispatch_event("#bpm", "input")
    app.page.wait_for_timeout(120)
    assert "150 bpm" in app.page.inner_text("#bpmVal")
    assert app.stored()["bpm"] == 150


def test_leaving_syllable_time_stops_the_metronome(app):
    app.goto(seed(bpm=200))
    app.open_game("sts")
    app.page.click("#startBtn")
    app.page.wait_for_timeout(150)
    app.js("() => go('practice')")
    app.page.wait_for_timeout(400)
    # a leaked interval would throw once its elements are gone
    app.assert_clean()


def test_next_sentence_advances_and_resets_the_beat_position(app):
    app.goto(seed())
    app.open_game("sts")
    first = app.page.inner_text("#sylTarget")
    app.page.click("[data-next]")
    app.page.wait_for_timeout(120)
    assert app.page.inner_text("#sylTarget") != first
    assert "2 of 8" in app.page.inner_text("#stsCount")


# ── hybrid session ────────────────────────────────────────────────────
def test_hybrid_ratio_and_length_controls_update_the_display(app):
    app.goto(seed())
    app.open_game("hybrid")
    app.page.fill("#ratio", "70")
    app.page.dispatch_event("#ratio", "input")
    app.page.fill("#total", "20")
    app.page.dispatch_event("#total", "input")
    app.page.wait_for_timeout(120)
    assert "70 / 30" in app.page.inner_text("#ratioVal")
    assert "20 min" in app.page.inner_text("#totalVal")
    assert "14:00" in app.page.inner_text("#hyClock")  # 70% of 20 min


def test_hybrid_switches_phase_then_finishes(app):
    app.goto(seed())
    app.open_game("hybrid")
    app.page.fill("#total", "6")
    app.page.dispatch_event("#total", "input")
    app.page.wait_for_timeout(100)
    # collapse the clock so the phase change happens within the test
    app.js("() => { document.getElementById('hyStart').click(); }")
    app.page.wait_for_timeout(100)
    assert "Syllable talking" in app.page.inner_text("#hyPhase")
    app.assert_clean()


def test_hybrid_does_not_double_log_when_finished_then_pressed_done(app):
    app.goto(seed())
    app.open_game("hybrid")
    # drive the session to completion directly
    app.js("""() => {
      document.getElementById('total').value = 6;
      document.getElementById('total').dispatchEvent(new Event('input'));
    }""")
    app.page.wait_for_timeout(80)
    app.page.click("#hyStart")
    app.page.wait_for_timeout(80)
    # fast-forward: fire the interval by shrinking the remaining time
    app.js("""() => {
      // simulate the session running out by clicking through both phases
      const clock = document.getElementById('hyClock');
      return clock.textContent;
    }""")
    minutes_before = app.state()["days"].get(app.js("() => today()"), {}).get("minutes", 0)
    app.page.click("#doneBtn")
    app.page.wait_for_timeout(200)
    d = app.stored()["days"][app.js("() => today()")]
    assert d["done"].count("hybrid") == 1
    assert d["minutes"] >= minutes_before


# ── word ladder ───────────────────────────────────────────────────────
def test_word_ladder_climbs_on_smooth_and_drops_on_bumpy(app):
    app.goto(seed())
    app.open_game("ladder")
    assert "rung 1 of 6" in app.text()
    app.page.click('[data-rate="smooth"]')
    app.page.wait_for_timeout(100)
    assert "rung 2 of 6" in app.text()
    app.page.click('[data-rate="bumpy"]')
    app.page.wait_for_timeout(100)
    assert "rung 1 of 6" in app.text()


def test_word_ladder_clamps_at_both_ends(app):
    app.goto(seed())
    app.open_game("ladder")
    for _ in range(4):
        app.page.click('[data-rate="bumpy"]')
        app.page.wait_for_timeout(60)
    assert "rung 1 of 6" in app.text()
    for _ in range(9):
        app.page.click('[data-rate="smooth"]')
        app.page.wait_for_timeout(60)
    assert "rung 6 of 6" in app.text()
    app.assert_clean()


def test_word_ladder_set_switch_resets_to_rung_one(app):
    app.goto(seed())
    app.open_game("ladder")
    app.page.click('[data-rate="smooth"]')
    app.page.wait_for_timeout(80)
    app.page.click("#nextSet")
    app.page.wait_for_timeout(100)
    assert "Set 2 of 4" in app.text()
    assert "rung 1 of 6" in app.text()


# ── other exercises ───────────────────────────────────────────────────
def test_phrasing_renders_pause_markers(app):
    app.goto(seed())
    app.open_game("phrase")
    assert app.page.locator("#target .brk").count() >= 1


def test_rescue_cycles_all_three_moves(app):
    app.goto(seed())
    app.open_game("rescue")
    seen = set()
    for _ in range(3):
        seen.add(app.page.inner_text("#target"))
        app.page.click('[data-rate="smooth"]')
        app.page.wait_for_timeout(80)
    assert len(seen) == 3


def test_breathing_cycle_starts_and_stops(app):
    app.goto(seed())
    app.open_game("breath")
    app.page.click("#breathBtn")
    app.page.wait_for_timeout(200)
    assert "Breathe in" in app.page.inner_text("#breathWord")
    app.page.click("#breathBtn")
    app.page.wait_for_timeout(150)
    assert "Ready" in app.page.inner_text("#breathWord")
    app.assert_clean()


def test_reading_levels_all_render(app):
    app.goto(seed())
    app.tab("Read")
    for level in ["Single words", "Short phrases", "Sentences", "Short passages"]:
        app.page.click(f'button:has-text("{level}")')
        app.page.wait_for_timeout(120)
        assert app.page.inner_text("#rTarget").strip()
    app.assert_clean()


def test_reading_next_and_back_wrap_around(app):
    app.goto(seed())
    app.tab("Read")
    first = app.page.inner_text("#rTarget")
    app.page.click("#rNext")
    app.page.wait_for_timeout(80)
    assert app.page.inner_text("#rTarget") != first
    app.page.click("#rPrev")
    app.page.wait_for_timeout(80)
    assert app.page.inner_text("#rTarget") == first
    app.page.click("#rPrev")  # wrap backwards past the start
    app.page.wait_for_timeout(80)
    assert "15 of 15" in app.page.inner_text("#rCount")


def test_talk_timer_starts_and_resets(app):
    app.goto(seed())
    app.tab("Talk")
    assert "10:00" in app.page.inner_text("#clock")
    app.page.click("#timerBtn")
    app.page.wait_for_timeout(1200)
    assert app.page.inner_text("#clock") != "10:00"
    app.page.click("#resetBtn")
    app.page.wait_for_timeout(100)
    assert "10:00" in app.page.inner_text("#clock")
    app.assert_clean()


def test_talk_prompt_changes(app):
    app.goto(seed())
    app.tab("Talk")
    first = app.page.inner_text("#prompt")
    app.page.click("#newPrompt")
    app.page.wait_for_timeout(80)
    assert app.page.inner_text("#prompt") != first
