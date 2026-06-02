import base64
import csv
import hashlib
import io
import json
import math
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"C:\Users\mayan\Desktop\3STSEM\ai\model")
NOTEBOOK = ROOT / "v6.6.ipynb"
TARGET = ROOT / "Figures"
PAPER_FIG_DIR = ROOT / "paper_figures" / "ieee_access_v66"

MIN_PLOT_WIDTH = 1800
TEXT_WIDTH_PX = 2600
TEXT_MARGIN = 70
TEXT_DPI = (350, 350)
TEXT_MAX_LINES = 64
TEXT_WRAP = 132


@dataclass
class ExportItem:
    order: float
    source: str
    heading: str
    label: str
    kind: str
    image: Image.Image | None = None
    text: str | None = None
    source_path: Path | None = None
    cell: int | None = None
    output_index: int | None = None


def slugify(text: str, max_len: int = 86) -> str:
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"^#+\s*", "", text.strip())
    text = re.sub(r"\bv6\.6\b", "v66", text, flags=re.I)
    text = re.sub(r"[^A-Za-z0-9]+", "_", text.lower()).strip("_")
    text = re.sub(r"_+", "_", text)
    return text[:max_len].strip("_") or "result"


def clean_heading(text: str) -> str:
    text = re.sub(r"^#+\s*", "", text.strip())
    text = re.sub(r"\s+", " ", text)
    return text or "Notebook result"


def load_font(size: int):
    candidates = [
        Path(r"C:\Windows\Fonts\consola.ttf"),
        Path(r"C:\Windows\Fonts\Consola.ttf"),
        Path(r"C:\Windows\Fonts\cour.ttf"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default(size=size)


FONT = load_font(30)
FONT_BOLD = load_font(34)
SMALL_FONT = load_font(22)


def normalize_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = "".join(value)
    return str(value).replace("\r\n", "\n").replace("\r", "\n").strip()


def is_meaningful_text(text: str) -> bool:
    if not text:
        return False
    stripped = text.strip()
    if stripped.startswith("<Figure size") and stripped.endswith(">"):
        return False
    if stripped.startswith("<matplotlib.") or stripped.startswith("[<matplotlib."):
        return False
    if "Saved paper figure" in stripped and len(stripped.splitlines()) < 4:
        return False
    return True


def image_from_png_data(data) -> Image.Image:
    raw = "".join(data) if isinstance(data, list) else str(data)
    img = Image.open(io.BytesIO(base64.b64decode(raw)))
    img.load()
    return img.convert("RGBA")


def upscale_if_needed(img: Image.Image, min_width: int = MIN_PLOT_WIDTH) -> Image.Image:
    w, h = img.size
    if w >= min_width:
        return img
    scale = min_width / max(w, 1)
    new_size = (int(round(w * scale)), int(round(h * scale)))
    return img.resize(new_size, Image.Resampling.LANCZOS)


def text_pages(text: str, title: str) -> list[Image.Image]:
    logical_lines = []
    for raw_line in text.splitlines():
        if raw_line.strip():
            logical_lines.extend(textwrap.wrap(raw_line, width=TEXT_WRAP, replace_whitespace=False) or [""])
        else:
            logical_lines.append("")
    if not logical_lines:
        logical_lines = ["(empty output)"]

    pages = []
    for page_no in range(0, len(logical_lines), TEXT_MAX_LINES):
        page_lines = logical_lines[page_no:page_no + TEXT_MAX_LINES]
        line_height = 39
        title_height = 78
        footer_height = 46
        height = TEXT_MARGIN * 2 + title_height + footer_height + max(1, len(page_lines)) * line_height
        img = Image.new("RGB", (TEXT_WIDTH_PX, height), "white")
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, TEXT_WIDTH_PX, 58], fill="#EAF4FF")
        draw.text((TEXT_MARGIN, 14), title[:150], font=FONT_BOLD, fill="#17202A")
        y = TEXT_MARGIN + 35
        for line in page_lines:
            draw.text((TEXT_MARGIN, y), line, font=FONT, fill="#17202A")
            y += line_height
        page_idx = page_no // TEXT_MAX_LINES + 1
        total_pages = math.ceil(len(logical_lines) / TEXT_MAX_LINES)
        draw.text(
            (TEXT_MARGIN, height - TEXT_MARGIN + 18),
            f"Notebook metric/text output page {page_idx} of {total_pages}",
            font=SMALL_FONT,
            fill="#4E5A65",
        )
        pages.append(img)
    return pages


