#!/usr/bin/env python3
"""
Test Suite for Orationes Assets, PDFs, and Link Integrity.
Validates existence of local files, PDF magic numbers, CSS variables, and external URLs.
"""

import os
import re
import glob
import urllib.parse
import unittest
from html.parser import HTMLParser

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PRINT_DIR = os.path.join(BASE_DIR, 'print')
DATA_DIR = os.path.join(BASE_DIR, 'data')
LATIN_DIR = os.path.join(DATA_DIR, 'latin')
PRAYERS_DIR = os.path.join(DATA_DIR, 'prayers')
INDEX_HTML = os.path.join(BASE_DIR, 'index.html')
STYLE_CSS = os.path.join(BASE_DIR, 'style.css')


class LocalAssetExtractor(HTMLParser):
    """Extracts local static references (stylesheets, scripts, images) from HTML."""
    def __init__(self):
        super().__init__()
        self.local_assets = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        target = None
        if tag == 'link' and attr_dict.get('rel') == 'stylesheet':
            target = attr_dict.get('href')
        elif tag == 'script' and 'src' in attr_dict:
            target = attr_dict.get('src')
        elif tag == 'img' and 'src' in attr_dict:
            target = attr_dict.get('src')

        if target and not target.startswith(('http://', 'https://', '//', '#')):
            self.local_assets.append(target)


class TestAssetsAndLinks(unittest.TestCase):

    def test_html_local_assets_exist(self):
        """Verifies that all local CSS, JS, and image files referenced in index.html exist on disk."""
        self.assertTrue(os.path.exists(INDEX_HTML), "index.html not found")
        with open(INDEX_HTML, 'r', encoding='utf-8') as f:
            content = f.read()

        extractor = LocalAssetExtractor()
        extractor.feed(content)

        self.assertGreater(len(extractor.local_assets), 0, "No local assets found in index.html")

        for asset_rel in extractor.local_assets:
            asset_path = os.path.join(BASE_DIR, asset_rel)
            with self.subTest(asset=asset_rel):
                self.assertTrue(os.path.exists(asset_path), f"Asset referenced in index.html does not exist: {asset_rel}")
                self.assertGreater(os.path.getsize(asset_path), 0, f"Asset file is empty: {asset_rel}")

    def test_css_structure_and_variables(self):
        """Verifies that style.css exists and defines critical theme variables."""
        self.assertTrue(os.path.exists(STYLE_CSS), "style.css not found")
        with open(STYLE_CSS, 'r', encoding='utf-8') as f:
            css = f.read()

        essential_vars = [
            '--bg-color',
            '--text-color',
            '--rubric-color',
            '--border-color',
            '--subtext-color'
        ]

        for var in essential_vars:
            with self.subTest(css_var=var):
                self.assertIn(var, css, f"style.css is missing essential CSS variable: {var}")

    def test_pdf_assets_integrity(self):
        """Verifies that print PDFs exist, are non-empty, and start with the %PDF- magic header."""
        self.assertTrue(os.path.exists(PRINT_DIR), "print/ directory not found")
        pdf_files = glob.glob(os.path.join(PRINT_DIR, '*.pdf'))
        self.assertGreater(len(pdf_files), 0, "No PDF documents found in print/")

        for pdf_path in pdf_files:
            filename = os.path.basename(pdf_path)
            with self.subTest(pdf=filename):
                size = os.path.getsize(pdf_path)
                self.assertGreater(size, 1024, f"PDF file {filename} is suspiciously small ({size} bytes)")
                with open(pdf_path, 'rb') as f:
                    header = f.read(5)
                self.assertEqual(header, b'%PDF-', f"File {filename} is not a valid PDF (missing %PDF- header)")

    def test_latin_source_markdown_files_exist(self):
        """Verifies that every structured prayer has a corresponding raw Latin Markdown source."""
        json_prayers = glob.glob(os.path.join(PRAYERS_DIR, '*.json'))
        self.assertGreater(len(json_prayers), 0, "No prayer JSON files found")

        for json_path in json_prayers:
            prayer_id = os.path.splitext(os.path.basename(json_path))[0]
            latin_md_path = os.path.join(LATIN_DIR, f"{prayer_id}.md")
            with self.subTest(prayer_latin_md=f"{prayer_id}.md"):
                self.assertTrue(
                    os.path.exists(latin_md_path),
                    f"Missing Latin source Markdown for '{prayer_id}': data/latin/{prayer_id}.md"
                )
                self.assertGreater(
                    os.path.getsize(latin_md_path), 50,
                    f"Latin source file data/latin/{prayer_id}.md is unexpectedly small"
                )

    def test_external_urls_syntax(self):
        """Finds all HTTP/HTTPS links across HTML and JSON files and validates their URL format."""
        files_to_scan = [INDEX_HTML] + glob.glob(os.path.join(PRAYERS_DIR, '*.json'))
        url_regex = re.compile(r'https?://[^\s"\'<>)]+')

        found_urls = set()
        for file_path in files_to_scan:
            with open(file_path, 'r', encoding='utf-8') as f:
                matches = url_regex.findall(f.read())
                for url in matches:
                    found_urls.add((url, os.path.basename(file_path)))

        self.assertGreater(len(found_urls), 0, "No external URLs found in files")

        for url, source_file in found_urls:
            with self.subTest(url=url, source=source_file):
                parsed = urllib.parse.urlparse(url)
                self.assertIn(parsed.scheme, ('http', 'https'), f"Invalid URL scheme in {source_file}: {url}")
                self.assertTrue(parsed.netloc, f"Invalid URL host/domain in {source_file}: {url}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
