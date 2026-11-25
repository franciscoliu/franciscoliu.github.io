#!/usr/bin/env python3
"""Generate the publication lists on the website.

Sources (edit these, never the generated HTML):
  data/publications.bib        copy of the CV's BibTeX file: titles, authors, order, equal-contribution stars
  data/publications_meta.json  website-only data per BibTeX key: topic, selected/home flags, venue label,
                               thumbnail, links, notes

Output: the blocks between <!-- PUBS:START --> and <!-- PUBS:END --> in
  publications.html  (all entries. "Selected" = every paper with Zheyuan Liu as first or equal-first author,
                      preprints included, plus the entries marked "selected": true in the metadata.)
  index.html         (accepted papers with Zheyuan Liu as first or equal-first author; no topic tags.
                      An entry's "home": true/false in the metadata overrides the rule.)

Usage:
  python3 scripts/build_publications.py           rewrite the two pages
  python3 scripts/build_publications.py --check   exit 1 if the pages are out of date (nothing is written)
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIB = ROOT / "data" / "publications.bib"
META = ROOT / "data" / "publications_meta.json"
START, END = "<!-- PUBS:START -->", "<!-- PUBS:END -->"
TOPICS = {"knowledge": ("k", "Knowledge"), "response": ("r", "Response"), "action": ("a", "Action")}


def clean_tex(s):
    s = re.sub(r"\\textbf\{\\textcolor\{red\}\{([^}]*)\}\}", r"\1", s)
    s = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", s)
    s = s.replace("\\%", "%").replace("\\&", "&")
    s = re.sub(r"[{}]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_bib(text):
    entries = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", text, flags=re.S):
        key, body = m.group(2), m.group(3)
        fields = {}
        for fm in re.finditer(
            r'(\w+)\s*=\s*(\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}|"[^"]*"|\d+)\s*,?', body, flags=re.S
        ):
            value = fm.group(2).strip()
            if value[0] in '{"':
                value = value[1:-1]
            fields[fm.group(1).lower()] = value
        authors = []
        for raw in re.split(r"\s+and\s+", re.sub(r"\s+", " ", fields.get("author", ""))):
            me = "textbf" in raw
            name = clean_tex(raw)
            if name == "others":
                authors.append({"name": "et al.", "me": False, "star": False})
                continue
            star = "*" in name
            name = name.replace("*", "")
            if "," in name:
                last, first = [x.strip() for x in name.split(",", 1)]
                name = f"{first} {last}"
            authors.append({"name": name, "me": me, "star": star})
        entries.append(
            {"key": key, "title": clean_tex(fields.get("title", "")), "authors": authors, "year": fields.get("year", "")}
        )
    return entries


def lead_author(entry):
    """Zheyuan Liu is the first author or an equal-contribution (starred) author."""
    authors = entry["authors"]
    return bool(authors) and (authors[0]["me"] or any(a["me"] and a["star"] for a in authors))


def render(entry, meta, tags=True):
    e = html.escape
    key = entry["key"]
    title = meta.get("title") or entry["title"]
    links = meta.get("links", {})
    thumb = meta.get("thumb")
    topic = meta.get("pillar", "other")

    names = []
    for a in entry["authors"]:
        label = e(a["name"]) + ("*" if a["star"] else "")
        names.append(f"<b>{label}</b>" if a["me"] else label)
    authors = ", ".join(names)

    head = [f'<span class="yr">{e(entry["year"])}</span>', f'<span class="venue">{e(meta.get("venue", ""))}</span>']
    if meta.get("note"):
        head.append(f'<span class="note">{e(meta["note"])}</span>')

    paper = links.get("Paper")
    title_html = (
        f'<a class="title" href="{e(paper)}">{e(title)}</a>' if paper else f'<span class="title">{e(title)}</span>'
    )

    row = []
    if tags and topic in TOPICS:
        cls, label = TOPICS[topic]
        row.append(f'<span class="tag {cls}">{label}</span>')
    for label, url in links.items():
        row.append(f'<a href="{e(url)}">{e(label)}</a>')
    if meta.get("stat"):
        tip = f' title="{e(meta["stat_title"])}"' if meta.get("stat_title") else ""
        row.append(f'<span class="stat"{tip}>{e(meta["stat"])}</span>')
    if meta.get("extra"):
        row.append(f'<span class="extra">{e(meta["extra"])}</span>')

    classes = "pub" if thumb else "pub nothumb"
    selected = "true" if meta.get("selected") or lead_author(entry) else "false"
    out = [f'    <article class="{classes}" id="{e(key)}" data-topic="{topic}" data-selected="{selected}">']
    out.append(f'      <div class="pub-meta">{"".join(head)}</div>')
    if thumb:
        out.append(f'      <img class="thumb" src="{e(thumb)}" alt="" loading="lazy">')
    out.append('      <div class="pub-body">')
    out.append(f"        {title_html}")
    out.append(f'        <p class="authors">{authors}</p>')
    if row:
        out.append(f'        <p class="plinks">{"".join(row)}</p>')
    out.append("      </div>")
    out.append("    </article>")
    return "\n".join(out)


def build():
    entries = parse_bib(BIB.read_text(encoding="utf-8"))
    meta = json.loads(META.read_text(encoding="utf-8"))["entries"]
    missing = [x["key"] for x in entries if x["key"] not in meta]
    if missing:
        sys.exit(f"No entry in {META.name} for: {', '.join(missing)}")

    def sort_key(pair):
        index, entry = pair
        m = meta[entry["key"]]
        return (-int(entry["year"] or 0), bool(m.get("preprint")), not lead_author(entry), index)

    def on_home(entry):
        m = meta[entry["key"]]
        if "home" in m:
            return bool(m["home"])
        return lead_author(entry) and not m.get("preprint")

    ordered = [entry for _, entry in sorted(enumerate(entries), key=sort_key)]
    all_html = "\n\n".join(render(x, meta[x["key"]]) for x in ordered)
    home_html = "\n\n".join(render(x, meta[x["key"]], tags=False) for x in ordered if on_home(x))
    return {"publications.html": all_html, "index.html": home_html}, len(ordered)


def inject(page, block):
    text = page.read_text(encoding="utf-8")
    if START not in text or END not in text:
        sys.exit(f"{page.name}: markers {START} / {END} not found")
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    return text, f"{before}{START}\n{block}\n    {END}{after}"


def main():
    check = "--check" in sys.argv
    blocks, count = build()
    stale = []
    for name, block in blocks.items():
        page = ROOT / name
        old, new = inject(page, block)
        if old != new:
            stale.append(name)
            if not check:
                page.write_text(new, encoding="utf-8")
    if check:
        if stale:
            sys.exit(f"Out of date: {', '.join(stale)}. Run: python3 scripts/build_publications.py")
        print(f"Up to date ({count} publications).")
    else:
        print(f"{count} publications. Rewritten: {', '.join(stale) if stale else 'nothing (already up to date)'}.")


if __name__ == "__main__":
    main()
