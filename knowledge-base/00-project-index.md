# Stuttering — research base and app

Built September 2026. Focus: **school-age children**, Australian context, evidence-led.

Tuned to a specific profile — a child who stutters frequently in **every** context, including one-on-one with a parent, and who is socially confident, unafraid to speak, and not ashamed of stuttering. That profile is unusual in the literature and it changes what the right treatment is. See **§8** first.

---

## What's here

```
Stuttering/
├── README.md                       ← you are here
├── knowledge-base/
│   ├── 01-the-evidence.md          What the research actually says. Prevalence,
│   │                               natural recovery, why school age is different,
│   │                               psychosocial impact, what is NOT supported.
│   ├── 02-treatment-programs.md    Every named program compared. The Oakville
│   │                               section is the long one — structure, stages,
│   │                               contingencies, transfer rules, evidence.
│   ├── 03-measuring-progress.md    Severity rating scales, %SS, OASES, Palin PRS,
│   │                               CALMS. What to track and how to read it.
│   ├── 04-school-and-social.md     Classroom accommodations, bullying data,
│   │                               what parents should and shouldn't do.
│   ├── 05-finding-a-therapist.md   Directory: Australia + global telehealth.
│   │                               Five questions to vet any clinician.
│   │                               Medicare/NDIS funding as at Sept 2026.
│   ├── 06-app-landscape.md         Stutter Stars, Stamurai, Penguin and seven
│   │                               others. The seven gaps none of them fill.
│   ├── 07-app-spec.md              Steady Voice build notes + React Native
│   │                               porting spec.
│   └── 08-this-childs-profile.md   ★ The profile, what it rules out, what it
│                                     points to, and what to say at the first
│                                     appointment.
├── printables/
│   ├── Steady-Voice-manual.pdf     ★ 15-page manual for the app, in plain
│   │                                 language. Front half for the child,
│   │                                 back half for the grown-up. Print it.
│   ├── Steady-Voice-manual-ptBR.pdf  The same manual in Brazilian Portuguese,
│   │                                 with an English/Portuguese glossary of
│   │                                 the app's buttons (the app itself is
│   │                                 in English).
│   ├── manual.html                 Sources for the manuals — edit and
│   ├── manual-ptbr.html              re-render with make_manual.py /
│   │                                 make_manual_ptbr.py
│   └── teacher-handout.md          One page. Give this to the teacher.
├── app/
│   ├── steadyvoice.body.html       ★ The source of truth. Edit this one.
│   └── steadyvoice.html            Built: standalone single file, opens from disk
├── pwa/                            Built: the installable app, deploy this folder
│   ├── index.html  manifest.webmanifest  sw.js  icons
│   └── sw.template.js              Edit this, not sw.js
├── build.py                        Builds both outputs from the one source
├── DEPLOY.md                       ★ Getting it onto the phones, offline
└── .github/workflows/deploy.yml    Auto-deploys pwa/ to GitHub Pages
```

Run `python3 build.py` after editing the source. The service worker cache name is stamped with a hash of the build, so a redeploy always invalidates the old cache on every installed device.

Every claim has a source link at the foot of its file. Nothing is asserted without one.

---

## The five things that matter most

**1. The problem here is motor, not social.** A child who bumps as much alone with a parent as in front of a class is telling you the driver is speech production, not situational anxiety. Say that at the first appointment, and be sceptical of any clinician who proposes an anxiety-focused approach for this child. → §8

**2. Ask for the Oakville Program by name.** The Australian school-age syllable-timed speech program, from the group that developed Lidcombe and Camperdown. Pure motor training, no emotional component, parent-delivered under clinician supervision. Its school-age trial in 6–11 year olds reported a **77% group mean severity reduction at 12 months**. It is the best-matched treatment available for this profile — and it is Phase II evidence, not a randomised controlled trial, so hold it accordingly. → §2, §8

**3. School age is not preschool.** The two-thirds natural recovery figure applies to preschoolers. A 2021 systematic review found *no high-level evidence* for interventions with school-aged children — not that nothing works, but that treatment is harder and slower and anyone promising a cure is overselling. → §1

**4. Medicare changed on 1 March 2026, in your favour.** A dedicated stuttering pathway: 8 assessment and 20 treatment sessions, lifetime cap before age 25, $87.25 rebate, GP referral, **no care plan needed**. Item numbers in §5 — quote them, because it's new enough that not every GP knows. → §5

**5. Apps are scaffolding, not treatment.** There is essentially no high-quality efficacy evidence for stuttering apps in children. Their honest job is practice scaffolding, adherence support and measurement. Steady Voice is built to that limit and says so on its home screen. → §6

---

## Do these five things

1. **Ring Queensland Health Child Development Service** — 07 5687 9183 (option 2). Free, waitlisted, one phone call.
2. **Book a GP appointment** and ask for a referral under the new stuttering MBS items (82005 / 93033 / 93041 assessment, 82020 / 93036 / 93044 treatment).
3. **Book a telehealth assessment with the Australian Stuttering Treatment Centre** — asrc@uts.edu.au, +61 2 9514 5314 — and **ask about the Oakville Program specifically.**
4. **Ask for an OASES-S or CALMS baseline** while he's still completely comfortable about it. Costs one assessment, and means you'd notice if that ever changed.
5. **Print the teacher handout** and give it to the classroom teacher.
6. **Print the manual** (`printables/Steady-Voice-manual.pdf`, or the `-ptBR` version) and read the front half with him.

**One more thing, if he stutters in Portuguese too.** The Oakville treatment guide is explicit: if a child stutters more in another language than the language of treatment, treatment should also be done in that other language. Raise it at the first appointment, and practise in Portuguese at home regardless — the syllable beat works identically in both.

Then spend the rebated treatment sessions on whoever the plan says should deliver them.

---

## Using the app

**On a phone or tablet, read `DEPLOY.md`** — it covers hosting it on GitHub Pages and installing it on Android and iOS so it works offline. A copied HTML file will not work properly on iOS: service workers do not run from `file://`, and `localStorage` there is unreliable, which risks losing the daily ratings.

On a computer, `app/steadyvoice.html` opens straight from disk.

- Person icon, top right — switches between the child's view and the grown-up view.
- Sun icon — light/dark.
- **Start with Syllable Time.** It's the exercise the app is built around. Turn the click on, start slow, and do it together — the parent speaks in syllable talking too.
- All data stays in that browser on that device. No account, no upload, no speech recognition. Export the CSV to keep a copy or take it to an appointment.

Start the daily severity rating from day one, even before therapy begins — four weeks of baseline is worth a great deal at a first appointment. Rate the situations too, for the first few weeks at least: that chart answers whether context matters at all, which is the open question in this case.
