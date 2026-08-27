"""PDF rendering for the MO§ES™ Enterprise Pilot sample customer report.

Converts the markdown sample report (§16.9) to a polished PDF using
markdown-it-py (for markdown→HTML) and WeasyPrint (for HTML→PDF).

Usage:
    from reporting.pdf import render_sample_report_pdf
    render_sample_report_pdf(output_path="sample_customer_report.pdf")
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

# ── CSS for the polished PDF ─────────────────────────────────────────────

_REPORT_CSS = """
@page {
    size: A4;
    margin: 2cm 2.5cm;
    @bottom-center {
        content: "MO§ES™ Enterprise Pilot — Synthetic Demonstration Report";
        font-size: 8pt;
        color: #888;
    }
    @bottom-right {
        content: counter(page) " / " counter(pages);
        font-size: 8pt;
        color: #888;
    }
}

body {
    font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.5;
    color: #1a1a1a;
    max-width: 100%;
}

h1 {
    font-size: 20pt;
    color: #1a3a5c;
    border-bottom: 3px solid #1a3a5c;
    padding-bottom: 8px;
    margin-top: 30px;
}

h2 {
    font-size: 14pt;
    color: #1a3a5c;
    border-bottom: 1px solid #ccc;
    padding-bottom: 4px;
    margin-top: 24px;
    page-break-after: avoid;
}

h3 {
    font-size: 12pt;
    color: #2c5282;
    margin-top: 18px;
    page-break-after: avoid;
}

h4 {
    font-size: 11pt;
    color: #4a5568;
    margin-top: 14px;
    page-break-after: avoid;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 9pt;
    page-break-inside: avoid;
}

th {
    background-color: #1a3a5c;
    color: white;
    padding: 6px 10px;
    text-align: left;
    font-weight: 600;
}

td {
    padding: 5px 10px;
    border: 1px solid #ddd;
}

tr:nth-child(even) {
    background-color: #f7f9fc;
}

code {
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 9pt;
    background-color: #f0f0f0;
    padding: 1px 4px;
    border-radius: 3px;
}

pre {
    background-color: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 10px;
    overflow-x: auto;
    font-size: 8pt;
    page-break-inside: avoid;
}

pre code {
    background: none;
    padding: 0;
}

blockquote {
    border-left: 4px solid #1a3a5c;
    margin: 12px 0;
    padding: 8px 16px;
    background-color: #f0f4f8;
    color: #2c5282;
}

strong {
    color: #1a3a5c;
}

hr {
    border: none;
    border-top: 1px solid #ccc;
    margin: 20px 0;
}

/* Title block */
.title-block {
    text-align: center;
    margin-bottom: 30px;
    padding: 20px;
    background: linear-gradient(135deg, #1a3a5c 0%, #2c5282 100%);
    color: white;
    border-radius: 8px;
}

.title-block h1 {
    color: white;
    border: none;
    margin: 0;
}

.title-block .subtitle {
    font-size: 12pt;
    margin-top: 8px;
    opacity: 0.9;
}

/* Finding callout */
.finding {
    border-left: 4px solid #e65100;
    background-color: #fff3e0;
    padding: 10px 16px;
    margin: 12px 0;
    border-radius: 0 4px 4px 0;
}

.finding h3 {
    color: #e65100;
    margin-top: 0;
}

/* Evidence grade badge */
.evidence-grade {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 8pt;
    font-weight: 600;
    color: white;
}

.grade-controlled { background-color: #2e7d32; }
.grade-complete { background-color: #1565c0; }
.grade-strong { background-color: #6a1b9a; }
.grade-partial { background-color: #e65100; }
.grade-activity { background-color: #f9a825; }
.grade-customer { background-color: #00838f; }
.grade-inferred { background-color: #c62828; }
.grade-insufficient { background-color: #757575; }
"""

_TITLE_HTML = """
<div class="title-block">
  <h1>MO§ES™ 30-Day Pilot Readout</h1>
  <div class="subtitle">Synthetic Demonstration Report — Acme AI-Enabled Software Company</div>
  <div class="subtitle" style="font-size:10pt;margin-top:4px;">Pilot Window: 2026-07-01 to 2026-07-30 | Cohort: acme_50 (50 operators)</div>
</div>
"""


def _markdown_to_html(md_text: str) -> str:
    """Convert markdown to HTML using markdown-it-py."""
    from markdown_it import MarkdownIt

    md = MarkdownIt("commonmark", {"html": True, "breaks": False, "linkify": True})
    # Enable tables
    md.enable("table")
    html = md.render(md_text)
    return html


def render_sample_report_pdf(
    output_path: str = "sample_customer_report.pdf",
    source_md: Optional[str] = None,
) -> str:
    """Render the sample customer report as a polished PDF.

    Args:
        output_path: Where to write the PDF.
        source_md: Path to the markdown source. If None, uses the default
                   demo_data/graphics/g09_sample_customer_report.md.

    Returns:
        The absolute path to the generated PDF.
    """
    from weasyprint import HTML

    # Locate the source markdown
    if source_md is None:
        demo_data = Path(__file__).resolve().parents[1].parent / "demo_data"
        source_md = str(demo_data / "graphics" / "g09_sample_customer_report.md")

    md_path = Path(source_md)
    if not md_path.exists():
        raise FileNotFoundError(f"Sample report not found: {source_md}")

    md_text = md_path.read_text(encoding="utf-8")

    # Strip the top-level header (we replace it with the title block)
    lines = md_text.split("\n")
    # Remove leading # headers and horizontal rules until we hit content
    skip = True
    content_lines = []
    for line in lines:
        if skip and (line.startswith("#") or line.startswith("===") or line.strip() == ""):
            continue
        skip = False
        content_lines.append(line)
    md_text = "\n".join(content_lines)

    # Convert markdown → HTML
    body_html = _markdown_to_html(md_text)

    # Wrap in full HTML document with CSS
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>MO§ES™ 30-Day Pilot Readout</title>
<style>{_REPORT_CSS}</style>
</head>
<body>
{_TITLE_HTML}
{body_html}
</body>
</html>"""

    # Render to PDF
    output = Path(output_path).resolve()
    HTML(string=full_html).write_pdf(str(output))
    return str(output)


def render_markdown_pdf(
    md_text: str,
    output_path: str,
    title: str = "MO§ES™ Report",
) -> str:
    """Render arbitrary markdown text as a PDF.

    Args:
        md_text: The markdown content.
        output_path: Where to write the PDF.
        title: Document title for the header.

    Returns:
        The absolute path to the generated PDF.
    """
    from weasyprint import HTML

    body_html = _markdown_to_html(md_text)
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{_REPORT_CSS}</style>
</head>
<body>
{body_html}
</body>
</html>"""

    output = Path(output_path).resolve()
    HTML(string=full_html).write_pdf(str(output))
    return str(output)
