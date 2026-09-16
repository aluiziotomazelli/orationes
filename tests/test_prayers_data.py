#!/usr/bin/env python3
"""
Test Suite for Orationes Liturgical Compendium
Validates prayer schemas, HTML tag integrity, JS/JSON synchronization, and index.html linking.
"""

import os
import re
import json
import glob
import unittest
from html.parser import HTMLParser

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PRAYERS_DIR = os.path.join(BASE_DIR, 'data', 'prayers')
INDEX_HTML = os.path.join(BASE_DIR, 'index.html')


class TagBalanceParser(HTMLParser):
    """Checks for unclosed or improperly nested HTML inline tags."""
    VOID_TAGS = {'br', 'hr', 'img', 'meta', 'link', 'input'}

    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() not in self.VOID_TAGS:
            self.stack.append(tag.lower())

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in self.VOID_TAGS:
            return
        if not self.stack:
            self.errors.append(f"Unexpected closing tag </{tag}> without matching opening tag")
            return
        last = self.stack.pop()
        if last != tag_lower:
            self.errors.append(f"Mismatched closing tag: expected </{last}>, found </{tag}>")


def validate_html_strings(obj, path=""):
    """Recursively validates HTML strings inside a dict/list."""
    errors = []
    if isinstance(obj, str):
        if '<' in obj and '>' in obj:
            parser = TagBalanceParser()
            parser.feed(obj)
            for err in parser.errors:
                errors.append(f"{path}: {err} in text: '{obj[:60]}...'")
            if parser.stack:
                errors.append(f"{path}: Unclosed tags {parser.stack} in text: '{obj[:60]}...'")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            errors.extend(validate_html_strings(v, f"{path}.{k}" if path else k))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            errors.extend(validate_html_strings(item, f"{path}[{i}]"))
    return errors


class TestPrayersData(unittest.TestCase):

    def setUp(self):
        self.json_files = glob.glob(os.path.join(PRAYERS_DIR, '*.json'))
        self.assertTrue(len(self.json_files) > 0, "No prayer JSON files found in data/prayers/")

    def test_json_validity_and_schema(self):
        valid_types = {
            'section_header', 'psalm_title', 'rubric', 'dialogue',
            'prayer', 'prayer_ref', 'hymn_stanza', 'oratio', 'psalm_verse'
        }

        for path in self.json_files:
            filename = os.path.basename(path)
            with self.subTest(file=filename):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.assertIn('id', data, f"{filename} missing 'id'")
                self.assertIn('title', data, f"{filename} missing 'title'")
                self.assertIn('la', data['title'], f"{filename} missing Latin title ('title.la')")
                self.assertIn('items', data, f"{filename} missing 'items'")
                self.assertIsInstance(data['items'], list, f"{filename} 'items' must be a list")
                self.assertGreater(len(data['items']), 0, f"{filename} 'items' list cannot be empty")

                for idx, item in enumerate(data['items']):
                    self.assertIn('type', item, f"{filename} items[{idx}] missing 'type'")
                    self.assertIn(item['type'], valid_types, f"{filename} items[{idx}] invalid type: {item['type']}")

                    if item['type'] == 'dialogue':
                        self.assertIn('v', item, f"{filename} dialogue at [{idx}] missing 'v'")
                        self.assertIn('r', item, f"{filename} dialogue at [{idx}] missing 'r'")
                        self.assertIn('la', item['v'], f"{filename} dialogue at [{idx}].v missing 'la'")
                        self.assertIn('la', item['r'], f"{filename} dialogue at [{idx}].r missing 'la'")
                    elif item['type'] in ('prayer', 'prayer_ref', 'hymn_stanza'):
                        self.assertIn('text', item, f"{filename} {item['type']} at [{idx}] missing 'text'")
                        self.assertIn('la', item['text'], f"{filename} {item['type']} at [{idx}].text missing 'la'")
                    elif item['type'] == 'rubric':
                        self.assertIn('text', item, f"{filename} rubric at [{idx}] missing 'text'")
                        self.assertIn('la', item['text'], f"{filename} rubric at [{idx}].text missing 'la'")
                    elif item['type'] == 'oratio':
                        self.assertIn('label', item, f"{filename} oratio at [{idx}] missing 'label'")
                        self.assertIn('text', item, f"{filename} oratio at [{idx}] missing 'text'")
                        self.assertIn('amen', item, f"{filename} oratio at [{idx}] missing 'amen'")
                        self.assertIn('la', item['label'], f"{filename} oratio label at [{idx}] missing 'la'")
                        self.assertIn('la', item['text'], f"{filename} oratio text at [{idx}] missing 'la'")
                        self.assertIn('la', item['amen'], f"{filename} oratio amen at [{idx}] missing 'la'")
                    elif item['type'] == 'psalm_verse':
                        self.assertIn('text', item, f"{filename} psalm_verse at [{idx}] missing 'text'")
                        self.assertIn('la', item['text'], f"{filename} psalm_verse at [{idx}].text missing 'la'")
                    elif item['type'] == 'section_header':
                        self.assertIn('title', item, f"{filename} section_header at [{idx}] missing 'title'")
                        self.assertIn('la', item['title'], f"{filename} section_header at [{idx}].title missing 'la'")

    def test_html_tag_balance(self):
        for path in self.json_files:
            filename = os.path.basename(path)
            with self.subTest(file=filename):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                errors = validate_html_strings(data)
                self.assertEqual(len(errors), 0, f"{filename} has HTML formatting errors:\n" + "\n".join(errors))

    def test_js_file_parity(self):
        for path in self.json_files:
            js_path = path[:-5] + '.js'
            filename = os.path.basename(path)
            self.assertTrue(os.path.exists(js_path), f"Missing matching JS file for {filename}: {js_path}")

            with open(path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            with open(js_path, 'r', encoding='utf-8') as f:
                js_content = f.read()

            # Extract json payload assigned in js file
            match = re.search(r'window\.ORATIONES_DATA\.\w+\s*=\s*(\{[\s\S]*\});?\s*$', js_content)
            self.assertIsNotNone(match, f"{js_path} does not match expected window.ORATIONES_DATA assignment syntax")
            js_data = json.loads(match.group(1))

            self.assertEqual(json_data, js_data, f"{filename} and its corresponding .js file content mismatch")

    def test_index_html_integration(self):
        self.assertTrue(os.path.exists(INDEX_HTML), "index.html not found")
        with open(INDEX_HTML, 'r', encoding='utf-8') as f:
            html = f.read()

        for path in self.json_files:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            prayer_id = data['id']

            # Verify that prayer JS is loaded via script tag
            expected_script = f'src="data/prayers/{prayer_id}.js"'
            self.assertIn(expected_script, html, f"index.html does not load script for prayer '{prayer_id}' ({expected_script})")

            # Verify that home view contains a card link
            expected_card_link = f'href="#{prayer_id}"'
            self.assertIn(expected_card_link, html, f"index.html does not contain home card link for '{prayer_id}' ({expected_card_link})")


if __name__ == '__main__':
    unittest.main(verbosity=2)
