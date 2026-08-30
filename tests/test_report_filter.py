import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from openpyxl import Workbook

from report import get_applied_urls, write_report


class AppliedStatusExcelTests(unittest.TestCase):
    def test_get_applied_urls_reads_manual_applied_status(self):
        with TemporaryDirectory() as tmpdir:
            report_dir = Path(tmpdir) / "reports"
            report_dir.mkdir()

            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Job opportunities"
            sheet.append([
                "Run time",
                "Change",
                "Status",
                "Title",
                "Role",
                "URL",
                "Source",
                "HR / contact emails",
                "Application links",
                "Details",
                "Applied?",
            ])
            sheet.append([
                "2024-01-01T10:00:00",
                "New opportunity",
                "Found",
                "Example Job",
                "Engineer",
                "https://example.com/applied",
                "LinkedIn",
                "",
                "",
                "",
                "Applied",
            ])
            sheet.append([
                "2024-01-01T10:05:00",
                "New opportunity",
                "Found",
                "Another Job",
                "Analyst",
                "https://example.com/pending",
                "LinkedIn",
                "",
                "",
                "",
                "",
            ])

            workbook.save(report_dir / "job_report.xlsx")

            self.assertEqual(
                get_applied_urls(report_dir),
                {"https://example.com/applied"},
            )

    def test_write_report_includes_applied_column(self):
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            report_file, _ = write_report(
                [
                    {
                        "run_time": "2024-01-01T10:00:00",
                        "change": "New opportunity",
                        "status": "Found",
                        "title": "Example Job",
                        "role": "Engineer",
                        "url": "https://example.com/applied",
                        "source": "LinkedIn",
                        "emails": "",
                        "application_links": "",
                        "details": "",
                        "applied_status": "Applied",
                    }
                ],
                base_dir=output_dir,
            )

            self.assertTrue(report_file.exists())
            self.assertEqual(
                report_file.parent.name,
                "reports",
            )


if __name__ == "__main__":
    unittest.main()