def item_hash(item: ExportItem, page_text: str | None = None) -> str:
    if item.image is not None:
        buf = io.BytesIO()
        item.image.save(buf, format="PNG")
        return hashlib.sha256(buf.getvalue()).hexdigest()
    if item.source_path is not None:
        return hashlib.sha256(item.source_path.read_bytes()).hexdigest()
    return hashlib.sha256((page_text or item.text or "").encode("utf-8", errors="replace")).hexdigest()


def parse_markdown_headings(nb) -> dict[int, str]:
    current = "Notebook result"
    headings = {}
    for idx, cell in enumerate(nb["cells"], start=1):
        if cell.get("cell_type") == "markdown":
            lines = "".join(cell.get("source", [])).strip().splitlines()
            for line in lines:
                if line.strip().startswith("##"):
                    current = clean_heading(line)
                    break
        elif cell.get("cell_type") == "code":
            headings[idx] = current
    return headings


def notebook_items(nb) -> list[ExportItem]:
    headings = parse_markdown_headings(nb)
    items: list[ExportItem] = []
    for cell_idx, cell in enumerate(nb["cells"], start=1):
        if cell.get("cell_type") != "code":
            continue
        heading = headings.get(cell_idx, f"Cell {cell_idx}")
        outputs = cell.get("outputs", [])
        for out_idx, out in enumerate(outputs, start=1):
            data = out.get("data", {}) or {}
            base_order = cell_idx * 1000 + out_idx

            if "image/png" in data:
                # Final appendix figures are also saved at higher DPI in paper_figures.
                if cell_idx in (72, 74):
                    continue
                try:
                    img = image_from_png_data(data["image/png"])
                except Exception as exc:
                    text = f"Could not decode image output: {exc}"
                    items.append(ExportItem(base_order, "notebook-error", heading, "decode_error", "text", text=text, cell=cell_idx, output_index=out_idx))
                    continue
                items.append(ExportItem(base_order, "notebook-image", heading, f"{heading} plot {out_idx}", "image", image=img, cell=cell_idx, output_index=out_idx))

            pieces = []
            if "text/plain" in data:
                pieces.append(normalize_text(data["text/plain"]))
            if "text" in out:
                pieces.append(normalize_text(out["text"]))
            text = "\n".join(p for p in pieces if p).strip()
            if is_meaningful_text(text):
                # Cell 72/74 path listings are not metric evidence; the actual figures are copied below.
                if cell_idx in (72, 74) and "paper_figures" in text:
                    continue
                label = f"{heading} metrics output {out_idx}"
                items.append(ExportItem(base_order + 0.25, "notebook-text", heading, label, "text", text=text, cell=cell_idx, output_index=out_idx))
    return items


def paper_figure_items() -> list[ExportItem]:
    items: list[ExportItem] = []
    if not PAPER_FIG_DIR.exists():
        return items
    for path in sorted(PAPER_FIG_DIR.glob("*.png")):
        name = path.stem
        match = re.match(r"fig_a(\d+)_", name)
        if match:
            fig_no = int(match.group(1))
            cell_order = 72 if fig_no <= 12 else 74
            order = cell_order * 1000 + fig_no / 100.0
        else:
            fig_no = 999
            order = 74 * 1000 + fig_no
        heading = "IEEE Access paper figure appendix" if fig_no <= 12 else "Additional IEEE Access metrics and flowcharts"
        label = name
        items.append(ExportItem(order, "paper-figure", heading, label, "image-file", source_path=path))
    return items


def clear_previous_exports():
    TARGET.mkdir(parents=True, exist_ok=True)
    for path in TARGET.iterdir():
        if path.is_file() and (
            re.match(r"^\d{3}_", path.name)
            or path.name in {"_export_index.csv", "_duplicate_skips.csv", "_export_summary.txt"}
        ):
            path.unlink()


