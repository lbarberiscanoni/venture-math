# Venture Math @ Berkeley — course page

A single static page listing the schedule, topics and guest lineup for
**Venture Math: What the Numbers Really Look Like, from Formation to IPO**
(UC Berkeley Extension, Fall 2026).

`index.html` is **generated** — do not hand-edit it. Run:

```
python3 build.py
```

It reads `../fliers/sessions/*.json`, the same data the printed flyers are built from, and
fills `template.html`. Edit the flyer JSON (or `template.html` for wording and design), then
rebuild. The output is self-contained — no dependencies, no external requests — so you can
open it directly in a browser or serve the folder with any static server.

Generating from the flyers is deliberate: the schedule has already shifted once (Oct 21 changed
guest *and* topic, Nov 4 gained a second session), and a hand-maintained page silently fell out
of step. One source, two outputs.

## Publishing to GitHub Pages

1. Create a **public** repo and push this folder to it. Pages on a private repo requires a
   paid GitHub plan, and the published site is public either way — so a public repo is
   the simpler path for a page that is only course information.
2. Repo **Settings → Pages → Build and deployment**: source *Deploy from a branch*,
   branch `main`, folder `/ (root)`.
3. The site appears at `https://<user>.github.io/<repo>/` within a minute or two.

## Scope — deliberately just the course info

This repo holds **only** the public course page. It is intentionally separate from the
working directory it lives in, which also contains the chart libraries (`carta-charts/`,
`substack-charts/`) and outreach data. Neither belongs here:

- The ~710 charts are third-party material. Carta's report disclosure says
  *"Reproduction prohibited"* and every chart carries an all-rights-reserved footer;
  the rest come from The Information, CB Insights, McKinsey, PitchBook, Bain, Stanford GSB
  and others, each with its own terms. Serving them from a public URL is redistribution.
- The outreach CSVs and warm-intro maps are private business data.

Keep this repo to the page. If the chart library ever needs version control, give it a
separate private repo that tracks the code and metadata and gitignores the images
(they are all re-derivable from the fetch scripts).

## Updating the lineup

Edit `fliers/sessions/*.json` and re-run `build.py`. A session with no flyer simply does
not appear — that is how the empty **Oct 14** slot is handled, and why the page shows dates
rather than session numbers (the flyers number 01–11 with no 07, and a visible gap on a public
schedule invites a question you do not want to answer).

Only add a guest once they have accepted. Having a flyer is the signal — if there is no flyer,
there is no row.
