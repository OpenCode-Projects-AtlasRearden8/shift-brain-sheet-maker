#!/usr/bin/env python3
"""Shift Brain Sheet Maker.

A small Python build script that turns JSON template files into printable,
blank shift "brain sheet" HTML forms (report handoff grid, task/time-box
columns, free-note areas). Education aid only, never medical advice.
This tool does not collect, store, or transmit any patient data.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = ROOT / "templates"
OUTPUT_DIR = ROOT / "output"

POLICY_NOTE = (
    "Education only - not medical advice. Always check your facility's policy "
    "and the current medical record before acting. This is a blank form: "
    "no patient data is stored by this tool."
)
FOOTER = (
    "Shift Brain Sheet Maker - Asdale Dynamics, LLC - printable blank education "
    "form; no patient data is stored - {today} - template: {tmpl}"
)

ALLOWED_TOP_LEVEL = {
    "name",
    "file_name",
    "title",
    "subtitle",
    "patients",
    "column_titles",
    "handoff_fields",
    "time_slots",
    "slot_height",
    "note_areas",
}
ALLOWED_FIELD_KEYS = {"label", "hint", "options"}
ALLOWED_NOTE_KEYS = {"title", "lines"}


def _e(value: object) -> str:
    return escape(str(value), quote=True)


def validate_template(template: dict, source: str = "template") -> dict:
    if not isinstance(template, dict):
        raise ValueError(f"{source}: template must be a JSON object")
    for key in ("name", "title", "handoff_fields", "time_slots", "note_areas"):
        if key not in template:
            raise ValueError(f"{source}: missing required key '{key}'")
    unknown = set(template) - ALLOWED_TOP_LEVEL
    if unknown:
        raise ValueError(
            f"{source}: unknown key(s) {sorted(unknown)}; "
            f"allowed: {sorted(ALLOWED_TOP_LEVEL)}"
        )
    if not isinstance(template["name"], str) or not template["name"].strip():
        raise ValueError(f"{source}: 'name' must be a non-empty string")
    if not isinstance(template["title"], str) or not template["title"].strip():
        raise ValueError(f"{source}: 'title' must be a non-empty string")
    if "subtitle" in template and not isinstance(template["subtitle"], str):
        raise ValueError(f"{source}: 'subtitle' must be a string when present")

    patients = template.get("patients", 4)
    if not isinstance(patients, int) or not 1 <= patients <= 8:
        raise ValueError(f"{source}: 'patients' must be an integer between 1 and 8")

    column_titles = template.get("column_titles")
    if column_titles is not None:
        if (
            not isinstance(column_titles, list)
            or len(column_titles) != patients
            or not all(isinstance(t, str) and t.strip() for t in column_titles)
        ):
            raise ValueError(
                f"{source}: 'column_titles' must be a list of {patients} non-empty strings"
            )

    fields = template["handoff_fields"]
    if not isinstance(fields, list) or not fields:
        raise ValueError(f"{source}: 'handoff_fields' must be a non-empty list")
    for i, field in enumerate(fields, start=1):
        if not isinstance(field, dict):
            raise ValueError(f"{source}: handoff_field #{i} must be an object")
        unknown = set(field) - ALLOWED_FIELD_KEYS
        if unknown:
            raise ValueError(
                f"{source}: handoff_field #{i} has unknown key(s) {sorted(unknown)}"
            )
        if not isinstance(field.get("label"), str) or not field["label"].strip():
            raise ValueError(f"{source}: handoff_field #{i} needs a non-empty 'label'")
        if "hint" in field and not isinstance(field["hint"], str):
            raise ValueError(f"{source}: handoff_field #{i} 'hint' must be a string")
        if "options" in field:
            opts = field["options"]
            if (
                not isinstance(opts, list)
                or not opts
                or len(opts) > 8
                or not all(isinstance(o, str) and o.strip() for o in opts)
            ):
                raise ValueError(
                    f"{source}: handoff_field #{i} 'options' must be a list of "
                    f"1-8 non-empty strings"
                )

    slots = template["time_slots"]
    if (
        not isinstance(slots, list)
        or not 1 <= len(slots) <= 12
        or not all(isinstance(s, str) and s.strip() for s in slots)
    ):
        raise ValueError(
            f"{source}: 'time_slots' must be a list of 1-12 non-empty strings"
        )
    slot_height = template.get("slot_height", 46)
    if not isinstance(slot_height, int) or not 24 <= slot_height <= 96:
        raise ValueError(f"{source}: 'slot_height' must be an integer between 24 and 96")

    areas = template["note_areas"]
    if not isinstance(areas, list) or not areas:
        raise ValueError(f"{source}: 'note_areas' must be a non-empty list")
    for i, area in enumerate(areas, start=1):
        if not isinstance(area, dict):
            raise ValueError(f"{source}: note_area #{i} must be an object")
        unknown = set(area) - ALLOWED_NOTE_KEYS
        if unknown:
            raise ValueError(
                f"{source}: note_area #{i} has unknown key(s) {sorted(unknown)}"
            )
        if not isinstance(area.get("title"), str) or not area["title"].strip():
            raise ValueError(f"{source}: note_area #{i} needs a non-empty 'title'")
        lines = area.get("lines")
        if not isinstance(lines, int) or not 1 <= lines <= 40:
            raise ValueError(f"{source}: note_area #{i} 'lines' must be 1-40")
    return template


def load_templates(templates_dir: Path = TEMPLATES_DIR) -> list[dict]:
    if not templates_dir.is_dir():
        raise FileNotFoundError(f"templates folder not found: {templates_dir}")
    paths = sorted(templates_dir.glob("*.json"))
    if not paths:
        raise FileNotFoundError(f"no *.json templates found in {templates_dir}")
    templates = []
    for path in paths:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}: invalid JSON: {exc}") from exc
        templates.append(validate_template(raw, source=str(path)))
    names = [t["name"] for t in templates]
    if len(set(names)) != len(names):
        raise ValueError(f"duplicate template names: {names}")
    return templates


def default_file_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return f"{slug}_brain_sheet"


def _entry_cell(field: dict, cell_class: str) -> str:
    inner = []
    hint = field.get("hint")
    if hint:
        inner.append(f'<span class="hint">{_e(hint)}</span>')
    options = field.get("options")
    if options:
        opts = "".join(f'<span class="opt">&#9744; {_e(o)}</span>' for o in options)
        inner.append(opts)
    body = "".join(inner)
    return f'<td class="{cell_class}">{body}</td>'


def render(template: dict) -> str:
    patients = template.get("patients", 4)
    title = template["title"]
    subtitle = template.get("subtitle", "Printable blank shift form")
    column_titles = template.get("column_titles", [f"Patient {i + 1}" for i in range(patients)])
    slots = template["time_slots"]
    slot_height = template.get("slot_height", 46)
    fields = template["handoff_fields"]
    note_areas = template["note_areas"]

    colgroup_grid = '<col style="width:158px">' + "<col>" * patients
    colgroup_time = '<col style="width:110px">' + "<col>" * patients

    grid_header = "".join(
        f'<th>{_e(t)}</th>' for t in column_titles
    )
    grid_rows = []
    for field in fields:
        label_hint = field.get("hint")
        hint_html = f' <span class="hint">{_e(label_hint)}</span>' if label_hint else ""
        cells = "".join(_entry_cell(field, "entry") for _ in range(patients))
        grid_rows.append(
            f'<tr><td class="rowlabel">{_e(field["label"])}{hint_html}</td>{cells}</tr>'
        )
    grid_table = (
        "<table><colgroup>" + colgroup_grid + "</colgroup>"
        f'<thead><tr><th class="rowlabel">Shift handoff</th>{grid_header}</tr></thead>'
        "<tbody>" + "".join(grid_rows) + "</tbody></table>"
    )

    time_header = "".join(f'<th>{_e(t)}</th>' for t in column_titles)
    time_rows = []
    for slot in slots:
        cells = "".join(
            f'<td class="slot" style="height:{slot_height}px"></td>'
            for _ in range(patients)
        )
        time_rows.append(
            f'<tr><td class="rowlabel slotlabel">{_e(slot)}</td>{cells}</tr>'
        )
    time_table = (
        "<table><colgroup>" + colgroup_time + "</colgroup>"
        f'<thead><tr><th class="rowlabel">Time</th>{time_header}</tr></thead>'
        "<tbody>" + "".join(time_rows) + "</tbody></table>"
    )

    note_blocks = []
    for area in note_areas:
        lines = '<div class="rule"></div>' * area["lines"]
        note_blocks.append(
            '<div class="note-block">'
            f"<h3>{_e(area['title'])}</h3>"
            f'<div class="ruled">{lines}</div>'
            "</div>"
        )
    notes_html = "".join(note_blocks)
    footer = FOOTER.format(today=date.today().isoformat(), tmpl=_e(template["name"]))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{_e(title)} - printable blank form</title>
<style>
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  color: #111827;
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  font-size: 10pt;
}}
header.sheet-head {{
  border-bottom: 3px solid #111827;
  padding: 6pt 2pt 4pt;
}}
header.sheet-head h1 {{
  margin: 0 0 2pt;
  font-size: 16pt;
  letter-spacing: 0.01em;
}}
header.sheet-head .subtitle {{
  margin: 0 0 4pt;
  color: #374151;
  font-size: 9.5pt;
}}
.meta-bar {{
  margin: 4pt 0 2pt;
  font-size: 9.5pt;
}}
.meta-bar .blankfill {{
  display: inline-block;
  height: 13pt;
  border-bottom: 1pt solid #111827;
}}
.meta-bar .blankfill.narrow {{ width: 70pt; }}
.meta-bar .blankfill.wide {{ width: 150pt; }}
.meta-bar .item {{ margin-right: 18pt; white-space: nowrap; }}
.policy-note {{
  margin: 5pt 0 2pt;
  padding: 3pt 6pt;
  border: 1.5pt solid #111827;
  font-size: 9pt;
  font-weight: 600;
}}
h2 {{
  margin: 12pt 0 4pt;
  padding-bottom: 2pt;
  border-bottom: 2px solid #111827;
  font-size: 10.5pt;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}}
th, td {{ border: 1px solid #4b5563; padding: 3pt 5pt; vertical-align: top; }}
th {{
  background: #f3f4f6;
  font-size: 8.5pt;
  text-align: center;
  border-bottom: 2px solid #111827;
}}
th.rowlabel {{ text-align: left; }}
td.rowlabel {{
  background: #f9fafb;
  font-weight: 700;
  font-size: 8pt;
  line-height: 1.2;
}}
td.slotlabel {{ text-align: center; font-size: 8.5pt; }}
td.entry {{ height: 27px; }}
td.entry .hint {{ color: #6b7280; font-size: 7.5pt; font-style: italic; display: block; }}
td.entry .opt {{ color: #374151; font-size: 8pt; margin-right: 8pt; white-space: nowrap; }}
h3.note-title, .note-block h3 {{
  margin: 0 0 2pt;
  font-size: 9.5pt;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}}
.note-block {{ margin: 8pt 0; }}
.ruled {{ border: 1px solid #4b5563; }}
.ruled .rule {{ height: 24px; border-bottom: 1px solid #9ca3af; }}
.ruled .rule:last-child {{ border-bottom: 1px solid #4b5563; }}
footer {{
  margin-top: 14pt;
  padding-top: 4pt;
  border-top: 1px solid #6b7280;
  font-size: 8pt;
  color: #4b5563;
}}
@media print {{
  @page {{ size: letter landscape; margin: 0.35in; }}
  body {{ font-size: 9pt; }}
  h2 {{ break-after: avoid; }}
  .grid-section, .time-section {{ break-inside: avoid; }}
  .note-block {{ break-inside: avoid; }}
}}
</style>
</head>
<body>
<header class="sheet-head">
  <h1>{_e(title)}</h1>
  <p class="subtitle">{_e(subtitle)}</p>
  <p class="meta-bar">
    <span class="item">Date: <span class="blankfill wide"></span></span>
    <span class="item">Shift: <span class="blankfill narrow"></span></span>
    <span class="item">Unit: <span class="blankfill narrow"></span></span>
    <span class="item">Nurse: <span class="blankfill narrow"></span></span>
    <span class="item">Charge / resource: <span class="blankfill narrow"></span></span>
  </p>
  <p class="policy-note">Reminder: {POLICY_NOTE}</p>
</header>

<section class="grid-section">
  <h2>Shift report - handoff grid</h2>
  {grid_table}
</section>

<section class="time-section">
  <h2>Task columns by time</h2>
  {time_table}
</section>

<section class="notes-section">
  <h2>Notes</h2>
  {notes_html}
</section>

<footer>{footer}</footer>
</body>
</html>
"""


