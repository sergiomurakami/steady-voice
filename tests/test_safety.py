"""Escaping, privacy claims, and the clinical content the app must not get wrong."""
from conftest import seed

XSS = '<img src=x onerror="window.__pwned=1">'


def test_child_name_is_escaped_everywhere(app):
    app.goto(seed(profile={"name": XSS, "startedOn": "2026-09-01"}))
    assert app.js("() => window.__pwned") is None
    assert app.page.locator("img[onerror]").count() == 0
    app.switch_mode()
    app.tab("Find help")
    assert app.js("() => window.__pwned") is None
    assert app.page.input_value("#kidName") == XSS


def test_notes_are_escaped_in_the_textarea_and_the_table(app):
    app.goto(seed(mode="parent"))
    app.page.fill("#dayNotes", XSS)
    app.page.click('[data-sr="5"]')
    app.page.wait_for_timeout(200)
    app.tab("Progress")
    assert app.js("() => window.__pwned") is None
    assert app.page.locator("#view img[onerror]").count() == 0


def test_out_loud_entries_are_escaped(app):
    app.goto(seed())
    app.tab("Out Loud")
    app.page.fill("#outWhat", XSS)
    app.page.click("#addOut")
    app.page.wait_for_timeout(250)
    assert app.js("() => window.__pwned") is None
    assert app.page.locator("#view img[onerror]").count() == 0
    assert XSS in app.text()


def test_out_loud_logging_increments_the_transfer_counter(app):
    app.goto(seed())
    app.tab("Out Loud")
    app.page.fill("#outWhat", "Ordered my own lunch in stretchy speech")
    app.page.click("#addOut")
    app.page.wait_for_timeout(250)
    iso = app.js("() => today()")
    assert app.stored()["days"][iso]["transfer"] == 1
    assert app.stored()["outLoud"][0]["text"].startswith("Ordered my own")


def test_out_loud_rejects_an_empty_entry(app):
    app.goto(seed())
    app.tab("Out Loud")
    app.page.click("#addOut")
    app.page.wait_for_timeout(200)
    assert app.stored()["outLoud"] == []
    assert "Write what you did" in app.page.inner_text("#toast")


def test_out_loud_jobs_are_graded_by_situation_not_by_nerve(app):
    """This child is not shy — the levels must not be a courage ladder."""
    app.goto(seed())
    levels = app.js("() => [...new Set(OUT_LOUD.map(m => m.level))]")
    joined = " ".join(levels).lower()
    for banned in ["brave", "courage", "scary", "nerve", "dare"]:
        assert banned not in joined, f"'{banned}' framing survived in: {levels}"
    assert any("quiet" in l.lower() or "one to one" in l.lower() for l in levels)


def test_no_desensitisation_exercise_remains(app):
    """Voluntary stuttering targets a fear this child does not have."""
    app.goto(seed())
    ids = app.js("() => GAMES.map(g => g.id)")
    assert "bumps" not in ids
    app.tab("Practice")
    body = app.text().lower()
    assert "voluntary stuttering" not in body
    assert "on purpose" not in body


def test_the_app_says_it_is_not_a_substitute_for_a_clinician(app):
    app.goto(seed())
    assert "does not replace a speech pathologist" in app.text()
    app.switch_mode()
    app.tab("Guides")
    assert "clinician" in app.all_text().lower()


def test_privacy_claim_is_true_no_network_calls_are_made(app):
    """The app tells parents nothing is uploaded. Hold it to that."""
    requests = []
    app.page.on("request", lambda r: requests.append(r.url))
    app.goto(seed())
    for label in ["Practice", "Read", "Out Loud", "Talk", "Today"]:
        app.tab(label)
    app.switch_mode()
    for label in ["Progress", "Guides", "Find help", "Today"]:
        app.tab(label)
    offenders = [u for u in requests
                 if not u.startswith("file://")
                 and "fonts.googleapis.com" not in u
                 and "fonts.gstatic.com" not in u]
    assert offenders == [], f"unexpected network traffic: {offenders}"


def test_guides_lead_with_the_motor_not_anxiety_framing(app):
    app.goto(seed(mode="parent"))
    app.tab("Guides")
    body = app.all_text().lower()
    assert "motor" in body
    assert "not distressed" in body or "not being distressed" in body


def test_oakville_practice_dose_is_stated_correctly(app):
    """4-6 sessions a day of 5-10 minutes, per the treatment guide."""
    app.goto(seed())
    app.tab("Practice")
    body = app.text().lower()
    assert "four to six" in body
    assert "five to ten" in body


def test_prompting_rules_are_present_where_a_parent_will_see_them(app):
    app.goto(seed())
    app.tab("Out Loud")
    body = app.text().lower()
    assert "once an hour" in body or "one prompt" in body
    assert "never as a response" in body


def test_syllable_time_warns_against_staccato(app):
    app.goto(seed())
    app.open_game("sts")
    body = app.text().lower()
    assert "legato" in body or "joined smoothly" in body
    assert "staccato" in body or "chopped" in body


def test_severity_anchors_cover_the_whole_scale(app):
    app.goto(seed(mode="parent", srMax=10))
    missing = app.js("""() => {
      const out = [];
      for (let n = 0; n <= S.srMax; n++) { if (!anchorFor(n)) out.push(n); }
      return out;
    }""")
    assert missing == [], f"no severity anchor text for {missing}"


def test_severity_anchors_cover_the_lidcombe_scale_too(app):
    app.goto(seed(mode="parent", srMax=9))
    missing = app.js("""() => {
      const out = [];
      for (let n = 0; n <= S.srMax; n++) { if (!anchorFor(n)) out.push(n); }
      return out;
    }""")
    assert missing == [], f"no severity anchor text for {missing}"


def test_tabs_expose_the_current_page_to_assistive_tech(app):
    app.goto(seed())
    current = app.page.locator('#tabs button[aria-current="page"]')
    assert current.count() == 1
    app.tab("Practice")
    assert "Practice" in app.page.locator(
        '#tabs button[aria-current="page"]').inner_text()


def test_contact_details_in_the_directory_are_intact(app):
    app.goto(seed(mode="parent"))
    app.tab("Find help")
    body = app.text()
    assert "asrc@uts.edu.au" in body
    assert "+61 2 9514 5314" in body
    assert "07 5687 9183" in body
    assert "Oakville" in body


def test_medicare_item_numbers_are_present_and_paired(app):
    app.goto(seed(mode="parent"))
    app.tab("Guides")
    body = app.all_text()   # the funding section lives in a collapsed <details>
    for item in ["82005", "93033", "93041", "82020", "93036", "93044"]:
        assert item in body, f"missing MBS item {item}"
    assert "8" in body and "20 treatment" in body
