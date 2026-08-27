#!/usr/bin/env python3
"""TUI Audit Tool — headless layout audit for the Enterprise Pilot TUI.

Adapted from the SigRank tui-audit.mjs concept. Renders every screen at
multiple terminal sizes, checks for overflow, truncation, dead space,
alignment, color contrast (WCAG AA), and budget usage.

Usage:
    python tests/tui_audit.py              # full report
    python tests/tui_audit.py --ci         # exit non-zero on HIGH issues
    python tests/tui_audit.py --golden-save   # save golden frames
    python tests/tui_audit.py --golden-check  # compare against saved frames

The audit is headless — it captures rich console output without a TTY.
No stdin required, no interactive prompts.
"""
from __future__ import annotations

import io
import os
import sys
import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# ── Terminal sizes to test ──────────────────────────────────────────────────

SIZES = [
    {"name": "minimal", "cols": 80, "rows": 24, "label": "80×24 — small IDE / SSH"},
    {"name": "standard", "cols": 100, "rows": 30, "label": "100×30 — typical terminal"},
    {"name": "wide", "cols": 120, "rows": 40, "label": "120×40 — large / tmux split"},
    {"name": "ultrawide", "cols": 140, "rows": 50, "label": "140×50 — full-screen monitor"},
]

# ── ANSI stripping ──────────────────────────────────────────────────────────

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\][^\x07]*\x07|\x1b[=>]")

def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)

def visible_len(s: str) -> int:
    return len(strip_ansi(s))

def has_color(s: str) -> bool:
    return bool(re.search(r"\x1b\[", s))

# ── Issue tracking ──────────────────────────────────────────────────────────

@dataclass
class Issue:
    severity: str  # HIGH, MED, LOW
    category: str  # overflow, truncation, dead_space, alignment, contrast
    msg: str
    context: str = ""

@dataclass
class FrameResult:
    screen: str
    size: str
    cols: int
    rows: int
    lines: list[str] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    render_time_ms: float = 0.0
    used_rows: int = 0
    budget_rows: int = 0

# ── Frame analysis ──────────────────────────────────────────────────────────

def analyze_frame(result: FrameResult) -> None:
    """Check a rendered frame for overflow, truncation, dead space, alignment."""
    cols = result.cols
    rows = result.rows

    for i, line in enumerate(result.lines):
        vis = visible_len(line)

        # Overflow: line wider than terminal
        if vis > cols:
            result.issues.append(Issue(
                severity="HIGH",
                category="overflow",
                msg=f"line {i} is {vis} cols (>{cols} by {vis - cols})",
                context=strip_ansi(line)[:80],
            ))

        # Truncation: line ends with "…" or "..." suspiciously (rich truncates)
        stripped = strip_ansi(line).rstrip()
        if stripped.endswith("…") and vis < cols - 5:
            # Could be intentional ellipsis or rich truncation
            # Flag as MED if it looks like truncated data (mid-word)
            if not re.search(r"[.!?]…$", stripped):
                result.issues.append(Issue(
                    severity="MED",
                    category="truncation",
                    msg=f"line {i} ends with ellipsis at {vis} cols (may be truncated)",
                    context=stripped[:80],
                ))

    # Dead space: how many trailing empty rows
    used = sum(1 for l in result.lines if strip_ansi(l).strip())
    result.used_rows = used
    result.budget_rows = rows - 2  # reserve 2 for menu/prompt
    wasted = result.budget_rows - used
    if wasted > rows * 0.6:
        result.issues.append(Issue(
            severity="LOW",
            category="dead_space",
            msg=f"{used}/{result.budget_rows} rows used ({wasted} unused) — room for more content",
        ))

    # Alignment: check for ragged table borders within the same table block.
    # Only compare consecutive lines that have the same number of border positions
    # (i.e., rows within the same table). Skip lines that belong to different
    # tables, panels, or full-width borders.
    # Also skip markdown table content (plain text pipes inside a Panel).
    border_chars = set("┃│|")
    prev_positions: list[int] | None = None
    prev_line_idx = -1
    for i, line in enumerate(result.lines):
        stripped = strip_ansi(line)
        if not any(c in stripped for c in border_chars):
            prev_positions = None
            continue
        # Skip markdown table rows (they start with a panel border + "|")
        # These are text content, not rich Table borders — alignment is approximate
        if re.match(r"^[│┃]\s*\|", stripped):
            prev_positions = None
            continue
        positions = [j for j, c in enumerate(stripped) if c in border_chars]
        if not positions:
            prev_positions = None
            continue
        # Only compare to previous line if it had the same number of borders
        # (same table block) and was the immediately preceding line
        if (prev_positions is not None
                and len(positions) == len(prev_positions)
                and i == prev_line_idx + 1
                and positions != prev_positions):
            # Check if it's a real mismatch (positions differ by more than 1 col)
            diffs = [abs(a - b) for a, b in zip(positions, prev_positions)]
            if max(diffs) > 1:
                result.issues.append(Issue(
                    severity="MED",
                    category="alignment",
                    msg=f"table border mismatch at line {i} — columns don't line up",
                    context=f"expected {prev_positions[:5]}, got {positions[:5]}",
                ))
        prev_positions = positions
        prev_line_idx = i

