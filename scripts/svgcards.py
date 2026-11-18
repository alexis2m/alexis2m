"""Small toolkit for animated README cards (stdlib only).

GitHub shows README images through <img>: no script, no external request, but
the SVG's own <style> (CSS keyframes) and SMIL run. So fonts are embedded as
base64 WOFF2 subsets, motion is one-shot CSS with staggered delays, numbers
count up with SMIL <set> frames, and everything stops under reduced motion.
STATIC=1 renders the final frame only (for screenshots and review).
"""
import base64
import json
import os
from html import escape

STATIC = os.environ.get("STATIC") == "1"


class Fonts:
    """Embedded fonts + advance-width metrics (from fonts/metrics.json)."""

    def __init__(self, font_dir, families):
        # families: {css_family: {weight: file_stem}}
        self.dir = font_dir
        self.families = families
        self.metrics = json.load(open(os.path.join(font_dir, "metrics.json"), encoding="utf-8"))
        self.stem = {(fam, w): stem for fam, ws in families.items() for w, stem in ws.items()}

    def css(self):
        out = []
        for (fam, w), stem in self.stem.items():
            b64 = base64.b64encode(open(os.path.join(self.dir, stem + ".woff2"), "rb").read()).decode()
            out.append(f"@font-face{{font-family:'{fam}';font-weight:{w};src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
        return "".join(out)

    def width(self, s, fam, w, size, spacing=0.0):
        m = self.metrics[self.stem[(fam, w)]]
        fallback = m["w"].get("n", m["upm"] // 2)
        return sum(m["w"].get(c, fallback) for c in s) * size / m["upm"] + spacing * max(len(s) - 1, 0)

    def wrap(self, s, fam, w, size, max_w):
        lines, cur = [], ""
        for word in s.split(" "):
            test = (cur + " " + word).strip()
            if cur and self.width(test, fam, w, size) > max_w:
                lines.append(cur)
                cur = word
            else:
                cur = test
        if cur:
            lines.append(cur)
        return lines


BASE_CSS = """
.f{opacity:0;animation:rise .7s cubic-bezier(.2,.7,.2,1) forwards}
.fo{opacity:0;animation:fade .6s ease-out forwards}
.dr{animation:draw 1s cubic-bezier(.6,0,.2,1) forwards}
.gr{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(0);animation:grow .8s cubic-bezier(.2,.7,.2,1) forwards}
.gx{transform-box:fill-box;transform-origin:0 50%;transform:scaleX(0);animation:growx .9s cubic-bezier(.2,.7,.2,1) forwards}
@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes fade{to{opacity:1}}
@keyframes draw{to{stroke-dashoffset:0}}
@keyframes grow{to{transform:scaleY(1)}}
@keyframes growx{to{transform:scaleX(1)}}
@media (prefers-reduced-motion:reduce){
.f,.fo,.dr,.gr,.gx{animation:none!important;opacity:1!important;transform:none!important;stroke-dashoffset:0!important}
.cu{display:none!important}}
"""

STATIC_CSS = "*{animation:none!important}.f,.fo{opacity:1}.dr{stroke-dashoffset:0!important}.gr,.gx{transform:none}"


def d(t):
    """Inline animation delay."""
    return f' style="animation-delay:{t:.2f}s"'


def text(x, y, s, size, fam, w, fill, cls="f", delay=0.0, anchor="start", spacing=0.0, extra=""):
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    c = f' class="{cls}"{d(delay)}' if cls else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-weight="{w}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}"{ls}{c}{extra}>{escape(s)}</text>')


def rule(x1, y1, x2, y2, stroke, width=1.0, delay=0.0, draw=True):
    if not draw:
        return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width}"/>'
    length = abs(x2 - x1) + abs(y2 - y1)
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width}" '
            f'stroke-dasharray="{length:.1f}" stroke-dashoffset="{length:.1f}" class="dr"{d(delay)}/>')


def countup(x, y, value, fmt, size, fam, w, fill, delay=0.0, dur=0.9, frames=18, anchor="start", spacing=0.0):
    """Number that counts from 0 to value: SMIL shows one frame at a time, then the final
    text fades in for good. Reduced motion and STATIC show only the final text."""
    final = text(x, y, fmt(value), size, fam, w, fill, cls="fo", delay=delay + dur, anchor=anchor, spacing=spacing)
    if STATIC:
        return final
    step = dur / frames
    out = []
    for i in range(frames):
        v = value * ((i + 1) / (frames + 1)) ** 0.6
        v = round(v, 1) if isinstance(value, float) else int(v)
        t0 = delay + i * step
        out.append(
            text(x, y, fmt(v), size, fam, w, fill, cls="", anchor=anchor, spacing=spacing,
                 extra=f' opacity="0" class="cu"').replace(
                "</text>",
                f'<set attributeName="opacity" to="1" begin="{t0:.3f}s" dur="{step:.3f}s"/></text>'))
    return "".join(out) + final


def svg(w, h, body, fonts, bg, title, extra_css=""):
    bg_rect = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    css = fonts.css() + BASE_CSS + (STATIC_CSS if STATIC else "") + extra_css
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(title)}"><title>{escape(title)}</title>'
            f'<style>{css}</style>{bg_rect}{body}</svg>')


def nb(n):
    """French thousands separator (narrow no-break space)."""
    return f"{n:,}".replace(",", " ")


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"wrote {path} ({len(content) // 1024} KB)")
