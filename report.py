from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter


BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "reports"
HISTORY_DIR = REPORT_DIR / "history"


HEADERS = [
    "Run time",
    "Change",
    "Status",
    "Title",
    "Role",
    "URL",
    "Source",
    "HR / contact emails",
    "Application links",
    "Details"
]


def write_report(rows):

    REPORT_DIR.mkdir(exist_ok=True)
    HISTORY_DIR.mkdir(exist_ok=True)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Job opportunities"
    sheet.append(HEADERS)

    header_fill = PatternFill(
        "solid",
        fgColor="1F4E78"
    )

    for cell in sheet[1]:
        cell.font = Font(
            bold=True,
            color="FFFFFF"
        )
        cell.fill = header_fill

    for row in rows:
        sheet.append([
            row.get("run_time", ""),
            row.get("change", ""),
            row.get("status", ""),
            row.get("title", ""),
            row.get("role", ""),
            row.get("url", ""),
            row.get("source", ""),
            row.get("emails", ""),
            row.get("application_links", ""),
            row.get("details", "")
        ])

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    widths = [
        22,
        16,
        18,
        42,
        24,
        70,
        24,
        36,
        70,
        52
    ]

    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[
            get_column_letter(index)
        ].width = width

    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = cell.alignment.copy(
                vertical="top",
                wrap_text=True
            )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    current_path = REPORT_DIR / "job_report.xlsx"
    history_path = HISTORY_DIR / (
        f"job_report_{timestamp}.xlsx"
    )

    workbook.save(current_path)
    workbook.save(history_path)

    return current_path, history_path
