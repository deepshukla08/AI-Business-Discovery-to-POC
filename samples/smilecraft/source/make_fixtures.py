"""Regenerate SmileCraft's binary sample inputs (PDF + screenshot) from source.

    pip install fpdf2 pillow
    python make_fixtures.py

Deliberately NOT in backend/requirements.txt — the app reads fixtures, it never makes them.
"""

from pathlib import Path

from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE.parent

# fpdf2's core fonts are latin-1 only; typographic characters would raise
LATIN1 = str.maketrans({"—": "-", "–": "-", "’": "'", "‘": "'", "“": '"', "”": '"', "…": "..."})


def build_pdf() -> Path:
    lines = (HERE / "patient_policy.md").read_text(encoding="utf-8").splitlines()

    pdf = FPDF()
    pdf.set_margins(20, 18, 20)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    def write(height: float, text: str, style: str = "", size: int = 10) -> None:
        # multi_cell leaves the cursor at the RIGHT margin by default, which gives the
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

    path = OUT / "patient_policy.pdf"
    pdf.output(str(path))
    return path


# The screenshot is evidence in its own right: slots double-booked against a policy that
# forbids it, a Confirmed column stuck on TBC, and one treatment written five ways.
HEADERS = ["Time", "Patient", "Phone", "Treatment", "Doctor", "Conf", "Notes"]
WIDTHS = [70, 175, 110, 165, 110, 60, 200]
ROWS = [
    ["09:00", "Anita Deshpande", "98220 41xxx", "RCT", "Dr. Meera", "TBC", ""],
    ["09:00", "Rohit Kale", "97640 88xxx", "check up", "Dr. Meera", "TBC", "squeezed in"],
    ["09:30", "Sameer Joshi", "", "Root canal", "Dr. Meera", "Y", ""],
    ["10:00", "", "", "", "", "", ""],
    ["10:15", "Priya Kulkarni", "99700 12xxx", "scaling", "Dr. Amit", "TBC", ""],
    ["10:15", "Vikram Rao", "", "SCP", "Dr. Amit", "TBC", "same slot ok?"],
    ["11:00", "Neha Patil", "98901 55xxx", "r.c.t sitting 2", "Dr. Meera", "TBC", ""],
    ["11:30", "Farida Shaikh", "", "crown fit", "Dr. Amit", "Y", "lab not recd??"],
    ["12:00", "Ganesh More", "88060 73xxx", "EXT", "Dr. Meera", "TBC", ""],
    ["12:30", "", "", "", "", "", "no show yday - call"],
    ["14:00", "Imran Shaikh", "", "R.C.T.", "Dr. Meera", "TBC", "Baner file?"],
    ["14:45", "Sunita Bhosale", "97300 21xxx", "ORT review", "Dr. Kiran (visiting)", "TBC", "is he coming?"],
    ["15:30", "Mahesh Gokhale", "", "filling", "Dr. Amit", "TBC", ""],
]


def font(size: int, bold: bool = False):
    for name in (("arialbd.ttf", "arial.ttf")[not bold], "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_screenshot() -> Path:
    left, top, row_h, gutter = 30, 104, 27, 30
    width = left + gutter + sum(WIDTHS) + 30
    height = top + row_h * (len(ROWS) + 1) + 50

    img = Image.new("RGB", (width, height), "#ffffff")
    d = ImageDraw.Draw(img)
    cell_font, head_font, chrome_font = font(13), font(13, bold=True), font(12)

    # application chrome, so a vision model reads this as a real screenshot
    d.rectangle([0, 0, width, 34], fill="#1f4e79")
    d.text((12, 9), "DentaSoft 7.2  -  Appointment Book", font=font(13, bold=True), fill="#ffffff")
    d.rectangle([0, 34, width, 96], fill="#eef2f6")
    d.text((12, 46), "Branch: Kothrud    Date: Mon 16 Sep 2024", font=font(13, bold=True), fill="#1f4e79")
    d.text((12, 70), "[ < Prev ]  [ Today ]  [ Next > ]        Chairs: 2        Print day list", font=chrome_font, fill="#44607a")

    for r, values in enumerate([HEADERS] + ROWS):
        y = top + r * row_h
        is_head = r == 0
        d.rectangle([left, y, left + gutter, y + row_h], fill="#eef2f6", outline="#c9d4de")

        x = left + gutter
        for value, w in zip(values, WIDTHS):
            d.rectangle(
                [x, y, x + w, y + row_h],
                fill="#eef2f6" if is_head else "#ffffff",
                outline="#c9d4de",
            )
            d.text((x + 7, y + 6), value, font=head_font if is_head else cell_font, fill="#152733")
            x += w

    path = OUT / "screenshot_appointment_book.png"
    img.save(path)
    return path


if __name__ == "__main__":
    for produced in (build_pdf(), build_screenshot()):
        print(f"wrote {produced.name}  ({produced.stat().st_size:,} bytes)")
