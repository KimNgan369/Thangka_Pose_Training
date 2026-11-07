from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import zipfile
from pathlib import Path

from lxml import etree
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"I:\nam4\phan tich anh phat giao\training\Thangka_Pose_Training")
REPORT = ROOT / "reports/lan5/52300129_52300131_BaoCaoTienDo_Lan5_Tuan8_9_10_Thangka_20261101_TheoBaoCaoGiuaKy.docx"
QA = ROOT / "reports/lan5/qa"
BACKUP = QA / "user_edit_before_figure_number_fix_20261101.docx"
NEW_IMAGE = QA / "figure3_redesigned.png"
TEMP_DOCX = REPORT.with_name(REPORT.stem + "_rewrite.tmp.docx")

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
W = "{" + NS["w"] + "}"
R = "{" + NS["r"] + "}"
A = "{" + NS["a"] + "}"
WP = "{" + NS["wp"] + "}"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def make_diagram(path: Path) -> tuple[int, int, dict[str, int]]:
    width, height = 2200, 1040
    image = Image.new("RGB", (width, height), "#FCFDFE")
    draw = ImageDraw.Draw(image)
    regular = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 36)
    bold = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 42)
    title_font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 52)
    subtitle_font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 35)
    note_font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 31)
    badge_font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 31)

    title = "Các bước hiển thị của demo suy luận"
    subtitle = "Tái hiện luồng demo; không phải một lượt suy luận mới."
    draw.text((width // 2, 28), title, font=title_font, fill="#172B3A", anchor="ma")
    draw.text((width // 2, 97), subtitle, font=subtitle_font, fill="#516779", anchor="ma")

    rows = [
        ("Ảnh đầu vào", "Ảnh Thangka đã được cắt (crop).", "#4E78A0", "#EDF4FA"),
        ("Ước lượng tư thế", "YOLO11n-pose tạo khung bao và 17 điểm mốc.", "#2D8B83", "#EDF7F5"),
        ("Phân loại từ ảnh", "Ba mô hình ResNet-18; phân loại ở hai cấp L1 và L2.", "#5C78AF", "#F0F3FA"),
        ("Cổng quyết định", "Ngưỡng L1, bằng chứng và ngưỡng riêng cho L2.", "#C9893F", "#FBF4EA"),
        ("Kết quả demo", "Nhãn, phương án dự phòng hoặc từ chối; kèm biểu đồ độ tin cậy.", "#9070A8", "#F5F0F8"),
    ]

    def wrap(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = word if not current else current + " " + word
            if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    row_y0, row_h, gap = 168, 120, 12
    left, right = 58, width - 58
    badge_x = 137
    title_x, title_w = 207, 450
    body_x, body_right = 700, width - 98
    line_h = 43
    drawn_line_widths: dict[str, int] = {}
    draw.line(
        (badge_x, row_y0 + row_h // 2, badge_x, row_y0 + 4 * (row_h + gap) + row_h // 2),
        fill="#CBD5DF",
        width=5,
    )

    for index, (label, body, accent, fill) in enumerate(rows, start=1):
        y = row_y0 + (index - 1) * (row_h + gap)
        draw.rounded_rectangle((left, y, right, y + row_h), radius=18, fill=fill, outline=accent, width=3)
        draw.rounded_rectangle((left, y, left + 12, y + row_h), radius=6, fill=accent)
        cy = y + row_h // 2
        draw.ellipse((badge_x - 34, cy - 34, badge_x + 34, cy + 34), fill=accent)
        draw.text((badge_x, cy), f"{index:02d}", font=badge_font, fill="#FFFFFF", anchor="mm")

        label_box = draw.textbbox((0, 0), label, font=bold)
        label_h = label_box[3] - label_box[1]
        draw.text((title_x, cy - label_h // 2 - label_box[1]), label, font=bold, fill="#1F2F3B")
        label_width = label_box[2] - label_box[0]
        if label_width > title_w:
            raise ValueError(f"Step label exceeds its column: {label!r} ({label_width}px)")

        lines = wrap(body, regular, body_right - body_x)
        if len(lines) > 2:
            raise ValueError(f"Step description would exceed two lines: {body!r}")
        block_h = len(lines) * line_h
        first_y = cy - block_h // 2 - draw.textbbox((0, 0), lines[0], font=regular)[1]
        for line_index, line in enumerate(lines):
            line_width = draw.textbbox((0, 0), line, font=regular)[2]
            if line_width > body_right - body_x:
                raise ValueError(f"Step description exceeds its column: {line!r}")
            draw.text((body_x, first_y + line_index * line_h), line, font=regular, fill="#273844")
            drawn_line_widths[f"step_{index}_line_{line_index + 1}"] = line_width

    note = (
        "Cấu hình triển khai đã chọn image_weight = 1,0. Nhánh tư thế hỗ trợ trực quan và được giữ làm nhánh đối chứng; "
        "kết quả phân loại hiện hành do nhánh ảnh quyết định."
    )
    note_lines = wrap(note, note_font, width - 208)
    if len(note_lines) > 2:
        raise ValueError("The configuration note would exceed two lines.")
    note_box = (58, 842, width - 58, 1012)
    draw.rounded_rectangle(note_box, radius=17, fill="#FFF9F0", outline="#D9A76D", width=2)
    note_line_h = 39
    note_block_h = len(note_lines) * note_line_h
    note_first_y = (note_box[1] + note_box[3] - note_block_h) // 2
    note_x = note_box[0] + 40
    note_max_width = note_box[2] - note_x - 40
    for line_index, line in enumerate(note_lines):
        line_width = draw.textbbox((0, 0), line, font=note_font)[2]
        if line_width > note_max_width:
            raise ValueError("The configuration note exceeds its box.")
        draw.text((note_x, note_first_y + line_index * note_line_h), line, font=note_font, fill="#3B4650")
        drawn_line_widths[f"note_line_{line_index + 1}"] = line_width

    image.save(path, format="PNG", optimize=True)
    return width, height, drawn_line_widths


def paragraph_text(p) -> str:
    return "".join(t.text or "" for t in p.iter(W + "t"))


def patch_sequence_fields(document_root) -> tuple[list[int], list[int]]:
    old_figures: list[int] = []
    old_tables: list[int] = []
    counters = {"Hình": 0, "Bảng": 0}
    paragraphs = document_root.xpath(".//w:body//w:p", namespaces=NS)
    for p in paragraphs:
        nodes = list(p.iter())
        for index, node in enumerate(nodes):
            if node.tag != W + "instrText" or not node.text:
                continue
            match = re.search(r"\bSEQ\s+(Hình|Bảng)\b", node.text)
            if not match:
                continue
            kind = match.group(1)
            separate_at = next(
                (j for j in range(index + 1, len(nodes)) if nodes[j].tag == W + "fldChar" and nodes[j].get(W + "fldCharType") == "separate"),
                None,
            )
            end_at = next(
                (j for j in range((separate_at or index) + 1, len(nodes)) if nodes[j].tag == W + "fldChar" and nodes[j].get(W + "fldCharType") == "end"),
                None,
            )
            if separate_at is None or end_at is None:
                raise ValueError(f"Incomplete SEQ field for {kind}")
            result_nodes = [n for n in nodes[separate_at + 1 : end_at] if n.tag == W + "t"]
            if not result_nodes or not (result_nodes[0].text or "").strip().isdigit():
                raise ValueError(f"Missing cached number for SEQ {kind}")
            old_value = int(result_nodes[0].text)
            if kind == "Hình":
                old_figures.append(old_value)
            else:
                old_tables.append(old_value)
            counters[kind] += 1
            result_nodes[0].text = str(counters[kind])
    return old_figures, old_tables


def update_list_prefix(p, new_number: int) -> None:
    prefix = re.compile(r"^(Hình\s+)\d+(\.)")
    for t in p.iter(W + "t"):
        value = t.text or ""
        if prefix.match(value):
            t.text = prefix.sub(lambda m: f"{m.group(1)}{new_number}{m.group(2)}", value, count=1)
            return
    raise ValueError(f"Could not locate figure-list label: {paragraph_text(p)!r}")


def main() -> None:
    if not REPORT.is_file():
        raise FileNotFoundError(REPORT)
    if REPORT == BACKUP or not REPORT.is_relative_to(ROOT):
        raise ValueError("Unexpected report path")
    QA.mkdir(parents=True, exist_ok=True)
    if BACKUP.exists():
        raise FileExistsError(f"Refusing to overwrite backup: {BACKUP}")

    original_hash = sha256(REPORT)
    original_size = REPORT.stat().st_size
    shutil.copy2(REPORT, BACKUP)
    if sha256(BACKUP) != original_hash:
        raise RuntimeError("The preservation copy does not match the current report")

    width, height, measured_widths = make_diagram(NEW_IMAGE)

    with zipfile.ZipFile(REPORT, "r") as source:
        if source.testzip() is not None:
            raise RuntimeError("Source DOCX archive is damaged")
        doc_root = etree.fromstring(source.read("word/document.xml"))
        rel_root = etree.fromstring(source.read("word/_rels/document.xml.rels"))
        settings_root = etree.fromstring(source.read("word/settings.xml"))
        rels = {}
        for rel in rel_root:
            if rel.get("Type", "").endswith("/image"):
                rels[rel.get("Id")] = rel.get("Target")

        image_refs = doc_root.xpath(".//a:blip/@r:embed", namespaces=NS)
        target_rels = [rid for rid in image_refs if rels.get(rid, "").replace("\\", "/").endswith("media/image4.png")]
        if len(target_rels) != 1:
            raise ValueError(f"Expected one drawing for image4.png; found {len(target_rels)}")
        image_rid = target_rels[0]
        blips = doc_root.xpath(f".//a:blip[@r:embed='{image_rid}']", namespaces=NS)
        if len(blips) != 1:
            raise ValueError(f"Expected one use of the target drawing; found {len(blips)}")
        drawing = blips[0]
        while drawing is not None and drawing.tag not in (WP + "inline", WP + "anchor"):
            drawing = drawing.getparent()
        if drawing is None:
            raise ValueError("Could not find the target drawing extent")
        extent = drawing.find(WP + "extent")
        if extent is None:
            raise ValueError("Target drawing has no extent")
        cx = int(extent.get("cx"))
        cy = round(cx * height / width)
        extent.set("cx", str(cx))
        extent.set("cy", str(cy))
        for inner_extent in drawing.iter(A + "ext"):
            inner_extent.set("cx", str(cx))
            inner_extent.set("cy", str(cy))

        old_figures, old_tables = patch_sequence_fields(doc_root)
        if len(old_figures) != 34 or len(old_tables) != 27:
            raise ValueError(f"Unexpected caption totals: {len(old_figures)} figures, {len(old_tables)} tables")
        if len(set(old_figures)) != len(old_figures) or sorted(old_figures) != list(range(1, 21)) + list(range(23, 24)) + list(range(25, 38)):
            raise ValueError(f"Unexpected current figure sequence: {old_figures}")
        if old_tables != list(range(1, 28)):
            raise ValueError(f"Table numbers are not already continuous: {old_tables}")
        figure_map = {old: new for new, old in enumerate(old_figures, start=1)}

        body = doc_root.find("w:body", namespaces=NS)
        children = list(body)
        heading_start = next((i for i, child in enumerate(children) if child.tag == W + "p" and paragraph_text(child).strip() == "DANH MỤC HÌNH"), None)
        heading_end = next((i for i, child in enumerate(children) if child.tag == W + "p" and paragraph_text(child).strip() == "DANH MỤC BẢNG BIỂU"), None)
        if heading_start is None or heading_end is None or heading_end <= heading_start:
            raise ValueError("Could not locate the figure and table lists")

        figure_entries = []
        removed_entries = []
        for child in children[heading_start + 1 : heading_end]:
            if child.tag != W + "p":
                continue
            text = paragraph_text(child)
            match = re.match(r"^Hình\s+(\d+)\.", text)
            if not match:
                continue
            old_number = int(match.group(1))
            if old_number not in figure_map:
                body.remove(child)
                removed_entries.append(old_number)
                continue
            update_list_prefix(child, figure_map[old_number])
            figure_entries.append(figure_map[old_number])
        if removed_entries != [21, 22, 24]:
            raise ValueError(f"Unexpected stale figure-list entries removed: {removed_entries}")
        if figure_entries != list(range(1, 35)):
            raise ValueError(f"Figure list did not become continuous: {figure_entries}")

        table_entries = []
        children = list(body)
        table_heading = next((i for i, child in enumerate(children) if child.tag == W + "p" and paragraph_text(child).strip() == "DANH MỤC BẢNG BIỂU"), None)
        if table_heading is not None:
            for child in children[table_heading + 1 :]:
                if child.tag != W + "p":
                    continue
                match = re.match(r"^Bảng\s+(\d+)\.", paragraph_text(child))
                if match:
                    table_entries.append(int(match.group(1)))
                elif table_entries:
                    break
        if table_entries != list(range(1, 28)):
            raise ValueError(f"Table list is not continuous: {table_entries}")

        update_fields = settings_root.find("w:updateFields", namespaces=NS)
        if update_fields is None:
            update_fields = etree.SubElement(settings_root, W + "updateFields")
        update_fields.set(W + "val", "true")

        new_parts = {
            "word/document.xml": etree.tostring(doc_root, xml_declaration=True, encoding="UTF-8", standalone=True),
            "word/settings.xml": etree.tostring(settings_root, xml_declaration=True, encoding="UTF-8", standalone=True),
            rels[image_rid].replace("\\", "/"): NEW_IMAGE.read_bytes(),
        }
        if "../media/" in next(iter([rels[image_rid]])):
            raise ValueError("Unexpected relative media target")
        media_part = "word/" + rels[image_rid].replace("\\", "/")
        if media_part not in source.namelist():
            raise ValueError(f"Image media part not found: {media_part}")
        new_parts.pop(rels[image_rid].replace("\\", "/"), None)
        new_parts[media_part] = NEW_IMAGE.read_bytes()

        with zipfile.ZipFile(TEMP_DOCX, "w", compression=zipfile.ZIP_DEFLATED) as target:
            for item in source.infolist():
                target.writestr(item, new_parts.get(item.filename, source.read(item.filename)))

    with zipfile.ZipFile(TEMP_DOCX, "r") as check:
        if check.testzip() is not None:
            raise RuntimeError("Rewritten DOCX archive failed its CRC check")
        checked_doc = etree.fromstring(check.read("word/document.xml"))
        check_settings = etree.fromstring(check.read("word/settings.xml"))
        cached = {"Hình": [], "Bảng": []}
        for p in checked_doc.xpath(".//w:body//w:p", namespaces=NS):
            nodes = list(p.iter())
            for idx, node in enumerate(nodes):
                if node.tag != W + "instrText" or not node.text:
                    continue
                match = re.search(r"\bSEQ\s+(Hình|Bảng)\b", node.text)
                if not match:
                    continue
                sep = next(j for j in range(idx + 1, len(nodes)) if nodes[j].tag == W + "fldChar" and nodes[j].get(W + "fldCharType") == "separate")
                end = next(j for j in range(sep + 1, len(nodes)) if nodes[j].tag == W + "fldChar" and nodes[j].get(W + "fldCharType") == "end")
                result = next(n for n in nodes[sep + 1 : end] if n.tag == W + "t")
                cached[match.group(1)].append(int(result.text))
        if cached["Hình"] != list(range(1, 35)) or cached["Bảng"] != list(range(1, 28)):
            raise RuntimeError(f"Cached caption numbering failed verification: {cached}")
        if check_settings.find("w:updateFields", namespaces=NS).get(W + "val") != "true":
            raise RuntimeError("Word field-refresh setting was not saved")

    os.replace(TEMP_DOCX, REPORT)
    print(json.dumps({
        "report": str(REPORT),
        "backup": str(BACKUP),
        "original_sha256": original_hash,
        "original_size": original_size,
        "final_sha256": sha256(REPORT),
        "final_size": REPORT.stat().st_size,
        "figure_captions": 34,
        "table_captions": 27,
        "figure_list_entries": 34,
        "table_list_entries": 27,
        "removed_stale_figure_list_numbers": removed_entries,
        "image_dimensions": [width, height],
        "updated_extent_emu": [cx, cy],
        "measured_text_widths_px": measured_widths,
        "fields_set_to_update_on_open": True,
    }, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
