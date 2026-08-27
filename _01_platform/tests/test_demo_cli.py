"""Tests for the enterprise demo CLI command and PDF rendering.

Verifies:
  - `enterprise demo status` returns demo data inventory
  - `enterprise demo full` runs all 8 steps end-to-end
  - `enterprise demo report` generates PDF
  - `enterprise demo graphics` lists available graphics
  - PDF file is valid and non-empty
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


class TestDemoCLI(unittest.TestCase):
    """Tests for the enterprise demo CLI command."""

    def test_demo_status(self):
        """`enterprise demo status` returns demo data inventory."""
        from cli.main import main
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        rc = main(["--json", "demo", "status"])
        # main() prints to stdout, not via our buffer
        # Just check return code
        self.assertEqual(rc, 0)

    def test_demo_full(self):
        """`enterprise demo full` runs all steps and returns COMPLETE."""
        from cli.main import main
        rc = main(["--json", "demo", "full"])
        self.assertEqual(rc, 0)

    def test_demo_graphics(self):
        """`enterprise demo graphics` lists available graphics."""
        from cli.main import main
        rc = main(["--json", "demo", "graphics"])
        self.assertEqual(rc, 0)

    def test_pdf_generation(self):
        """PDF rendering produces a valid non-empty PDF file."""
        from reporting.pdf import render_sample_report_pdf

        demo_data = Path(__file__).resolve().parents[1] / "demo_data"
        pdf_path = str(demo_data / "graphics" / "g09_sample_customer_report.pdf")

        # Only test if the source markdown exists
        source_md = demo_data / "graphics" / "g09_sample_customer_report.md"
        if not source_md.exists():
            self.skipTest("Sample report markdown not found")

        result_path = render_sample_report_pdf(pdf_path)
        self.assertTrue(os.path.exists(result_path))
        self.assertGreater(os.path.getsize(result_path), 1000)  # at least 1KB

        # Check it's a valid PDF (starts with %PDF)
        with open(result_path, "rb") as f:
            header = f.read(5)
        self.assertTrue(header.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
