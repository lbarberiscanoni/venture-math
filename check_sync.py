#!/usr/bin/env python3
"""Report where venturemath.xyz has drifted from the local sources.

    python3 site/check_sync.py

Checks, without changing anything:
  1. Each session's data sheet: handouts/<sheet> vs site/sheets/ vs the live URL.
  2. Handouts in handouts/ that no session JSON links (built but unpublished).
  3. Flyers and index.html: local site copy vs the live URL.
  4. YouTube (@venturemathlectures, needs yt-dlp): lecture videos not linked from any
     session, and sessions whose title differs from their video's title.
Exit code 1 if anything is out of sync.
"""
import glob
import json
import os
import re
import subprocess
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
VM = os.path.dirname(ROOT)
BASE = os.environ.get("SITE_BASE_URL", "https://venturemath.xyz")
CHANNEL = "https://www.youtube.com/@venturemathlectures/videos"

problems = []


def read(path):
    with open(path, "rb") as f:
        return f.read()


def live(path):
    try:
        with urllib.request.urlopen(f"{BASE}/{path}", timeout=20) as r:
            return r.read()
    except Exception as e:  # noqa: BLE001
        return f"ERROR {e}".encode()


sessions = []
for f in sorted(glob.glob(os.path.join(VM, "fliers", "sessions", "[0-9]*.json"))):
    d = json.load(open(f))
    if d.get("slug", "").endswith("guest-slug"):
        continue
    sessions.append(d)

# 1 + 3: sheets, flyers, index
for d in sessions:
    slug, sheet = d["slug"], d.get("sheet")
    if sheet:
        src = os.path.join(VM, "handouts", sheet)
        dst = os.path.join(ROOT, "sheets", f"{slug}.html")
        if not os.path.exists(dst) or read(src) != read(dst):
            problems.append(f"{slug}: site/sheets copy is older than handouts/{sheet} (run site/build.py)")
        elif live(f"sheets/{slug}.html") != read(dst):
            problems.append(f"{slug}: data sheet not pushed (live differs from site/sheets)")
    fl = os.path.join(ROOT, "fliers", f"{slug}.html")
    if os.path.exists(fl) and live(f"fliers/{slug}.html") != read(fl):
        problems.append(f"{slug}: flyer not pushed (live differs from site/fliers)")
if live("") != read(os.path.join(ROOT, "index.html")):
    problems.append("index.html: schedule not pushed (live differs from site/index.html)")

# 2: handouts nobody links (ignore helper outputs like *-page.html)
linked = {d.get("sheet") for d in sessions}
for h in sorted(glob.glob(os.path.join(VM, "handouts", "*.html"))):
    name = os.path.basename(h)
    if name not in linked and not name.endswith("-page.html"):
        problems.append(f"handouts/{name}: built but no session JSON has \"sheet\": \"{name}\"")

# 4: YouTube
try:
    out = subprocess.run(
        ["yt-dlp", "--flat-playlist", "--print", "%(id)s\t%(title)s", CHANNEL],
        capture_output=True, text=True, timeout=120,
    ).stdout
    by_id = {}
    for d in sessions:
        m = re.search(r"v=([\w-]{11})", d.get("lecture_url", ""))
        if m:
            by_id[m.group(1)] = d
    for line in out.splitlines():
        vid, title = line.split("\t", 1)
        if not re.search(r"S\d+E\d+", title):
            continue  # clips and trailers, not full lectures
        d = by_id.get(vid)
        if not d:
            problems.append(f"YouTube {vid} \"{title}\": not linked from any session (add lecture_url)")
            continue
        yt = re.split(r"\s+with\s+|\s+\|\s+", title)[0].strip()
        if yt.lower() != d["session_title"].replace("&amp;", "&").lower():
            problems.append(f"{d['slug']}: site title \"{d['session_title']}\" vs YouTube \"{yt}\"")
except FileNotFoundError:
    problems.append("yt-dlp not installed: YouTube check skipped")

if problems:
    print("Out of sync:")
    for p in problems:
        print("  -", p)
    raise SystemExit(1)
print(f"In sync: {len(sessions)} sessions, sheets, flyers, schedule and YouTube titles match {BASE}.")
