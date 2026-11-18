#!/usr/bin/env python3
"""Render the personal profile cards (cards/*-light.svg, cards/*-dark.svg).

Identity « Plan de vol » (black and white, IBM Plex Sans + Plex Mono, square on
the baseline). Every number links to a page that proves it: the ENI book page,
roekish.com case studies, the public repos, and data/contributions.json scraped
daily from the public GitHub calendar (scripts/fetch_contributions.py).
STATIC=1 renders the final frame only.
"""
import datetime
import json
import os

from svgcards import Fonts, countup, d, nb, rule, svg, text, write

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "cards")

S, M = "IBM Plex Sans", "IBM Plex Mono"
FONTS = Fonts(os.path.join(ROOT, "fonts"), {S: {400: "sans-400", 600: "sans-600"}, M: {400: "mono-400", 500: "mono-500"}})

THEMES = {
    "light": dict(bg="#F7F7F5", border="#DCDDD8", ink="#101418", ink2="#5E656E", line="#DCDDD8", bar="#101418", bar2="#B9BCB6"),
    "dark": dict(bg="#101418", border="#2A3037", ink="#F7F7F5", ink2="#A0A7AF", line="#2A3037", bar="#F7F7F5", bar2="#4A5159"),
}

MONTHS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def panel(w, h, t):
    return f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="6" fill="{t["bg"]}" stroke="{t["border"]}"/>'


def link(x, y, s, t, delay):
    return text(x, y, s + " →", 12.5, M, 500, t["ink"], delay=delay)


def fr_date(day):
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def hero(t):
    w, h, x = 880, 300, 44
    name_w = FONTS.width("Alexis Maison", S, 600, 30, -0.3)
    title = FONTS.wrap("Consultant Odoo et développeur. J'ai fondé Roekish, intégrateur Odoo, "
                       "et écrit un livre sur Next.js.", S, 600, 27, 720)
    b = [panel(w, h, t),
         text(x, 66, "Alexis Maison", 30, S, 600, t["ink"], delay=0.0, spacing=-0.3),
         f'<rect x="{x + name_w + 6:.1f}" y="59" width="7" height="7" fill="{t["ink"]}" class="fo"{d(0.35)}/>',
         text(w - x, 64, "Conseil en systèmes de gestion · Odoo", 12.5, M, 400, t["ink2"], delay=0.15, anchor="end")]
    b.append(rule(x, 92, w - x, 92, t["line"], delay=0.2))
    b += [text(x, 140 + 36 * i, line, 27, S, 600, t["ink"], delay=0.45 + 0.12 * i, spacing=-0.3) for i, line in enumerate(title)]
    # flight plan: a dashed route with three waypoints
    y = h - 52
    x1, x2 = x + 6, w - x - 6
    stops = [(x1, "Build."), ((x1 + x2) / 2, "Fly."), (x2, "Learn.")]
    b.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{t["ink2"]}" stroke-width="1" stroke-dasharray="3 5" '
             f'class="gx"{d(0.9)}/>')
    for i, (sx, label) in enumerate(stops):
        dl = 1.0 + 0.35 * i
        b.append(f'<rect x="{sx - 4}" y="{y - 4}" width="8" height="8" fill="{t["ink"]}" class="fo"{d(dl)}/>')
        anchor = "start" if i == 0 else "end" if i == 2 else "middle"
        b.append(text(sx + (-4 if i == 0 else 4 if i == 2 else 0), y + 28, label, 13, M, 500, t["ink"], delay=dl + 0.1, anchor=anchor))
    b.append(text(w / 2, y - 14, "Lyon · Annecy · Grenoble", 12, M, 400, t["ink2"], delay=1.1, anchor="middle"))
    return svg(w, h, "".join(b), FONTS, None, "Alexis Maison, consultant Odoo et développeur, fondateur de Roekish, auteur chez ENI")


TILES = [
    {"key": "livre", "label": "Livre", "value": 464, "fmt": lambda v: f"{v} pages",
     "caption": "Next.js pour les développeurs React, Éditions ENI, avril 2026.", "href": "editions-eni.fr"},
    {"key": "roekish", "label": "Roekish", "value": 24, "fmt": lambda v: f"{v}+ PME",
     "caption": "accompagnées avec Roekish, l'agence Odoo que j'ai fondée en 2023.", "href": "roekish.com/etudes-de-cas"},
    {"key": "open-source", "label": "Open source", "value": 3, "fmt": lambda v: f"{v} modules",
     "caption": "transporteurs Odoo 19 publiés : La Poste, Mondial Relay, DPD.", "href": "github.com/roekish-org"},
]


