"""Regenerate the binary sample inputs (PDF + screenshot) from source.

    pip install fpdf2 pillow
    python make_fixtures.py

Deliberately NOT in backend/requirements.txt — the app never generates fixtures, it only
reads them. Run this only if you edit current_process.md or the sheet rows below.
"""

from pathlib import Path

from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE.parent

# fpdf2's core fonts are latin-1 only; typographic characters would raise
LATIN1 = str.maketrans({"—": "-", "–": "-", "’": "'", "‘": "'", "“": '"', "”": '"', "…": "..."})


def build_pdf() -> Path:
    lines = (HERE / "current_process.md").read_text(encoding="utf-8").splitlines()

    pdf = FPDF()
    pdf.set_margins(20, 18, 20)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    def write(height: float, text: str, style: str = "", size: int = 10) -> None:
        # multi_cell defaults to leaving the cursor at the RIGHT margin, which gives the
        # next full-width multi_cell zero space. Always return to the left margin.
        pdf.set_font("Helvetica", style, size)
        pdf.multi_cell(0, height, text, new_x="LMARGIN", new_y="NEXT")

    for raw in lines:
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

    path = OUT / "current_process.pdf"
    pdf.output(str(path))
    return path


# The screenshot is evidence in its own right: two driver columns, and a status column
# where five people have invented five different spellings of "delivered".
HEADERS = ["Order ID", "Brand", "Area", "Address", "COD", "Driver", "Driver2", "Status", "Remarks"]
WIDTHS = [95, 85, 95, 250, 70, 90, 90, 100, 175]
ROWS = [
    ["BC-88412", "BlueCart", "Andheri E", "B-402 Sunrise CHS, Chakala", "0", "Suresh", "", "Delivered", ""],
    ["BC-88413", "BlueCart", "Powai", "Hiranandani, Rodas Enclave", "1,240", "Suresh", "", "delivered", ""],
    ["BC-88414", "BlueCart", "Chembur", "Flat 7, Sindhi Society", "0", "Ganesh", "Suresh", "done", "given to suresh"],
    ["HT-2201", "Hometown", "Bandra W", "Pali Naka, above cafe", "3,500", "Imran", "", "DONE", ""],
    ["HT-2202", "Hometown", "Bandra W", "Carter Rd - bldg name not given", "0", "Imran", "", "NA", "cust not picking"],
    ["BC-88415", "BlueCart", "Malad W", "Orlem, near church", "890", "Firoz", "", "delvered", ""],
    ["BC-88416", "BlueCart", "Malad W", "Evershine Nagar", "0", "Firoz", "Ganesh", "", "?? check with firoz"],
    ["HT-2203", "Hometown", "Kurla", "LBS Marg, opp depot", "2,100", "Ganesh", "", "Delivered", "cash pending"],
    ["BC-88417", "BlueCart", "Vashi", "Sector 17", "0", "", "", "", "no driver free"],
    ["BC-88418", "BlueCart", "Andheri W", "Lokhandwala, 3rd flr", "1,750", "Suresh", "", "Delivered", ""],
    ["HT-2204", "Hometown", "Ghatkopar", "Pant Nagar - flat no missing", "0", "Imran", "", "NA", "address problem"],
    ["BC-88419", "BlueCart", "Powai", "Galleria, shop 12", "560", "Firoz", "", "delivered", ""],
]


def font(size: int, bold: bool = False):
    for name in (("arialbd.ttf", "arial.ttf")[not bold], "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_screenshot() -> Path:
    left, top, row_h, gutter = 40, 96, 26, 34
    width = left + gutter + sum(WIDTHS) + 40
    height = top + row_h * (len(ROWS) + 1) + 60

    img = Image.new("RGB", (width, height), "#ffffff")
    d = ImageDraw.Draw(img)
    cell_font, head_font, chrome_font = font(13), font(13, bold=True), font(12)

    # spreadsheet chrome, so a vision model reads this as a real screenshot
    d.rectangle([0, 0, width, 58], fill="#217346")
    d.text((16, 20), "dispatch_master_MARCH.xlsx  -  Excel", font=font(14, bold=True), fill="#ffffff")
    d.rectangle([0, 58, width, 88], fill="#f3f2f1")
    d.text((16, 66), "A1     fx     Order ID", font=chrome_font, fill="#444444")

    x = left + gutter
    for header, w in zip(HEADERS, WIDTHS):
        d.text((x + 8, top - 22), chr(65 + HEADERS.index(header)), font=chrome_font, fill="#888888")
        x += w

    for r, values in enumerate([HEADERS] + ROWS):
        y = top + r * row_h
        is_head = r == 0
        d.rectangle([left, y, left + gutter, y + row_h], fill="#f3f2f1", outline="#d0cfcc")
        d.text((left + 10, y + 6), str(r + 1), font=chrome_font, fill="#666666")

        x = left + gutter
        for value, w in zip(values, WIDTHS):
            d.rectangle([x, y, x + w, y + row_h], fill="#f3f2f1" if is_head else "#ffffff", outline="#d0cfcc")
            d.text((x + 8, y + 6), value, font=head_font if is_head else cell_font, fill="#1b1a18")
            x += w

    path = OUT / "screenshot_dispatch_sheet.png"
    img.save(path)
    return path


if __name__ == "__main__":
    for produced in (build_pdf(), build_screenshot()):
        print(f"wrote {produced.name}  ({produced.stat().st_size:,} bytes)")