def save_item_image(img: Image.Image, dest: Path):
    img = img.convert("RGB")
    img.save(dest, format="PNG", dpi=TEXT_DPI, optimize=True)


def export_all():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    clear_previous_exports()

    items = notebook_items(nb) + paper_figure_items()
    items.sort(key=lambda x: x.order)

    seen_hashes: dict[str, str] = {}
    rows = []
    skipped = []
    serial = 1

    for item in items:
        base_slug = slugify(item.label)
        heading_slug = slugify(item.heading, max_len=48)
        if item.kind in {"image", "image-file"}:
            if item.source_path is not None:
                img = Image.open(item.source_path)
                img.load()
                img = img.convert("RGBA")
            else:
                img = item.image
            img = upscale_if_needed(img) if item.source != "paper-figure" else img
            tmp = ExportItem(item.order, item.source, item.heading, item.label, "image", image=img)
            digest = item_hash(tmp)
            if digest in seen_hashes:
                skipped.append({
                    "source": item.source,
                    "cell": item.cell or "",
                    "output_index": item.output_index or "",
                    "label": item.label,
                    "reason": f"exact duplicate of {seen_hashes[digest]}",
                })
                continue
            filename = f"{serial:03d}_{base_slug}.png"
            dest = TARGET / filename
            save_item_image(img, dest)
            seen_hashes[digest] = filename
            rows.append({
                "serial": serial,
                "file": filename,
                "kind": item.kind,
                "source": item.source,
                "cell": item.cell or "",
                "output_index": item.output_index or "",
                "heading": item.heading,
                "label": item.label,
                "width": img.size[0],
                "height": img.size[1],
            })
            serial += 1
        elif item.kind == "text":
            digest = item_hash(item)
            if digest in seen_hashes:
                skipped.append({
                    "source": item.source,
                    "cell": item.cell or "",
                    "output_index": item.output_index or "",
                    "label": item.label,
                    "reason": f"exact duplicate of {seen_hashes[digest]}",
                })
                continue
            pages = text_pages(item.text or "", item.label)
            for page_no, page in enumerate(pages, start=1):
                suffix = f"_part{page_no:02d}" if len(pages) > 1 else ""
                filename = f"{serial:03d}_{heading_slug}_{slugify(item.kind)}{suffix}.png"
                dest = TARGET / filename
                save_item_image(page, dest)
                rows.append({
                    "serial": serial,
                    "file": filename,
                    "kind": "text-as-image",
                    "source": item.source,
                    "cell": item.cell or "",
                    "output_index": item.output_index or "",
                    "heading": item.heading,
                    "label": item.label,
                    "width": page.size[0],
                    "height": page.size[1],
                })
                serial += 1
            seen_hashes[digest] = rows[-1]["file"]

    with (TARGET / "_export_index.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["serial", "file", "kind", "source", "cell", "output_index", "heading", "label", "width", "height"])
        writer.writeheader()
        writer.writerows(rows)

    with (TARGET / "_duplicate_skips.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["source", "cell", "output_index", "label", "reason"])
        writer.writeheader()
        writer.writerows(skipped)

    summary = [
        "v6.6 notebook figure/result export",
        f"Notebook: {NOTEBOOK}",
        f"Target: {TARGET}",
        f"Exported PNG files: {len(rows)}",
        f"Skipped exact duplicates: {len(skipped)}",
        "Notes:",
        "- Serial order follows notebook output order.",
        "- Final appendix embedded images are replaced by higher-resolution files from paper_figures/ieee_access_v66 when available.",
        "- Text and printed metric outputs are rendered as high-DPI PNG pages.",
        "- Existing non-numbered files in Figures were left untouched.",
    ]
    (TARGET / "_export_summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    return rows, skipped


if __name__ == "__main__":
    rows, skipped = export_all()
    print(f"Exported {len(rows)} PNG files to {TARGET}")
    print(f"Skipped {len(skipped)} exact duplicate outputs")
    print(f"Index: {TARGET / '_export_index.csv'}")
