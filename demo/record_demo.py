"""Record the README demo: load the sample library, then search it by meaning.

    python demo/record_demo.py            # writes demo/vectordb-q-demo.mp4 and .gif

Starts the real server (in-memory, local embeddings, no API key), drives the
real web UI with Playwright, and converts the capture with ffmpeg. Needs
requirements-local.txt, playwright (with chromium) and ffmpeg.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
W, H = 1280, 760
QUERIES = ["how did she escape before the drones arrived?", "was the election rigged?"]


def start_server(port: int) -> subprocess.Popen:
    env = dict(os.environ, PERSISTENCE_ENABLED="false", EMBEDDING_PROVIDER="local")
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port),
                             "--log-level", "warning"], cwd=ROOT, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(200):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1)
            break
        except OSError:
            time.sleep(0.1)
    # Load the embedding model before recording so the clip has no cold start
    req = urllib.request.Request(f"http://127.0.0.1:{port}/api/v1/embed", data=b'{"texts": ["warm up"]}',
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=120)
    return proc


def search(page, query: str):
    box = page.locator("#search-query")
    box.fill("")
    box.type(query, delay=45)
    page.wait_for_timeout(300)
    page.locator("#search-form button[type=submit]").click()
    page.wait_for_selector("#search-results .result-item")
    page.wait_for_timeout(600)
    page.locator("#search-results").scroll_into_view_if_needed()
    page.wait_for_timeout(3200)


def record(port: int, workdir: Path) -> Path:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": W, "height": H},
                                      record_video_dir=str(workdir), record_video_size={"width": W, "height": H})
        page = context.new_page()
        page.goto(f"http://127.0.0.1:{port}/")
        page.wait_for_timeout(1200)

        page.click("[data-page=libraries]")
        page.wait_for_timeout(800)
        page.click("button[onclick='loadSampleData()']")
        page.wait_for_selector("#libraries-list >> text=Sample Story", timeout=120_000)
        page.wait_for_function("!document.getElementById('sample-data-progress')"
                               " || !document.getElementById('sample-data-progress').isConnected", timeout=120_000)
        page.wait_for_timeout(1500)

        page.click("[data-page=search]")
        page.wait_for_timeout(700)
        label = page.locator("#search-library option", has_text="Sample Story").first.inner_text()
        page.select_option("#search-library", label=label)
        page.wait_for_timeout(500)
        for query in QUERIES:
            page.evaluate("window.scrollTo(0, 0); document.querySelector('.content-area')?.scrollTo(0, 0)")
            search(page, query)

        video = page.video.path()
        context.close()
        browser.close()
    return Path(video)


def convert(raw: Path):
    mp4 = OUT / "vectordb-q-demo.mp4"
    gif = OUT / "vectordb-q-demo.gif"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "26", "-movflags", "+faststart", str(mp4)], check=True)
    palette = raw.with_suffix(".png")
    scale = "fps=7,scale=880:-1:flags=lanczos"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-vf", f"{scale},palettegen=stats_mode=diff",
                    str(palette)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-i", str(palette), "-lavfi",
                    f"{scale}[x];[x][1:v]paletteuse=dither=none:diff_mode=rectangle",
                    str(gif)], check=True)
    for path in (mp4, gif):
        print(f"{path.relative_to(ROOT)}  {path.stat().st_size / 1024:.0f} KB")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8811)
    args = parser.parse_args()
    server = start_server(args.port)
    workdir = Path(tempfile.mkdtemp(prefix="vdbq-demo-"))
    try:
        convert(record(args.port, workdir))
    finally:
        server.terminate()
        server.wait(timeout=10)
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
