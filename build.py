#!/usr/bin/env python3
"""Generate index.html from the session flyers.

`../fliers/sessions/*.json` is the source of truth for the schedule — it is what the
printed flyers are built from — so the public page is generated from the same data
rather than hand-maintained alongside it.

Sessions with no flyer are simply absent (there is no session 07 / Oct 14), and the
page shows dates rather than session numbers so the gap in the flyer numbering does
not surface as a hole in the schedule.
"""
import glob, html, json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
SESSIONS = os.path.join(ROOT, "..", "fliers", "sessions")
MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
          "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}


def txt(v):
    """Flyer fields carry markup and entities; the page needs plain text."""
    return html.unescape(re.sub(r"<[^>]+>", " ", str(v or ""))).replace(" ", " ").strip()


def parse_date(d):
    m = re.match(r"([A-Za-z]+)\s+(\d+)", d)
    return (MONTHS[m.group(1)[:3].lower()], int(m.group(2))) if m else (99, 99)


def parse_time(t):
    m = re.match(r"(\d+)(?::(\d+))?\s*(am|pm)?", t.lower())
    if not m:
        return 0
    h, mi = int(m.group(1)), int(m.group(2) or 0)
    if m.group(3) == "pm" and h != 12:
        h += 12
    if h < 8:                       # "4:30 – 6:30pm" — bare hour is afternoon
        h += 12
    return h * 60 + mi


def fmt_date(d):
    mo, day = parse_date(d)
    return f"{[k.title() for k, v in MONTHS.items() if v == mo][0]} {day}"


rows = []
for f in sorted(glob.glob(os.path.join(SESSIONS, "*.json"))):
    if os.path.basename(f).startswith("_"):
        continue
    d = json.load(open(f))
    rows.append({
        "date": fmt_date(txt(d.get("date"))),
        "time": txt(d.get("time")).replace("PST", "PT"),
        "title": txt(d.get("session_title")),
        "detail": txt(d.get("topic_detail")),
        "guest": txt(d.get("guest_name")),
        "firm": txt(d.get("guest_logo_alt")),
        "virtual": "virtual" in txt(d.get("location")).lower(),
        "sort": (parse_date(txt(d.get("date"))), parse_time(txt(d.get("time")))),
    })
rows.sort(key=lambda r: r["sort"])

e = html.escape
cards = "\n".join(f'''    <li class="s">
      <div class="when"><span class="d">{e(r["date"])}</span><span class="t">{e(r["time"])}</span></div>
      <div class="body">
        <p class="topic">{e(r["title"])}</p>
        <p class="detail">{e(r["detail"])}</p>
        <p class="guest"><b>{e(r["guest"])}</b> · {e(r["firm"])}</p>
      </div>
      <span class="tag{' virt' if r["virtual"] else ''}">{"Online" if r["virtual"] else "In person"}</span>
    </li>''' for r in rows)

span = f'{rows[0]["date"]} – {rows[-1]["date"]}, 2026' if rows else ""
page = open(os.path.join(ROOT, "template.html")).read()
page = page.replace("<!--SESSIONS-->", cards).replace("__COUNT__", str(len(rows))).replace("__SPAN__", span)
open(os.path.join(ROOT, "index.html"), "w").write(page)
print(f"index.html — {len(rows)} sessions, {span}")
