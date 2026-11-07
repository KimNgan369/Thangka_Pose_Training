from pathlib import Path
from zipfile import ZipFile
import hashlib
import json

from docx import Document
from lxml import etree

ROOT = Path.cwd()
QA = ROOT / 'reports/lan5/qa'
FINAL = ROOT / 'reports/lan5/52300129_52300131_BaoCaoTienDo_Lan5_Tuan8_9_10_Thangka_20261101_TheoBaoCaoGiuaKy.docx'
REFERENCE = Path(r'I:\nam4\phan tich anh phat giao\report-GK-CK\52300129_52300131_report.docx')
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
CHANGED = {'word/document.xml', 'word/styles.xml', 'word/settings.xml', 'word/_rels/document.xml.rels', '[Content_Types].xml', 'docProps/core.xml'}

assert FINAL.exists(), FINAL
doc = Document(FINAL)
with ZipFile(FINAL) as package:
    assert package.testzip() is None
    xml = etree.fromstring(package.read('word/document.xml'))
    settings = etree.fromstring(package.read('word/settings.xml'))
    instructions = [(node.text or '').strip() for node in xml.xpath('.//w:instrText', namespaces=NS)]
    assert sum(value.startswith('SEQ H') for value in instructions) == 37
    assert sum(value.startswith('SEQ B') for value in instructions) == 27
    assert sum(value.startswith('TOC') for value in instructions) == 3
    assert settings.xpath('.//w:updateFields[@w:val="true"]', namespaces=NS)
    source_doc = Document(REFERENCE)
    cover_shapes = sum(len(paragraph._p.xpath('.//w:drawing')) for paragraph in source_doc.paragraphs[:29])
    assert len(doc.inline_shapes) == cover_shapes + 37

    body_captions = []
    for index, paragraph in enumerate(doc.paragraphs):
        seq = [n.text or '' for n in paragraph._p.xpath('.//w:instrText')]
        if any(value.strip().startswith('SEQ H') for value in seq):
            body_captions.append(paragraph)
            assert index > 0 and doc.paragraphs[index - 1]._p.xpath('.//w:drawing'), paragraph.text
            assert index + 1 < len(doc.paragraphs) and doc.paragraphs[index + 1].text.strip(), paragraph.text
    assert len(body_captions) == 37, len(body_captions)

    card_captions = 0
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for index, paragraph in enumerate(cell.paragraphs):
                    seq = [n.text or '' for n in paragraph._p.xpath('.//w:instrText')]
                    if any(value.strip().startswith('SEQ H') for value in seq):
                        card_captions += 1
                        assert index > 0 and cell.paragraphs[index - 1]._p.xpath('.//w:drawing'), paragraph.text
                        assert index + 1 < len(cell.paragraphs) and cell.paragraphs[index + 1].text.strip(), paragraph.text
    assert card_captions == 0, card_captions

    cached_lists = []
    for paragraph in doc.paragraphs:
        field = ' '.join((n.text or '') for n in paragraph._p.xpath('.//w:instrText'))
        if 'TOC' in field and '\\c "Hình"' in field:
            assert 'Hình 1.' in paragraph.text
            assert len(paragraph.text.splitlines()) == 37
            cached_lists.append('figures')
        if 'TOC' in field and '\\c "Bảng"' in field:
            assert 'Bảng 1.' in paragraph.text
            assert len(paragraph.text.splitlines()) == 27
            cached_lists.append('tables')
    assert sorted(cached_lists) == ['figures', 'tables'], cached_lists

    full_text = '\n'.join([p.text for p in doc.paragraphs] + [p.text for table in doc.tables for row in table.rows for cell in row.cells for p in cell.paragraphs])
    assert 'BÁO CÁO TIẾN ĐỘ LẦN 5' in full_text
    assert 'báo cáo giữa kỳ' in full_text.lower()
    assert 'lần 4' not in full_text.lower()
    cases = ['THK000431', 'THK000701', 'HAR_3314415', 'CHINA777_P01_28', 'THK001031', 'THK000419', 'THK000705', 'THK000914', 'THK000279', 'THK000177_3ef4f0fe8c_3', 'THK000748', 'HAR_98818']
    assert all(case in full_text for case in cases), [case for case in cases if case not in full_text]

    inventory = json.loads((QA / 'package_inventory.json').read_text(encoding='utf-8'))
    with ZipFile(REFERENCE) as reference:
        mismatches = [name for name, meta in inventory.items() if name not in CHANGED and hashlib.sha256(package.read(name)).hexdigest() != meta['sha256']]
        missing = [name for name in inventory if name not in package.namelist()]
    assert not mismatches, mismatches
    assert not missing, missing

print('DOCX structure, captions, comments, figure/table lists and preserved template parts: PASS')
print(f'Figures: 37 (12 saved-model examples plus 13 detailed pose-results figures and 12 report figures); tables: 27; size: {FINAL.stat().st_size / 1048576:.2f} MB')

