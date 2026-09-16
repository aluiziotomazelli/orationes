#!/usr/bin/env python3
"""
Imports translations from a filled OpenDocument Text (.odt) template into prayer JSON/JS.
Zero external dependencies (uses standard library zipfile and xml.etree.ElementTree).
"""

import os
import sys
import json
import zipfile
import xml.etree.ElementTree as ET

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PRAYERS_DIR = os.path.join(BASE_DIR, 'data', 'prayers')

# XML Namespaces for OpenDocument
NS = {
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
}


def extract_text_from_cell(cell_elem):
    """Extracts all text content from an ODT table cell element."""
    text_pieces = []
    for p in cell_elem.findall('.//text:p', NS):
        p_text = "".join(p.itertext()).strip()
        if p_text:
            text_pieces.append(p_text)
    return "\n".join(text_pieces)


def import_odt(odt_path, prayer_id, lang_code="fr", lang_label="Français"):
    if not os.path.exists(odt_path):
        raise FileNotFoundError(f"ODT template not found: {odt_path}")

    json_path = os.path.join(PRAYERS_DIR, f"{prayer_id}.json")
    js_path = os.path.join(PRAYERS_DIR, f"{prayer_id}.js")

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Prayer JSON not found: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        prayer_data = json.load(f)

    # Read and parse content.xml from ODT zip
    with zipfile.ZipFile(odt_path, 'r') as z:
        content_xml_bytes = z.read('content.xml')

    root = ET.fromstring(content_xml_bytes)
    table = root.find('.//table:table', NS)
    if table is None:
        raise ValueError("Could not find table in ODT document")

    rows = table.findall('table:table-row', NS)
    # Skip header row (index 0)
    data_rows = rows[1:]

    # Map table rows to prayer items
    table_index = 0

    for item in prayer_data.get('items', []):
        itype = item.get('type')

        if itype == 'section_header':
            table_index += 1
        elif itype == 'psalm_title':
            table_index += 1
        elif itype == 'rubric':
            if table_index < len(data_rows):
                cells = data_rows[table_index].findall('table:table-cell', NS)
                if len(cells) >= 2:
                    val = extract_text_from_cell(cells[1])
                    if val and not val.startswith('[Rubrica'):
                        item['text'][lang_code] = val
                table_index += 1
        elif itype == 'dialogue':
            # Dialogue has 2 rows: V and R
            if table_index < len(data_rows):
                v_cells = data_rows[table_index].findall('table:table-cell', NS)
                if len(v_cells) >= 2:
                    v_val = extract_text_from_cell(v_cells[1])
                    v_val = v_val.replace('℣.', '').replace('V.', '').strip()
                    if v_val:
                        item['v'][lang_code] = v_val
                table_index += 1

            if table_index < len(data_rows):
                r_cells = data_rows[table_index].findall('table:table-cell', NS)
                if len(r_cells) >= 2:
                    r_val = extract_text_from_cell(r_cells[1])
                    r_val = r_val.replace('℟.', '').replace('R.', '').strip()
                    if r_val:
                        item['r'][lang_code] = r_val
                table_index += 1
        elif itype == 'psalm_verse':
            if table_index < len(data_rows):
                cells = data_rows[table_index].findall('table:table-cell', NS)
                if len(cells) >= 2:
                    val = extract_text_from_cell(cells[1])
                    # Remove verse number prefix if typed in
                    if item.get('num'):
                        val = val.lstrip(item['num']).strip()
                    if val:
                        item['text'][lang_code] = val
                table_index += 1
        elif itype in ('prayer', 'prayer_ref', 'hymn_stanza'):
            if table_index < len(data_rows):
                cells = data_rows[table_index].findall('table:table-cell', NS)
                if len(cells) >= 2:
                    val = extract_text_from_cell(cells[1])
                    if val:
                        item['text'][lang_code] = val.replace('\n', '<br>')
                table_index += 1
        elif itype == 'oratio':
            if table_index < len(data_rows):
                cells = data_rows[table_index].findall('table:table-cell', NS)
                if len(cells) >= 2:
                    val = extract_text_from_cell(cells[1])
                    if val:
                        lines = [l.strip() for l in val.split('\n') if l.strip()]
                        if lines:
                            item['text'][lang_code] = lines[0]
                table_index += 1

    # Add language to availableLangs if not already present
    available = prayer_data.setdefault('availableLangs', [])
    if not any(l.get('code') == lang_code for l in available):
        available.append({'code': lang_code, 'label': lang_label})

    # Save updated JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(prayer_data, f, ensure_ascii=False, indent=2)

    # Save updated JS
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(f"// {prayer_data.get('title', {}).get('la', prayer_id)} Data\n")
        f.write("window.ORATIONES_DATA = window.ORATIONES_DATA || {};\n")
        f.write(f"window.ORATIONES_DATA.{prayer_id} = ")
        json.dump(prayer_data, f, ensure_ascii=False, indent=2)
        f.write(";\n")

    print(f"Tradução '{lang_code}' importada com sucesso para {json_path} e {js_path}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Uso: python3 scripts/import_odt_translation.py <arquivo.odt> <id_da_oracao> [codigo_idioma] [rotulo_idioma]")
        print("Exemplo: python3 scripts/import_odt_translation.py templates/angelus_traducao_français.odt angelus fr Français")
        sys.exit(1)

    odt_file = sys.argv[1]
    p_id = sys.argv[2]
    code = sys.argv[3] if len(sys.argv) > 3 else 'fr'
    label = sys.argv[4] if len(sys.argv) > 4 else 'Français'

    import_odt(odt_file, p_id, code, label)