def tile(t, spec, i):
    w, h, x = 286, 184, 22
    base = 0.25 * i
    cap = FONTS.wrap(spec["caption"], S, 400, 14, w - 2 * x)
    b = [panel(w, h, t),
         f'<rect x="{x}" y="27" width="6" height="6" fill="{t["ink"]}" class="fo"{d(base)}/>',
         text(x + 14, 34, spec["label"], 12.5, M, 500, t["ink2"], delay=base),
         countup(x, 86, spec["value"], spec["fmt"], 36, S, 600, t["ink"], delay=base + 0.15, spacing=-0.6)]
    b += [text(x, 116 + 20 * j, line, 14, S, 400, t["ink2"], delay=base + 0.4 + 0.08 * j) for j, line in enumerate(cap)]
    b.append(link(x, h - 20, spec["href"], t, base + 0.7))
    return svg(w, h, "".join(b), FONTS, None, f'{spec["label"]} : {spec["fmt"](spec["value"])} {spec["caption"]}')


def activity(t, data):
    w, x = 880, 44
    months = data["monthly"][-13:]
    top, chart_h, gap = 92, 120, 10
    bar_w = (w - 2 * x - gap * (len(months) - 1)) / len(months)
    peak = max(m["total"] for m in months) or 1
    best = max(months, key=lambda m: m["total"])
    end = datetime.date.fromisoformat(data["range"]["end"])
    stats_y = top + chart_h + 74
    h = stats_y + 92
    b = [panel(w, h, t),
         text(x, 52, "Contributions GitHub, 12 derniers mois", 20, S, 600, t["ink"], delay=0.0),
         text(w - x, 52, f"$ git log --since=\"{data['range']['start']}\"", 12, M, 400, t["ink2"], delay=0.1, anchor="end")]
    base_y = top + chart_h
    for i, m in enumerate(months):
        bx = x + i * (bar_w + gap)
        bh = max(2, chart_h * m["total"] / peak)
        current = m["month"] == end.strftime("%Y-%m")
        fill = t["bar2"] if current else t["bar"]
        b.append(f'<rect x="{bx:.1f}" y="{base_y - bh:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" fill="{fill}" class="gr"{d(0.3 + 0.06 * i)}/>')
        yy, mm = map(int, m["month"].split("-"))
        label = MONTHS[mm - 1] + (f" {str(yy)[2:]}" if mm == 1 or i == 0 else "")
        b.append(text(bx + bar_w / 2, base_y + 22, label, 11, M, 400, t["ink2"], delay=0.3 + 0.06 * i, anchor="middle"))
        if m is best:
            b.append(text(bx + bar_w / 2, base_y - bh - 8, nb(m["total"]), 11, M, 500, t["ink"], delay=1.2, anchor="middle"))
    b.append(rule(x, base_y + 0.5, w - x, base_y + 0.5, t["line"], delay=0.2, draw=False))
    best_day = datetime.date.fromisoformat(data["best_day"]["date"])
    stats = [
        (data["total_contributions"], lambda v: nb(int(v)), "contributions"),
        (data["active_days"], lambda v: nb(int(v)), "jours actifs sur 12 mois"),
        (data["current_streak"]["length"], lambda v: f"{int(v)} j", "de série en cours"),
        (data["best_day"]["count"], lambda v: nb(int(v)), f"le {best_day.day} {MONTHS[best_day.month - 1]}, record"),
    ]
    col = (w - 2 * x) / len(stats)
    b.append(rule(x, stats_y - 34, w - x, stats_y - 34, t["line"], delay=1.0))
    for i, (v, fmt, label) in enumerate(stats):
        sx = x + col * i
        b.append(countup(sx, stats_y, v, fmt, 28, S, 600, t["ink"], delay=1.1 + 0.15 * i, spacing=-0.4))
        b.append(text(sx, stats_y + 24, label, 12.5, S, 400, t["ink2"], delay=1.3 + 0.15 * i))
    b.append(text(x, h - 20, f"Calendrier public de github.com/alexis2m, relu le {fr_date(end)}. Barre claire : mois en cours.",
                  11.5, M, 400, t["ink2"], delay=1.8))
    return svg(w, h, "".join(b), FONTS, None,
               f'{nb(data["total_contributions"])} contributions GitHub sur 12 mois, {data["active_days"]} jours actifs, '
               f'série en cours de {data["current_streak"]["length"]} jours')


def main():
    data = json.load(open(os.path.join(ROOT, "data", "contributions.json"), encoding="utf-8"))
    for name, t in THEMES.items():
        write(os.path.join(OUT, f"hero-{name}.svg"), hero(t))
        for i, spec in enumerate(TILES):
            write(os.path.join(OUT, f"tile-{spec['key']}-{name}.svg"), tile(t, spec, i))
        write(os.path.join(OUT, f"activity-{name}.svg"), activity(t, data))


if __name__ == "__main__":
    main()