def build(
    templates_dir: Path = TEMPLATES_DIR,
    out_dir: Path = OUTPUT_DIR,
    only: list[str] | None = None,
) -> list[Path]:
    templates = load_templates(templates_dir)
    wanted = []
    for template in templates:
        if only is None:
            wanted.append(template)
            continue
        match = any(
            token == template["name"]
            or token == default_file_name(template["name"]).removesuffix("_brain_sheet")
            for token in only
        )
        if match:
            wanted.append(template)
    if only is not None and not wanted:
        available = ", ".join(t["name"] for t in templates)
        raise ValueError(f"no template matching {only}; available: {available}")
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for template in wanted:
        file_name = template.get("file_name", default_file_name(template["name"]))
        target = out_dir / f"{file_name}.html"
        target.write_text(render(template), encoding="utf-8")
        written.append(target)
    return written


def _list_templates(templates_dir: Path) -> int:
    for template in load_templates(templates_dir):
        file_name = template.get("file_name", default_file_name(template["name"]))
        print(
            f"{template['name']:12} -> {file_name}.html | "
            f"{len(template['handoff_fields'])} handoff rows, "
            f"{len(template['time_slots'])} time slots, "
            f"{len(template['note_areas'])} note areas"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build printable, blank shift brain sheet HTML forms from JSON "
            "templates. Education aid only, never medical advice; no patient "
            "data is stored."
        )
    )
    parser.add_argument(
        "--templates",
        type=Path,
        default=TEMPLATES_DIR,
        help="folder containing *.json templates (default: ./templates)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=OUTPUT_DIR,
        help="folder for generated HTML (default: ./output)",
    )
    parser.add_argument(
        "--template",
        action="append",
        default=[],
        metavar="NAME",
        help="build only the named template (repeatable; default: all)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list available templates and exit",
    )
    args = parser.parse_args(argv)
    try:
        if args.list:
            return _list_templates(args.templates)
        written = build(args.templates, args.out, only=args.template or None)
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for path in written:
        print(f"built {path}")
    print(f"{len(written)} sheet(s) written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