# ── Color contrast (WCAG AA) ─────────────────────────────────────────────────
# rich uses named styles; we check the ANSI codes it emits against terminal bgs.

def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.replace("#", "")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

def relative_luminance(rgb: tuple[int, int, int]) -> float:
    def f(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

def contrast_ratio(fg: str, bg: str) -> float:
    fl = relative_luminance(hex_to_rgb(fg))
    bl = relative_luminance(hex_to_rgb(bg))
    return (max(fl, bl) + 0.05) / (min(fl, bl) + 0.05)

# Theme palettes — must match the 256-color values in src/tui/app.py
# Each theme is checked against its intended background only.

THEME_PALETTES = {
    "dark": {
        "bg": "#1d1f21",
        "colors": [
            {"name": "red",       "hex": "#ff5f5f", "usage": "errors, negative deltas"},
            {"name": "green",     "hex": "#5fd75f", "usage": "verified, positive, OK"},
            {"name": "yellow",    "hex": "#ffd700", "usage": "warnings, gates"},
            {"name": "blue",      "hex": "#87afd7", "usage": "borders, panels"},
            {"name": "cyan",      "hex": "#5fd7d7", "usage": "menu items, titles"},
            {"name": "magenta",   "hex": "#af87af", "usage": "highlights"},
            {"name": "bold_red",  "hex": "#ff5f5f", "usage": "bold errors"},
            {"name": "bold_cyan", "hex": "#5fd7d7", "usage": "bold menu items"},
            {"name": "dim",       "hex": "#767676", "usage": "secondary/labels"},
        ],
    },
    "light": {
        "bg": "#ffffff",
        "colors": [
            {"name": "red",       "hex": "#af0000", "usage": "errors, negative deltas"},
            {"name": "green",     "hex": "#008700", "usage": "verified, positive, OK"},
            {"name": "yellow",    "hex": "#af5f00", "usage": "warnings, gates"},
            {"name": "blue",      "hex": "#0000af", "usage": "borders, panels"},
            {"name": "cyan",      "hex": "#005f87", "usage": "menu items, titles"},
            {"name": "magenta",   "hex": "#870087", "usage": "highlights"},
            {"name": "bold_red",  "hex": "#af0000", "usage": "bold errors"},
            {"name": "bold_cyan", "hex": "#005f87", "usage": "bold menu items"},
            {"name": "dim",       "hex": "#767676", "usage": "secondary/labels"},
        ],
    },
}

def check_color_contrast() -> tuple[list[str], list[Issue]]:
    lines = []
    issues = []
    AA_NORMAL = 4.5
    AA_LARGE = 3.0

    for theme_name, palette in THEME_PALETTES.items():
        bg = palette["bg"]
        lines.append(f"  ── {theme_name} theme (bg: {bg}) ──")
        lines.append("  color          hex       ratio   threshold  usage")
        lines.append("  ─────────────  ────────  ──────  ─────────  ──────────────────────")

        for color in palette["colors"]:
            ratio = contrast_ratio(color["hex"], bg)
            is_dim = color["name"] == "dim"
            threshold = AA_LARGE if is_dim else AA_NORMAL
            passed = ratio >= threshold

            flag = "✓" if passed else "✗"
            lines.append(
                f"  {color['name'].ljust(14)}  {color['hex']}  {ratio:.1f} {flag}  "
                f"{threshold}:1".ljust(11) + f"  {color['usage']}"
            )

            if not passed:
                issues.append(Issue("LOW", "contrast",
                    f"{color['name']} fails WCAG AA on {theme_name} bg "
                    f"({ratio:.1f}:{threshold} needed) — {color['usage']}"))
        lines.append("")

    lines.append(f"  Threshold: {AA_NORMAL}:1 (normal text) · {AA_LARGE}:1 (dim/large text)")
    if not issues:
        lines.append("  ✅ All colors pass WCAG AA on their intended backgrounds.")
    else:
        lines.append(f"  ⚠ {len(issues)} color(s) fail WCAG AA — see flags above.")

    return lines, issues

# ── Screen rendering ─────────────────────────────────────────────────────────

def render_screen(app, screen_name: str, cols: int, rows: int) -> tuple[list[str], float, Optional[str]]:
    """Render a single screen at a given terminal size. Returns (lines, time_ms, error)."""
    import time

    # Create a console with specific width, preserving the app's theme
    from rich.console import Console
    from tui.app import _THEMES
    buf = io.StringIO()
    console = Console(file=buf, width=cols, force_terminal=False, color_system="auto",
                      theme=_THEMES.get(app.theme_name))
    app.console = console

    screen_map = {
        "Pilot": lambda: app.screen_pilot(),
        "Cohort": lambda: app.screen_cohort(),
        "Operator": lambda: app.screen_operator(),
        "Divergence": lambda: app.screen_divergence(),
        "Diagnose": lambda: app.screen_diagnose(),
        "Workflow": lambda: app.screen_workflow(),
        "Interventions": lambda: app.screen_interventions(),
        "Verify": lambda: app.screen_verify(),
        "DataQuality": lambda: app.screen_data_quality(),
        "Gates": lambda: app.screen_gates(),
        "Export": lambda: app.screen_export(),
    }

    handler = screen_map.get(screen_name)
    if not handler:
        return [], 0.0, f"Unknown screen: {screen_name}"

    # For screens that need input, provide defaults via stdin.
    # Export needs: format (md), target (pilot), and possibly operator ID.
    # Some screens need operator ID (Operator, Diagnose).
    # Provide enough lines for any screen.
    old_stdin = sys.stdin
    old_stdout = sys.stdout
    sys.stdin = io.StringIO("op_031\nmd\npilot\n\n\n\n")
    # Suppress prompt text from appearing in audit output
    sys.stdout = io.StringIO()

    try:
        start = time.perf_counter()
        handler()
        elapsed = (time.perf_counter() - start) * 1000
        output = buf.getvalue()
        lines = output.split("\n")
        # Remove trailing empty line from split
        if lines and not lines[-1].strip():
            lines.pop()
        return lines, elapsed, None
    except Exception as e:
        return [], 0.0, str(e)
    finally:
        sys.stdin = old_stdin
        sys.stdout = old_stdout

# ── Golden frames ────────────────────────────────────────────────────────────

GOLDEN_DIR = Path(__file__).resolve().parents[1] / ".tui-golden"

def save_golden(frames: dict[str, list[str]]) -> None:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    for name, lines in frames.items():
        path = GOLDEN_DIR / f"{name}.txt"
        path.write_text("\n".join(lines) + "\n")
    print(f"  Saved {len(frames)} golden frames to {GOLDEN_DIR}/")

def check_golden(frames: dict[str, list[str]]) -> list[Issue]:
    issues = []
    if not GOLDEN_DIR.exists():
        issues.append(Issue("LOW", "golden", "No golden frames directory — run --golden-save first"))
        return issues
    for name, lines in frames.items():
        path = GOLDEN_DIR / f"{name}.txt"
        if not path.exists():
            issues.append(Issue("MED", "golden", f"Golden frame missing: {name}.txt"))
            continue
        saved = path.read_text().split("\n")
        if saved and not saved[-1].strip():
            saved.pop()
        if saved != lines:
            issues.append(Issue("HIGH", "golden",
                f"Golden frame mismatch: {name} — render output changed"))
    return issues

# ── Per-screen grading ───────────────────────────────────────────────────────

def grade_screen(results: list[FrameResult]) -> tuple[str, int]:
    """Grade a screen across all sizes. Returns (letter_grade, score)."""
    total_issues = sum(len(r.issues) for r in results)
    high_count = sum(1 for r in results for i in r.issues if i.severity == "HIGH")
    med_count = sum(1 for r in results for i in r.issues if i.severity == "MED")

    if high_count > 0:
        return "F", 50 + max(0, 20 - high_count * 5)
    if med_count > 6:
        return "C", 75
    if med_count > 3:
        return "B", 85
    if total_issues > 5:
        return "B", 88
    return "A", 95

# ── Main audit runner ────────────────────────────────────────────────────────

SCREENS = [
    "Pilot", "Cohort", "Operator", "Divergence", "Diagnose",
    "Workflow", "Interventions", "Verify", "DataQuality",
    "Gates", "Export",
]

def run_audit(args) -> int:
    from tui import TuiApp

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  Enterprise TUI Audit — every screen × every terminal size  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    app = TuiApp()
    all_results: list[FrameResult] = []
    golden_frames: dict[str, list[str]] = {}

    # ── Render every screen × every size ──
    for size in SIZES:
        print(f"── {size['label']} ──")
        for screen_name in SCREENS:
            lines, elapsed, error = render_screen(app, screen_name, size["cols"], size["rows"])
            if error:
                print(f"  {screen_name:15s}  RENDER FAILED: {error[:60]}")
                result = FrameResult(
                    screen=screen_name, size=size["name"],
                    cols=size["cols"], rows=size["rows"],
                    issues=[Issue("HIGH", "render", f"render failed: {error}")]
                )
            else:
                result = FrameResult(
                    screen=screen_name, size=size["name"],
                    cols=size["cols"], rows=size["rows"],
                    lines=lines, render_time_ms=elapsed,
                )
                analyze_frame(result)
                # Save golden frame for standard size only
                if size["name"] == "standard":
                    golden_frames[f"{screen_name}_{size['name']}"] = lines

            all_results.append(result)

            high = sum(1 for i in result.issues if i.severity == "HIGH")
            med = sum(1 for i in result.issues if i.severity == "MED")
            low = sum(1 for i in result.issues if i.severity == "LOW")
            status = "✅" if high == 0 else "❌"
            print(f"  {screen_name:15s}  {len(result.lines):3d} lines  {result.used_rows:2d}/{result.budget_rows} budget  "
                  f"{high}H {med}M {low}L  {result.render_time_ms:.0f}ms  {status}")
        print()

    # ── Golden frames ──
    if args.golden_save:
        print("── Saving golden frames ──")
        save_golden(golden_frames)
        print()
    elif args.golden_check:
        print("── Golden frame check ──")
        golden_issues = check_golden(golden_frames)
        for issue in golden_issues:
            print(f"  [{issue.severity}] {issue.category}: {issue.msg}")
        if not golden_issues:
            print("  ✅ All golden frames match.")
        print()

    # ── Per-screen grades ──
    print("── Per-screen grades ──────────────────────────────────────────────────")
    total_high = 0
    total_med = 0
    total_low = 0
    for screen_name in SCREENS:
        screen_results = [r for r in all_results if r.screen == screen_name]
        grade, score = grade_screen(screen_results)
        high = sum(1 for r in screen_results for i in r.issues if i.severity == "HIGH")
        med = sum(1 for r in screen_results for i in r.issues if i.severity == "MED")
        low = sum(1 for r in screen_results for i in r.issues if i.severity == "LOW")
        total_high += high
        total_med += med
        total_low += low
        bar = "█" * (score // 10)
        print(f"  {screen_name:15s} {grade}  {bar} {score}/100  ({high}H {med}M {low}L)")
    print()

    # ── HIGH severity issues (verbatim) ──
    high_issues = [i for r in all_results for i in r.issues if i.severity == "HIGH"]
    if high_issues:
        print("── HIGH severity (must fix) ──────────────────────────────────────────")
        for r in all_results:
            for issue in r.issues:
                if issue.severity == "HIGH":
                    print(f"  [{issue.category}] {r.screen} @ {r.size} ({r.cols}×{r.rows})")
                    print(f"    {issue.msg}")
                    if issue.context:
                        print(f"    «{issue.context}»")
                    print()
    else:
        print("── HIGH severity ──")
        print("  ✅ No HIGH severity issues found.")
        print()

    # ── MED severity issues ──
    med_issues = [(r, i) for r in all_results for i in r.issues if i.severity == "MED"]
    if med_issues:
        print("── MED severity (should fix) ──────────────────────────────────────────")
        for r, issue in med_issues:
            print(f"  [{issue.category}] {r.screen} @ {r.size} ({r.cols}×{r.rows})")
            print(f"    {issue.msg}")
            if issue.context:
                print(f"    «{issue.context}»")
        print()

    # ── Color contrast ──
    print("── Color contrast (WCAG AA) ────────────────────────────────────────────")
    contrast_lines, contrast_issues = check_color_contrast()
    for line in contrast_lines:
        print(line)
    total_low += len(contrast_issues)
    print()

    # ── Summary ──
    print("── Summary ────────────────────────────────────────────────────────────")
    print(f"  Total issues: {total_high} HIGH / {total_med} MED / {total_low} LOW")
    print(f"  Screens tested: {len(SCREENS)} × {len(SIZES)} sizes = {len(SCREENS) * len(SIZES)} frames")
    if total_high == 0:
        print("  ✅ No HIGH issues — CI would pass.")
    else:
        print(f"  ❌ {total_high} HIGH issues — CI would fail.")
    print()

    # ── CI mode ──
    if args.ci:
        return 1 if total_high > 0 else 0
    return 0


def main():
    parser = argparse.ArgumentParser(description="Enterprise TUI Audit Tool")
    parser.add_argument("--ci", action="store_true", help="CI mode — exit non-zero on HIGH issues")
    parser.add_argument("--golden-save", action="store_true", help="Save golden frames")
    parser.add_argument("--golden-check", action="store_true", help="Check against saved golden frames")
    args = parser.parse_args()

    exit_code = run_audit(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
