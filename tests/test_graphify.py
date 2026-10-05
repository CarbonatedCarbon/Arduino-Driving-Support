#!/usr/bin/env python3
"""
Graphify Knowledge Graph & HTML Visualizer Automated Test
=========================================================
Tests:
1. Knowledge graph generation (graphify-out/graph.json)
2. Interactive HTML export (graphify-out/graph.html)
3. Opening the HTML visualization page in the system browser
"""

import os
import sys
import json
import shutil
import subprocess
import webbrowser
from pathlib import Path
import pytest

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

GRAPHIFY_OUT = ROOT_DIR / "graphify-out"
GRAPH_JSON = GRAPHIFY_OUT / "graph.json"
GRAPH_HTML = GRAPHIFY_OUT / "graph.html"


def run_graphify_cli(*args) -> subprocess.CompletedProcess:
    """Run graphify CLI with fallback to python module."""
    cmd = ["graphify", *args]
    if shutil.which("graphify") is None:
        cmd = [sys.executable, "-m", "graphify", *args]

    return subprocess.run(
        cmd,
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=False,
    )


def test_graphify_graph_generation():
    """Verify that graphify builds graph.json with valid nodes and edges."""
    GRAPHIFY_OUT.mkdir(parents=True, exist_ok=True)

    # If graph.json does not exist or is empty, run code extraction
    if not GRAPH_JSON.exists() or GRAPH_JSON.stat().st_size == 0:
        res = run_graphify_cli(".", "--code-only")
        assert res.returncode == 0, f"graphify extraction failed: {res.stderr or res.stdout}"

    assert GRAPH_JSON.exists(), f"Expected {GRAPH_JSON} to exist"
    assert GRAPH_JSON.stat().st_size > 0, "graph.json is empty"

    with open(GRAPH_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    edges = data.get("links") or data.get("edges")
    assert edges is not None, "graph.json missing 'links' or 'edges'"
    assert len(data["nodes"]) > 0, "Graph has 0 nodes"
    assert len(edges) > 0, "Graph has 0 edges/links"


def test_graphify_html_generation():
    """Verify that graphify exports interactive graph.html."""
    GRAPHIFY_OUT.mkdir(parents=True, exist_ok=True)

    # Ensure HTML is exported
    res = run_graphify_cli("export", "html")
    assert res.returncode == 0, f"graphify export html failed: {res.stderr or res.stdout}"

    assert GRAPH_HTML.exists(), f"Expected {GRAPH_HTML} to exist"
    assert GRAPH_HTML.stat().st_size > 1000, "graph.html appears truncated or empty"

    content = GRAPH_HTML.read_text(encoding="utf-8", errors="ignore")
    assert "<html" in content.lower(), "graph.html missing <html> tag"


def test_open_graphify_html():
    """Verify HTML page path and launch in default system browser."""
    assert GRAPH_HTML.exists(), "Cannot open graph.html: file does not exist"

    file_uri = GRAPH_HTML.resolve().as_uri()
    try:
        opened = webbrowser.open(file_uri)
    except Exception:
        opened = False

    # Skip if running inside a headless container or CI without GUI display
    if not opened and sys.platform != "win32" and not os.getenv("DISPLAY"):
        pytest.skip("Headless environment: no graphical display detected to launch browser")

    print(f"\n[+] Opened interactive graph: {file_uri}")


def main():
    print("=" * 60)
    print("  Graphify Test: Building Graph & Opening HTML View")
    print("=" * 60)

    print("[*] 1. Verifying / Generating Knowledge Graph...")
    test_graphify_graph_generation()
    with open(GRAPH_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    edge_count = len(data.get("links") or data.get("edges") or [])
    print(f"    [PASS] graph.json: {len(data['nodes'])} nodes, {edge_count} edges")

    print("[*] 2. Verifying / Exporting Interactive HTML...")
    test_graphify_html_generation()
    print(f"    [PASS] graph.html generated ({GRAPH_HTML.stat().st_size:,} bytes)")

    print("[*] 3. Opening graph.html in default web browser...")
    file_uri = GRAPH_HTML.resolve().as_uri()
    webbrowser.open(file_uri)
    print(f"    [PASS] Launched browser for: {file_uri}")
    print("=" * 60)


if __name__ == "__main__":
    main()
