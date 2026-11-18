#!/usr/bin/env python3
"""One-off: turn the Google Fonts TTFs into small static WOFF2 subsets for the cards.
Usage: python build_fonts.py <src_dir> <out_dir> <spec>...   spec = file.ttf:wght:outname
Needs fonttools + brotli (not needed by the daily workflow)."""
import json, os, sys
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset

UNICODES = (list(range(0x20, 0x7F)) + list(range(0xA0, 0x100)) +
            [0x152, 0x153, 0x2019, 0x2013, 0x2014, 0x2026, 0x20AC, 0x2192, 0x2197, 0x2022, 0x202F, 0x2191, 0x2713])

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
metrics = {}
for spec in sys.argv[3:]:
    fname, wght, name = spec.split(":")
    font = TTFont(os.path.join(src, fname))
    if "fvar" in font:
        axes = {a.axisTag: (int(wght) if a.axisTag == "wght" else a.defaultValue) for a in font["fvar"].axes}
        font = instancer.instantiateVariableFont(font, axes)
    opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["kern", "liga", "tnum", "lnum"]
    opts.name_IDs = []; opts.notdef_outline = True; opts.hinting = False
    sub = subset.Subsetter(opts); sub.populate(unicodes=UNICODES); sub.subset(font)
    path = os.path.join(out, name + ".woff2"); font.flavor = "woff2"; font.save(path)
    cmap, hmtx = font.getBestCmap(), font["hmtx"]
    metrics[name] = {"upm": font["head"].unitsPerEm,
                     "w": {chr(u): hmtx[g][0] for u, g in cmap.items() if u in UNICODES}}
    print(path, os.path.getsize(path))
json.dump(metrics, open(os.path.join(out, "metrics.json"), "w"), ensure_ascii=False, separators=(",", ":"))
