# STATUS.md - Shift Brain Sheet Maker

Status: **complete and verified** (2026-10-22).

## What was built

A healthcare-worker **education aid** (never medical advice): a small Python
build script that generates **printable, blank shift "brain sheet" HTML forms**
from simple JSON templates. Every sheet prints with a reminder to check the
facility's policy, and the tool stores no patient data - all output fields are
blank write-in boxes.

Each generated sheet contains the three requested sections:

1. **Shift report handoff grid** - one column per patient with rows for room,
   initials, dx, code status, allergies, diet, IV/access, drips, O2, activity,
   labs, meds due, safety-flag checkboxes, pending items, and end-of-shift
   to-dos.
2. **Task/time-box columns** - one blank box per patient per time slot so a
   nurse can jot what is due and when.
3. **Free-note areas** - ruled, printable note blocks (to-dos, teaching, SBAR
   follow-ups, feeding logs, unit orientation, etc.).

Three sample templates are included:

- **med-surg** - 4-patient handoff grid, 0700-1700 task columns, SBAR notes
- **mom-baby** - 3 couplets (parent + newborn), feeding-log time slots, discharge checklist
- **float** - 4 patients, isolation flags, "where things live" orientation notes, catch-up plan

Files:

- `build.py` - build script (template loader, strict validator, HTML renderer, CLI)
- `templates/*.json` - the three sample templates
- `output/*.html` - generated blank sheets (committed for convenience)
- `tests/test_build.py` - 20-test suite (stdlib `unittest`; no dependencies)
- `README.md`, `LICENSE` (MIT, exact line: "Copyright (c) 2026 Asdale Dynamics, LLC"), `.gitignore`

## How to run it

Python 3.10+ only, standard library only:

```bash
python build.py                    # build all templates into ./output
python build.py --list             # list templates
python build.py --template float   # build one template
python build.py --out my_sheets    # custom output folder
python -m unittest discover -s tests -v   # run tests
```

Open the HTML in a browser and print (letter landscape; the `@page` print CSS
is built in).

## Verification results

- `python3 -m py_compile build.py tests/test_build.py` - clean.
- `python3 -m unittest discover -s tests -v` - **20 tests, all OK**
  (covers validation errors such as unknown keys/ranges/duplicates, balanced
  rendered HTML, exact grid/slot/note counts per template, policy wording on
  every sheet, build outputs on disk, exact LICENSE copyright line, README credit).
- `python3 build.py` - built all 3 sheets to `output/` (med 10.7 KB, mom-baby 9.5 KB, float 11.7 KB).
- `python3 build.py --list` - correct summary lines for all 3 templates.
- Invalid template (patients=99) - friendly CLI error, exit code 1.
- Rendered HTML verified balanced via `html.parser` and checked for no
  template-artifact braces; each sheet prints the facility-policy notice and
  "no patient data is stored" statement.
- Repo quality: no secrets, no personal data, no network calls, no
  dependencies.

## Known gaps / future ideas

- Sample template content (mom-baby, float especially) is approximate -
  review with nurses from those specialties before wide distribution.
- Sheets are designed for US letter landscape; no A4/duplex variants yet.
- No direct PDF export (browsers' Print-to-PDF works well in the meantime).
- No page-number/repeat-header logic for multi-printer setups; long handoff
  grids flow to a second page.
- No dark-mode or hole-punch margins variants; no unit-test coverage of visual
  print layout beyond structure.
- Could add: a `--preview` server or screenshot test, more templates
  (tele, PACU, psych), and packaging as a zip app for non-coders.
