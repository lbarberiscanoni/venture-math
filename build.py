#!/usr/bin/env python3
"""Generate index.html from the session flyers.

`../fliers/sessions/*.json` is the source of truth for the schedule — it is what the
printed flyers are built from — so the public page is generated from the same data
rather than hand-maintained alongside it.

Sessions with no flyer are simply absent (there is no session 07 / Oct 14), and the
page shows dates rather than session numbers so the gap in the flyer numbering does
not surface as a hole in the schedule.
"""
import glob, html, json, os, re, shutil

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


FLYERS_SRC = os.path.join(ROOT, "..", "fliers", "out")
FLYERS_DST = os.path.join(ROOT, "fliers")
# Anything still carrying drafting markers must not reach a public URL.
PLACEHOLDERS = ("TO REPLACE", "First Lastname", "guest-placeholder", "Lorem")

ASSETS_SRC = os.path.join(ROOT, "..", "fliers", "assets")
ASSETS_DST = os.path.join(ROOT, "assets")


def asset(ref):
    """Turn a flyer asset ref ("../assets/x.jpg") into a basename that exists in fliers/assets."""
    if not ref:
        return ""
    name = os.path.basename(str(ref))
    return name if os.path.exists(os.path.join(ASSETS_SRC, name)) else ""


def role(title):
    """First clause of the guest title is the current role; the rest is prior history."""
    return re.split(r"\s*·\s*", title)[0] if title else ""


rows, held = [], []
for f in sorted(glob.glob(os.path.join(SESSIONS, "*.json"))):
    if os.path.basename(f).startswith("_"):
        continue
    raw = open(f, encoding="utf-8").read()
    d = json.loads(raw)
    slug = d.get("slug") or os.path.splitext(os.path.basename(f))[0]
    unfinished = [m for m in PLACEHOLDERS if m in raw]
    if unfinished:
        held.append((slug, unfinished))
    title = txt(d.get("guest_title"))
    rows.append({
        "slug": slug, "flyer": "" if unfinished else slug,
        "date": fmt_date(txt(d.get("date"))),
        "time": txt(d.get("time")).replace("PST", "PT"),
        "title": txt(d.get("session_title")),
        "detail": txt(d.get("topic_detail")),
        "guest": txt(d.get("guest_name")),
        "firm": txt(d.get("guest_logo_alt")),
        "role": role(title),
        "photo": asset(d.get("guest_photo")),
        "logo": asset(d.get("guest_logo")),
        "virtual": "virtual" in txt(d.get("location")).lower(),
        "sort": (parse_date(txt(d.get("date"))), parse_time(txt(d.get("time")))),
    })
rows.sort(key=lambda r: r["sort"])

# copy the guest photos + firm logos the page references into site/assets/
if os.path.isdir(ASSETS_DST):
    shutil.rmtree(ASSETS_DST)
os.makedirs(ASSETS_DST, exist_ok=True)
wanted = {a for r in rows for a in (r["photo"], r["logo"]) if a}
for a in sorted(wanted):
    shutil.copy2(os.path.join(ASSETS_SRC, a), os.path.join(ASSETS_DST, a))

e = html.escape


def avatar(r, cls):
    return (f'<img class="{cls}" src="assets/{e(r["photo"])}" alt="{e(r["guest"])}" '
            f'loading="lazy" width="60" height="60">') if r["photo"] else ""


def logo_plate(r):
    return (f'<span class="logo-plate"><img src="assets/{e(r["logo"])}" '
            f'alt="{e(r["firm"])}" loading="lazy"></span>') if r["logo"] else ""


def guest_block(r):
    if not r["guest"]:
        return ""
    # the first clause of the title already names the firm; the logo plate carries the brand mark,
    # so show the role verbatim and fall back to the bare firm only when there is no role.
    role = f'<div class="role">{e(r["role"])}</div>' if r["role"] else \
           (f'<div class="role"><b>{e(r["firm"])}</b></div>' if r["firm"] else "")
    return (f'<div class="guest">{avatar(r, "avatar")}'
            f'<div class="who"><div class="name">{e(r["guest"])}</div>{role}</div>'
            f'{logo_plate(r)}</div>')


faces = "\n".join(
    f'        <img src="assets/{e(r["photo"])}" alt="{e(r["guest"])}" title="{e(r["guest"])} · {e(r["firm"])}" loading="lazy" width="60" height="60">'
    for r in rows if r["photo"])

cards = "\n".join(f'''    <li class="s reveal" style="--i:{i + 2}">
      <div class="when"><span class="d">{e(r["date"])}</span><span class="t">{e(r["time"])}</span></div>
      <div class="body">
        <p class="topic">{e(r["title"])}</p>
        <p class="detail">{e(r["detail"])}</p>
        {guest_block(r)}
      </div>
      <div class="aside">
        <span class="tag{' virt' if r["virtual"] else ''}">{"Online" if r["virtual"] else "In person"}</span>
        {f'<a class="fly" href="fliers/{r["flyer"]}.html">Flyer</a>' if r["flyer"] else ''}
      </div>
    </li>''' for i, r in enumerate(rows))

span = f'{rows[0]["date"]} – {rows[-1]["date"]}, 2026' if rows else ""
page = open(os.path.join(ROOT, "template.html")).read()
page = (page.replace("<!--FACES-->", faces).replace("<!--SESSIONS-->", cards)
            .replace("__COUNT__", str(len(rows))).replace("__SPAN__", span))
open(os.path.join(ROOT, "index.html"), "w").write(page)

# publish only the finished flyers, and clear out any previously-copied ones
if os.path.isdir(FLYERS_DST):
    shutil.rmtree(FLYERS_DST)
os.makedirs(FLYERS_DST, exist_ok=True)
copied = 0
for r in rows:
    if not r["flyer"]:
        continue
    for ext in (".html", ".pdf"):
        src = os.path.join(FLYERS_SRC, r["flyer"] + ext)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(FLYERS_DST, r["flyer"] + ext))
            copied += 1

print(f"index.html — {len(rows)} sessions, {span}")
print(f"fliers/    — {copied} files copied for {sum(1 for r in rows if r['flyer'])} sessions")
for slug, why in held:
    print(f"   HELD BACK: {slug} — contains {', '.join(why)}")
