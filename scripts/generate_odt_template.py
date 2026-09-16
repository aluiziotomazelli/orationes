#!/usr/bin/env python3
"""
Generates clean OpenDocument Text (.odt) translation templates from prayer JSON files.
Zero external dependencies (uses standard library zipfile and xml generation).
"""

import os
import sys
import json
import zipfile
import html
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PRAYERS_DIR = os.path.join(BASE_DIR, 'data', 'prayers')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')


def clean_html(raw_html):
    """Converts basic HTML formatting into plain text or clean representation for ODT."""
    if not raw_html:
        return ""
    text = raw_html.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
    text = re.sub(r'<span class="asterisk">\*</span>', '*', text)
    text = re.sub(r'<span class="v-num">(\d+)</span>', r'\1', text)
    text = re.sub(r'<span class="[vr]-sym">([℣℟]\.)</span>', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()


def build_manifest_xml():
    return '''<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">
  <manifest:file-entry manifest:full-path="/" manifest:version="1.2" manifest:media-type="application/vnd.oasis.opendocument.text"/>
  <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
</manifest:manifest>'''


def build_styles_xml():
    return '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
  xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  office:version="1.2">
  <office:font-face-decls>
    <style:font-face style:name="EB Garamond" svg:font-family="'EB Garamond', 'Georgia', serif"/>
  </office:font-face-decls>
  <office:styles>
    <style:default-style style:family="paragraph">
      <style:paragraph-properties fo:line-height="125%" fo:margin-top="0cm" fo:margin-bottom="0.15cm"/>
      <style:text-properties style:font-name="EB Garamond" fo:font-size="11pt" fo:color="#1c1a17"/>
    </style:default-style>
  </office:styles>
  <office:master-styles>
    <style:master-page style:name="Standard" style:page-layout-name="PM1"/>
  </office:master-styles>
</office:document-styles>'''


def escape_xml(text):
    return html.escape(text or '')


def build_content_xml(prayer_data, target_lang_name="Français"):
    prayer_title_la = prayer_data.get('title', {}).get('la', 'Oratio')
    prayer_sub_la = prayer_data.get('subtitle', {}).get('la', '')

    rows_xml = []

    # Table Header Row
    rows_xml.append('''
      <table:table-row>
        <table:table-cell office:value-type="string" table:style-name="HeaderCell">
          <text:p text:style-name="ColHeader">Latine (Texto Fonte)</text:p>
        </table:table-cell>
        <table:table-cell office:value-type="string" table:style-name="HeaderCell">
          <text:p text:style-name="ColHeader">''' + escape_xml(target_lang_name) + ''' (Tradução)</text:p>
        </table:table-cell>
      </table:table-row>''')

    for item in prayer_data.get('items', []):
        itype = item.get('type')

        if itype == 'section_header':
            title_la = escape_xml(clean_html(item.get('title', {}).get('la', '')))
            sub = escape_xml(clean_html(item.get('sub', '')))
            sub_xml = f'<text:p text:style-name="SectionSub">{sub}</text:p>' if sub else ''
            rows_xml.append(f'''
      <table:table-row>
        <table:table-cell table:number-columns-spanned="2" office:value-type="string" table:style-name="SectionHeaderCell">
          <text:p text:style-name="SectionTitle">{title_la}</text:p>
          {sub_xml}
        </table:table-cell>
        <table:covered-table-cell/>
      </table:table-row>''')

        elif itype == 'psalm_title':
            title = escape_xml(clean_html(item.get('title', '')))
            rows_xml.append(f'''
      <table:table-row>
        <table:table-cell table:number-columns-spanned="2" office:value-type="string" table:style-name="PsalmTitleCell">
          <text:p text:style-name="PsalmTitle">{title}</text:p>
        </table:table-cell>
        <table:covered-table-cell/>
      </table:table-row>''')

        elif itype == 'rubric':
            rubric_la = escape_xml(clean_html(item.get('text', {}).get('la', '')))
            rows_xml.append(f'''
      <table:table-row>
        <table:table-cell office:value-type="string" table:style-name="RubricCell">
          <text:p text:style-name="RubricText">{rubric_la}</text:p>
        </table:table-cell>
        <table:table-cell office:value-type="string" table:style-name="DataCell">
          <text:p text:style-name="RubricPrompt">[Rubrica em {escape_xml(target_lang_name)}]</text:p>
        </table:table-cell>
      </table:table-row>''')

        elif itype == 'dialogue':
            v_la = escape_xml(clean_html(item.get('v', {}).get('la', '')))
            r_la = escape_xml(clean_html(item.get('r', {}).get('la', '')))
            rows_xml.append(f'''
      <table:table-row>
        <table:table-cell office:value-type="string" table:style-name="DataCell">
          <text:p><text:span text:style-name="RedChar">℣.</text:span> {v_la}</text:p>
        </table:table-cell>
        <table:table-cell office:value-type="string" table:style-name="DataCell">
          <text:p><text:span text:style-name="RedChar">℣.</text:span> </text:p>
        </table:table-cell>
      </table:table-row>
      <table:table-row>
        <table:table-cell office:value-type="string" table:style-name="DataCell">
          <text:p><text:span text:style-name="RedChar">℟.</text:span> {r_la}</text:p>
        </table:table-cell>
        <table:table-cell office:value-type="string" table:style-name="DataCell">
          <text:p><text:span text:style-name="RedChar">℟.</text:span> </text:p>
        </table:table-cell>
      </table:table-row>''')

        elif itype == 'psalm_verse':
            num = escape_xml(item.get('num', ''))
            v_la = escape_xml(clean_html(item.get('text', {}).get('la', '')))
            num_span = f'<text:span text:style-name="VerseNum">{num}</text:span> ' if num else ''
            rows_xml.append(f'''
      <table:table-row>
        <table:table-cell office:value-type="string" table:style-name="DataCell">
          <text:p>{num_span}{v_la}</text:p>
        </table:table-cell>
        <table:table-cell office:value-type="string" table:style-name="DataCell">
          <text:p>{num_span}</text:p>
        </table:table-cell>
      </table:table-row>''')

        elif itype in ('prayer', 'prayer_ref', 'hymn_stanza'):
            text_la = escape_xml(clean_html(item.get('text', {}).get('la', '')))
            # Multi-line handling
            lines = text_la.split('\n')
            p_xml = "".join([f'<text:p>{line}</text:p>' for line in lines])
            rows_xml.append(f'''
      <table:table-row>
        <table:table-cell office:value-type="string" table:style-name="DataCell">
          {p_xml}
        </table:table-cell>
        <table:table-cell office:value-type="string" table:style-name="DataCell">
          <text:p></text:p>
        </table:table-cell>
      </table:table-row>''')

        elif itype == 'oratio':
            lbl_la = escape_xml(clean_html(item.get('label', {}).get('la', 'Orémus.')))
            txt_la = escape_xml(clean_html(item.get('text', {}).get('la', '')))
            amen_la = escape_xml(clean_html(item.get('amen', {}).get('la', '℟. Amen.')))
            rows_xml.append(f'''
      <table:table-row>
        <table:table-cell office:value-type="string" table:style-name="DataCell">
          <text:p><text:span text:style-name="BoldText">{lbl_la}</text:span></text:p>
          <text:p>{txt_la}</text:p>
          <text:p><text:span text:style-name="RedChar">{amen_la}</text:span></text:p>
        </table:table-cell>
        <table:table-cell office:value-type="string" table:style-name="DataCell">
          <text:p><text:span text:style-name="BoldText">[Oremos.]</text:span></text:p>
          <text:p></text:p>
          <text:p><text:span text:style-name="RedChar">℟. Amen.</text:span></text:p>
        </table:table-cell>
      </table:table-row>''')

    all_rows = "\n".join(rows_xml)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
  xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  office:version="1.2">
  <office:automatic-styles>
    <style:style style:name="Table1" style:family="table">
      <style:table-properties style:width="17cm" table:align="center"/>
    </style:style>
    <style:style style:name="Table1.Col" style:family="table-column">
      <style:table-column-properties style:column-width="8.5cm"/>
    </style:style>
    <style:style style:name="HeaderCell" style:family="table-cell">
      <style:table-cell-properties fo:background-color="#f2ede4" fo:padding="0.2cm" fo:border-bottom="0.05cm solid #990000" fo:border-top="0.02cm solid #cccccc" fo:border-left="none" fo:border-right="none"/>
    </style:style>
    <style:style style:name="SectionHeaderCell" style:family="table-cell">
      <style:table-cell-properties fo:background-color="#faf7f2" fo:padding="0.25cm 0.1cm 0.1cm 0.1cm" fo:border="none"/>
    </style:style>
    <style:style style:name="PsalmTitleCell" style:family="table-cell">
      <style:table-cell-properties fo:padding="0.2cm 0.1cm 0.05cm 0.1cm" fo:border="none"/>
    </style:style>
    <style:style style:name="RubricCell" style:family="table-cell">
      <style:table-cell-properties fo:padding="0.15cm" fo:border-bottom="0.01cm solid #eeeeee" fo:border-top="none" fo:border-left="none" fo:border-right="none"/>
    </style:style>
    <style:style style:name="DataCell" style:family="table-cell">
      <style:table-cell-properties fo:padding="0.12cm 0.15cm" fo:border-bottom="0.01cm solid #e8e3dc" fo:border-top="none" fo:border-left="none" fo:border-right="none"/>
    </style:style>

    <style:style style:name="DocTitle" style:family="paragraph">
      <style:paragraph-properties fo:text-align="center" fo:margin-bottom="0.1cm"/>
      <style:text-properties fo:font-size="16pt" fo:font-weight="bold" fo:color="#990000"/>
    </style:style>
    <style:style style:name="DocSubtitle" style:family="paragraph">
      <style:paragraph-properties fo:text-align="center" fo:margin-bottom="0.4cm"/>
      <style:text-properties fo:font-size="10pt" fo:font-style="italic" fo:color="#666666"/>
    </style:style>
    <style:style style:name="InstructionsBox" style:family="paragraph">
      <style:paragraph-properties fo:background-color="#fdfbf7" fo:padding="0.2cm" fo:border="0.01cm solid #e0d8cc" fo:margin-bottom="0.5cm"/>
      <style:text-properties fo:font-size="9.5pt" fo:color="#444444"/>
    </style:style>
    <style:style style:name="ColHeader" style:family="paragraph">
      <style:paragraph-properties fo:text-align="center"/>
      <style:text-properties fo:font-size="11pt" fo:font-weight="bold" fo:color="#990000"/>
    </style:style>
    <style:style style:name="SectionTitle" style:family="paragraph">
      <style:paragraph-properties fo:text-align="center" fo:margin-top="0.2cm" fo:margin-bottom="0.05cm"/>
      <style:text-properties fo:font-size="12pt" fo:font-weight="bold" fo:color="#990000"/>
    </style:style>
    <style:style style:name="SectionSub" style:family="paragraph">
      <style:paragraph-properties fo:text-align="center" fo:margin-bottom="0.1cm"/>
      <style:text-properties fo:font-size="9pt" fo:font-style="italic" fo:color="#990000"/>
    </style:style>
    <style:style style:name="PsalmTitle" style:family="paragraph">
      <style:paragraph-properties fo:text-align="center" fo:margin-top="0.15cm" fo:margin-bottom="0.05cm"/>
      <style:text-properties fo:font-size="11pt" fo:font-weight="bold" fo:color="#990000"/>
    </style:style>
    <style:style style:name="RubricText" style:family="paragraph">
      <style:paragraph-properties fo:text-align="center"/>
      <style:text-properties fo:font-size="9.5pt" fo:font-style="italic" fo:color="#990000"/>
    </style:style>
    <style:style style:name="RubricPrompt" style:family="paragraph">
      <style:paragraph-properties fo:text-align="center"/>
      <style:text-properties fo:font-size="9.5pt" fo:font-style="italic" fo:color="#888888"/>
    </style:style>

    <style:style style:name="RedChar" style:family="text">
      <style:text-properties fo:font-weight="bold" fo:color="#990000"/>
    </style:style>
    <style:style style:name="BoldText" style:family="text">
      <style:text-properties fo:font-weight="bold"/>
    </style:style>
    <style:style style:name="VerseNum" style:family="text">
      <style:text-properties fo:font-size="8pt" fo:font-weight="bold" fo:color="#990000"/>
    </style:style>
  </office:automatic-styles>

  <office:body>
    <office:text>
      <text:p text:style-name="DocTitle">{escape_xml(prayer_title_la)}</text:p>
      <text:p text:style-name="DocSubtitle">{escape_xml(prayer_sub_la)}</text:p>

      <text:p text:style-name="InstructionsBox">
        <text:span text:style-name="BoldText">Instruções para o Tradutor ({escape_xml(target_lang_name)}):</text:span><text:line-break/>
        1. Preencha apenas a coluna da direita com a tradução vernácula correspondente a cada linha.<text:line-break/>
        2. Mantenha os símbolos litúrgicos (℣., ℟., ✠, ✙, *) onde aplicável para preservar a métrica de recitação.<text:line-break/>
        3. Use a tecla &lt;Tab&gt; para saltar diretamente para a próxima linha de tradução.
      </text:p>

      <table:table table:name="TranslationTable" table:style-name="Table1">
        <table:table-column table:style-name="Table1.Col"/>
        <table:table-column table:style-name="Table1.Col"/>
        {all_rows}
      </table:table>
    </office:text>
  </office:body>
</office:document-content>'''


def export_odt(prayer_id, target_lang_name="Français", output_path=None):
    json_path = os.path.join(PRAYERS_DIR, f"{prayer_id}.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Prayer JSON not found: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not output_path:
        os.makedirs(TEMPLATES_DIR, exist_ok=True)
        output_path = os.path.join(TEMPLATES_DIR, f"{prayer_id}_traducao_{target_lang_name.lower()}.odt")

    content_xml = build_content_xml(data, target_lang_name)
    manifest_xml = build_manifest_xml()
    styles_xml = build_styles_xml()

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
        # mimetype must be first, uncompressed
        z.writestr('mimetype', 'application/vnd.oasis.opendocument.text', compress_type=zipfile.ZIP_STORED)
        z.writestr('META-INF/manifest.xml', manifest_xml)
        z.writestr('styles.xml', styles_xml)
        z.writestr('content.xml', content_xml)

    print(f"Template gerado com sucesso: {output_path}")
    return output_path


if __name__ == '__main__':
    prayer = sys.argv[1] if len(sys.argv) > 1 else 'completorium'
    lang = sys.argv[2] if len(sys.argv) > 2 else 'Français'
    export_odt(prayer, lang)
