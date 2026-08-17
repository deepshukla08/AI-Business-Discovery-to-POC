"""Rebuild Zippo's PDF and screenshot.

    pip install fpdf2 pillow
    python make_fixtures.py

Only needed if you edit current_process.md or the sheet rows below.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))  # samples/

from fixtures import markdown_to_pdf, table_screenshot  # noqa: E402

# Evidence in its own right: two driver columns — a workaround for reassignment that
# nobody records — and a status column where five people invented five spellings of
# "delivered". Neither fact appears in any transcript.
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


if __name__ == "__main__":
    produced = [
        markdown_to_pdf(HERE / "current_process.md", HERE.parent / "current_process.pdf"),
        table_screenshot(
            HERE.parent / "screenshot_dispatch_sheet.png",
            title="dispatch_master_MARCH.xlsx  -  Excel",
            subtitle="A1     fx     Order ID",
            toolbar="Sheet1    Ready",
            headers=HEADERS,
            widths=WIDTHS,
            rows=ROWS,
            accent="#217346",
            column_letters=True,
        ),
    ]
    for path in produced:
        print(f"wrote {path.name}  ({path.stat().st_size:,} bytes)")
