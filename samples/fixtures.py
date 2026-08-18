"""Shared machinery for building the binary sample inputs.

Each sample's `source/make_fixtures.py` supplies the content — a markdown document and a
table of rows — and calls into here for the rendering. Kept out of the backend entirely:
the app reads fixtures, it never makes them.

    pip install fpdf2 pillow
"""

from pathlib import Path

from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

# fpdf2's core fonts are latin-1 only; typographic characters would raise
LATIN1 = str.maketrans({"—": "-", "–": "-", "’": "'", "‘": "'", "“": '"', "”": '"', "…": "..."})


def markdown_to_pdf(source: Path, out: Path) -> Path:
    """A deliberately plain renderer — enough to make a document that looks like a real
    company policy and that pypdf can extract cleanly."""
    pdf = FPDF()
    pdf.set_margins(20, 18, 20)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    def write(height: float, text: str, style: str = "", size: int = 10) -> None:
        # multi_cell leaves the cursor at the RIGHT margin by default, which gives the
        # next full-width multi_cell zero space to work with. Always return to the left.
        pdf.set_font("Helvetica", style, size)
        pdf.multi_cell(0, height, text, new_x="LMARGIN", new_y="NEXT")

    for raw in source.read_text(encoding="utf-8").splitlines():
        line = raw.translate(LATIN1).rstrip()
        if line == "---":
            pdf.ln(3)
            y = pdf.get_y()
            pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
            pdf.ln(4)
        elif line.startswith("### "):
            pdf.ln(3)
            write(6, line[4:], "B", 11)
        elif line.startswith("## "):
            pdf.ln(4)
            write(7, line[3:], "B", 13)
        elif line.startswith("# "):
            write(9, line[2:], "B", 16)
        elif line.startswith("*") and line.endswith("*") and len(line) > 2:
            write(5, line.strip("*"), "I", 8)
        elif line:
            write(5, line)
        else:
            pdf.ln(2)

    pdf.output(str(out))
    return out


def font(size: int, bold: bool = False):
    for name in (("arialbd.ttf", "arial.ttf")[not bold], "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def table_screenshot(
    out: Path,
    *,
    title: str,
    subtitle: str,
    toolbar: str,
    headers: list[str],
    widths: list[int],
    rows: list[list[str]],
    accent: str,
    column_letters: bool = False,
) -> Path:
    """A screenshot of the tool a client actually runs their business on.

    The chrome matters: without a title bar and a toolbar a vision model reads this as a
    table of data rather than as evidence about a system someone uses every day.
    """
    left, top, row_h, gutter = 30, 104, 27, 32
    width = left + gutter + sum(widths) + 30
    height = top + row_h * (len(rows) + 1) + 50

    img = Image.new("RGB", (width, height), "#ffffff")
    d = ImageDraw.Draw(img)
    cell_font, head_font, chrome_font = font(13), font(13, bold=True), font(12)

    d.rectangle([0, 0, width, 34], fill=accent)
    d.text((12, 9), title, font=font(13, bold=True), fill="#ffffff")
    d.rectangle([0, 34, width, 96], fill="#eef2f6")
    d.text((12, 46), subtitle, font=font(13, bold=True), fill=accent)
    d.text((12, 70), toolbar, font=chrome_font, fill="#44607a")

    if column_letters:
        x = left + gutter
        for i, w in enumerate(widths):
            d.text((x + 8, top - 20), chr(65 + i), font=chrome_font, fill="#888888")
            x += w

    for r, values in enumerate([headers] + rows):
        y = top + r * row_h
        is_head = r == 0
        d.rectangle([left, y, left + gutter, y + row_h], fill="#eef2f6", outline="#c9d4de")
        if column_letters:
            d.text((left + 9, y + 6), str(r + 1), font=chrome_font, fill="#666666")

        x = left + gutter
        for value, w in zip(values, widths):
            d.rectangle(
                [x, y, x + w, y + row_h],
                fill="#eef2f6" if is_head else "#ffffff",
                outline="#c9d4de",
            )
            d.text((x + 7, y + 6), value, font=head_font if is_head else cell_font, fill="#152733")
            x += w

    img.save(out)
    return out
