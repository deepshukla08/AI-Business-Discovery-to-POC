"""Rebuild SmileCraft's PDF and screenshot.

    pip install fpdf2 pillow
    python make_fixtures.py

Only needed if you edit patient_policy.md or the appointment rows below.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))  # samples/

from fixtures import markdown_to_pdf, table_screenshot  # noqa: E402

# Evidence in its own right: 09:00 and 10:15 hold two patients each, against a policy that
# forbids double booking outright; Conf is stuck on TBC; a root canal is written four ways
# in one day; and six booked rows have no phone number, which quietly makes "just send
# reminders" impossible. None of it appears in any transcript.
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


if __name__ == "__main__":
    produced = [
        markdown_to_pdf(HERE / "patient_policy.md", HERE.parent / "patient_policy.pdf"),
        table_screenshot(
            HERE.parent / "screenshot_appointment_book.png",
            title="DentaSoft 7.2  -  Appointment Book",
            subtitle="Branch: Kothrud    Date: Mon 16 Sep 2024",
            toolbar="[ < Prev ]  [ Today ]  [ Next > ]        Chairs: 2        Print day list",
            headers=HEADERS,
            widths=WIDTHS,
            rows=ROWS,
            accent="#1f4e79",
        ),
    ]
    for path in produced:
        print(f"wrote {path.name}  ({path.stat().st_size:,} bytes)")
