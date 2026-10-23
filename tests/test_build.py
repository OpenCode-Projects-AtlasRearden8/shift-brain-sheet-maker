"""Tests for the Shift Brain Sheet Maker (stdlib unittest only)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build
from build import build as make_sheets


class BalancedHtmlParser(HTMLParser):
    VOID = {"meta", "br", "hr", "img", "input", "link", "col"}

    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack:
            self.errors.append(f"closing </{tag}> with empty stack")
            return
        open_tag = self.stack.pop()
        if open_tag != tag:
            self.errors.append(f"expected </{open_tag}>, got </{tag}>")


def render_html_for(template_path: str) -> str:
    templates = {t["name"]: t for t in build.load_templates()}
    return build.render(templates[template_path])


class TemplateLoadingTestCase(unittest.TestCase):
    def test_loads_three_sample_templates(self):
        templates = build.load_templates()
        self.assertEqual(len(templates), 3)
        names = {t["name"] for t in templates}
        self.assertEqual(names, {"med-surg", "mom-baby", "float"})

    def test_missing_required_key_is_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            build.validate_template({"name": "x"})
        self.assertIn("missing required key", str(ctx.exception))

    def test_unknown_key_is_rejected(self):
        bad = {
            "name": "bad",
            "title": "Bad",
            "handoff_fields": [{"label": "a"}],
            "time_slots": ["0800"],
            "note_areas": [{"title": "n", "lines": 3}],
            "time-slots": ["wrong"],
        }
        with self.assertRaises(ValueError) as ctx:
            build.validate_template(bad)
        self.assertIn("unknown key(s)", str(ctx.exception))

    def test_missing_label_is_rejected(self):
        bad = {
            "name": "bad",
            "title": "Bad",
            "handoff_fields": [{"hint": "no label"}],
            "time_slots": ["0800"],
            "note_areas": [{"title": "n", "lines": 3}],
        }
        with self.assertRaises(ValueError):
            build.validate_template(bad)

    def test_patients_out_of_range_is_rejected(self):
        bad = {
            "name": "bad",
            "title": "Bad",
            "patients": 99,
            "handoff_fields": [{"label": "a"}],
            "time_slots": ["0800"],
            "note_areas": [{"title": "n", "lines": 3}],
        }
        with self.assertRaises(ValueError):
            build.validate_template(bad)

    def test_missing_templates_dir_raises(self):
        with self.assertRaises(FileNotFoundError):
            build.load_templates(Path("does/not/exist"))


class RenderedHtmlTestCase(unittest.TestCase):
    def setUp(self):
        self.handles = ["med-surg", "mom-baby", "float"]
        self.htmls = {name: render_html_for(name) for name in self.handles}

    def test_html_is_balanced(self):
        for name, html in self.htmls.items():
            parser = BalancedHtmlParser()
            parser.feed(html)
            self.assertEqual(parser.stack, [], f"{name}: unclosed tags {parser.stack}")
            self.assertEqual(parser.errors, [], f"{name}: {parser.errors}")

    def test_every_sheet_prints_facility_policy_and_not_advice(self):
        for name, html in self.htmls.items():
            self.assertIn("not medical advice", html, name)
            self.assertIn("facility's policy", html, name)

    def test_no_patient_data_statement_and_no_user_content(self):
        for name, html in self.htmls.items():
            body_part = html.split("</style>", 1)[1]
            self.assertIn("no patient data is stored", body_part, name)
            self.assertNotIn("{", body_part, name)

    def test_checker_catches_mismatched_tags(self):
        checker = BalancedHtmlParser()
        checker.feed("<div><p></div>")
        self.assertTrue(any("expected" in e for e in checker.errors))

    def test_handoff_grid_has_label_row_per_field(self):
        templates = {t["name"]: t for t in build.load_templates()}
        for name, html in self.htmls.items():
            grid_part = html.split("Task columns by time", 1)[0]
            expected = len(templates[name]["handoff_fields"])
            self.assertEqual(
                grid_part.count('<td class="rowlabel">'), expected, name
            )

    def test_time_slot_cells_match_patients_times_slots(self):
        templates = {t["name"]: t for t in build.load_templates()}
        for name, html in self.htmls.items():
            template = templates[name]
            expected = template.get("patients", 4) * len(template["time_slots"])
            self.assertEqual(html.count('class="slot"'), expected, name)

    def test_time_slot_labels_use_distinct_class(self):
        html = self.htmls["med-surg"]
        self.assertEqual(html.count('class="rowlabel slotlabel"'), 6)

    def test_note_areas_have_ruled_lines(self):
        templates = {t["name"]: t for t in build.load_templates()}
        for name, html in self.htmls.items():
            expected = sum(a["lines"] for a in templates[name]["note_areas"])
            self.assertEqual(html.count('<div class="rule"></div>'), expected, name)

    def test_column_titles_rendered(self):
        html = self.htmls["mom-baby"]
        self.assertIn("Pair 1: Parent + Newborn", html)
        self.assertIn("Pair 3: Parent + Newborn", html)


class BuildOutputTestCase(unittest.TestCase):
    def test_build_writes_html_files(self):
        templates = build.load_templates()
        for template in templates:
            with tempfile.TemporaryDirectory() as tmp:
                out_dir = Path(tmp)
                paths = make_sheets(out_dir=out_dir, only=[template["name"]])
                self.assertEqual(len(paths), 1)
                html = paths[0].read_text(encoding="utf-8")
                self.assertIn(template["title"], html)
                self.assertIn("<!DOCTYPE html>", html)
                self.assertEqual(paths[0].suffix, ".html")

    def test_build_unknown_template_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError) as ctx:
                make_sheets(out_dir=Path(tmp), only=["nope"])
            self.assertIn("available:", str(ctx.exception))

    def test_default_file_names_are_unique_and_safe(self):
        templates = build.load_templates()
        names = []
        for template in templates:
            file_name = template.get("file_name", build.default_file_name(template["name"]))
            names.append(file_name)
            self.assertRegex(file_name, r"^[a-z0-9_]+$")
        self.assertEqual(len(set(names)), len(names))


class ProjectFilesTestCase(unittest.TestCase):
    def test_license_contains_exact_copyright(self):
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Copyright (c) 2026 Asdale Dynamics, LLC", license_text)
        self.assertIn("Permission is hereby granted, free of charge", license_text)

    def test_readme_credits_llc_and_explains_run(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Asdale Dynamics, LLC", readme)
        self.assertIn("python build.py", readme)


if __name__ == "__main__":
    unittest.main()
