# Shift Brain Sheet Maker

**Healthcare-worker education aid (never medical advice).** A small, local-first
Python build script that turns JSON templates into **printable, blank shift
"brain sheet" HTML forms** - the grids and boxes nurses, techs, and students
scribble on during a shift. Each sheet includes a shift report handoff grid,
task/time-box columns, and free-note areas, plus a printed reminder to check
your facility's policy.

Made by **Asdale Dynamics, LLC** (Dylan Asdale, RN turned AI author) as part of
a beginner-friendly, plain-English tool collection. Learn more at
[dylanasdale.github.io](https://dylanasdale.github.io) and in
*The Massive AI Manual*.

> **What this is:** an education aid and a printable-paper helper.
> **What this is not:** medical advice, a charting tool, or a patient data system.
> **Privacy:** sheets are blank forms; nothing you write on them is stored.
> No patient data is collected, stored, or transmitted by this tool.

## Sample templates

| Template  | File                        | Style |
|-----------|-----------------------------|-------|
| med-surg  | `med_surg_brain_sheet.html` | 4-patient handoff grid (room, status, allergies, drips, labs, meds, safety flags), timed task columns, SBAR note area |
| mom-baby  | `mom_baby_brain_sheet.html` | One column per couplet (birthing parent + newborn), feeding-log time slots, discharge teaching notes |
| float     | `float_brain_sheet.html`    | Unit-orientation fields ("where things live"), isolation flags, a quick catch-up plan for unfamiliar units |

## Quick start

Requires Python 3.10+ (standard library only - no installs).

```bash
python build.py              # build every template into ./output
python build.py --list       # show available templates
python build.py --template float   # build one template by name
python build.py --out my_sheets    # choose a different output folder
```

Open the generated HTML in any browser and print it. The print CSS is already
set up for **US letter, landscape**. Sheets look best in Chrome or Edge; enable
"Background graphics" in the print dialog if you want the shaded header rows.

The prebuilt sheets from the latest run are committed in `output/` so you can
print without building anything.

## Make your own template

Copy a file in `templates/` and edit it - each template is a plain JSON file:

```json
{
  "name": "tele-stepdown",
  "title": "Tele Step-Down Shift Brain Sheet",
  "patients": 4,
  "handoff_fields": [
    { "label": "Room" },
    { "label": "Dx / why here", "hint": "one-liner" },
    { "label": "Safety flags", "options": ["Fall risk", "Telemetry", "Isolation"] }
  ],
  "time_slots": ["0700", "0900", "1100", "1300", "1500", "1700"],
  "note_areas": [
    { "title": "To-dos and callbacks", "lines": 6 },
    { "title": "Free notes", "lines": 10 }
  ]
}
```

Keys:

| Key | Meaning |
|-----|---------|
| `name`, `title` | required; template id and the printed sheet title |
| `subtitle` | optional; small line under the title |
| `file_name` | optional; output HTML filename stem |
| `patients` | 1-8 patient columns (default 4) |
| `column_titles` | optional; must match `patients` count (e.g. mom-baby pairs) |
| `handoff_fields` | required; rows of the handoff grid. Each row: `label` (required), `hint` (italic suggestion), `options` (checkbox list) |
| `time_slots` | required; 1-12 row labels for the task/time-box columns |
| `slot_height` | optional; row height in px (24-96, default 46) |
| `note_areas` | required; free-note boxes with ruled `lines` (1-40 each) |

Unknown keys, bad counts, and JSON typos fail with a friendly error (strict
validation is intentional - it catches typos before you print).

The build script is deliberately small and honest: it reads templates, renders
one self-contained HTML file per sheet (inline CSS, no JavaScript, no
tracking, no network), and writes them to disk.

## Project layout

```
build.py                 - the build script (loader, validator, renderer, CLI)
templates/*.json         - sample templates (med-surg, mom-baby, float)
output/*.html            - generated blank sheets (rebuilt by build.py)
tests/test_build.py      - test suite (python -m unittest)
LICENSE                  - MIT
```

## Development

```bash
python -m unittest discover -s tests -v   # run the test suite
```

Tests cover template validation (unknown keys, ranges, duplicates), rendered
HTML (balanced tags, grid/slot/note counts, policy wording printed on every
sheet), build output files, and project files (exact LICENSE copyright line,
README credit).

## Health & safety statement

- Education only, never medical advice. Every printed sheet carries a visible
  reminder to check facility policy and the current medical record.
- This tool never asks for, stores, or transmits patient data. Generated files
  contain only blank form fields.
- Sample templates are starting points, not standards of practice - adapt them
  to your unit, your state, and your facility's policies.

## License

[MIT](LICENSE) - Copyright (c) 2026 Asdale Dynamics, LLC.
