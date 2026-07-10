# -*- coding: utf-8 -*-
"""
Money Intel Daily — static blog builder.

Reads posts_md/YYYY-MM-DD-slug.md (intel-bots blog_post.md format, old or new),
renders posts/ + index.html + feed.xml + sitemap.xml + robots.txt.
Re-run to rebuild everything; called automatically by intel-bots blog_publisher.
"""
import html
import re
from datetime import datetime
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
SRC = ROOT / "posts_md"
BASE = "https://youfuxu.github.io/money-intel-daily"
BRAND = "Money Intel Daily"
TAGLINE = "One money idea every day — with real numbers, not just headlines."
YT_URL = "https://www.youtube.com/@MoneyIntelDaily"
EMAIL_URL = "https://moneyintel.beehiiv.com"

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&display=swap" rel="stylesheet">')

MD_EXT = ["tables", "fenced_code", "sane_lists"]


def clean_body_lines(lines):
    """Drop placeholder / self-referential / orphan-header lines from the body."""
    keep = [ln for ln in lines
            if "[Add" not in ln
            and "beehiiv.com" not in ln
            and not ln.lstrip().startswith("📊 Read this breakdown as an article")
            and not ln.lstrip().startswith("📺")
            and not ln.lstrip().startswith("🔔")]
    out = []
    for i, ln in enumerate(keep):
        s = ln.rstrip()
        if s.endswith(":") and not s.lstrip().startswith(("→", "#", ">")):
            nxt = [n for n in keep[i + 1:i + 4]]
            if not any(n.lstrip().startswith("→") for n in nxt):
                continue  # header whose links were all filtered out
        if ln.lstrip().startswith("→"):
            if out and out[-1].strip() and not out[-1].lstrip().startswith("-"):
                out.append("")  # blank line so markdown starts a list
            out.append(linkify_arrow(ln))
            continue
        out.append(ln)
    return out


def linkify_arrow(ln: str) -> str:
    """'→ Label (desc): https://url' -> clickable sponsored list item."""
    m = re.match(r"\s*→\s*(.+?):\s*(https?://\S+)\s*$", ln)
    if m:
        label, url = html.escape(m.group(1).strip()), m.group(2)
        return f'- <a href="{url}" rel="nofollow sponsored noopener" target="_blank">{label}</a>'
    body = re.sub(r"(https?://\S+)",
                  r'<a href="\1" rel="nofollow sponsored noopener" target="_blank">\1</a>',
                  ln.lstrip()[1:].strip())
    return f"- {body}"


def parse_post(path: Path):
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()

    m = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)", path.stem)
    date_iso, slug = (m.group(1), m.group(2)) if m else ("2026-01-01", path.stem)
    date_obj = datetime.strptime(date_iso, "%Y-%m-%d")

    m_t = re.search(r"^TITLE:\s*(.+)$", raw, re.M)
    m_h1 = re.search(r"^#\s+(.+)$", raw, re.M)
    title = (m_t.group(1) if m_t else (m_h1.group(1) if m_h1 else path.stem)).strip()
    m_s = re.search(r"^SUBTITLE:\s*(.+)$", raw, re.M)
    subtitle = m_s.group(1).strip() if m_s else ""

    m_yt = re.search(r"\[Watch on YouTube\]\((https?://[^)]+)\)", raw) or \
           re.search(r"\*\*Watch the video:\*\*\s*\[[^\]]*\]\((https?://[^)]+)\)", raw)
    youtube = m_yt.group(1) if m_yt else ""

    body = []
    for ln in lines:
        s = ln.strip()
        if (s.startswith(("TITLE:", "SUBTITLE:", "# ", "<!--"))
                or s.startswith(("**Published:**", "**Channel:**", "**Watch the video:**"))):
            continue
        body.append(ln)
    while body and body[0].strip() in ("", "---"):
        body.pop(0)
    # drop the trailing generated CTA block (site renders its own)
    text = "\n".join(clean_body_lines(body)).strip()
    text = re.sub(r"\n---\s*\n\*Enjoyed this\?.*$", "", text, flags=re.S).strip()

    body_html = markdown.markdown(text, extensions=MD_EXT)
    body_html = body_html.replace("<table>", '<div class="table-scroll"><table>') \
                         .replace("</table>", "</table></div>")

    desc = subtitle
    if not desc:
        plain = re.sub(r"<[^>]+>", "", body_html).strip().replace("\n", " ")
        desc = plain[:155]

    return {"slug": slug, "title": title, "subtitle": subtitle, "desc": desc,
            "youtube": youtube, "body": body_html,
            "date_iso": date_iso, "date_disp": date_obj.strftime("%B %d, %Y"),
            "date_obj": date_obj}


def topbar(prefix=""):
    return (f'<div class="topbar"><div class="wrap">'
            f'<a class="logo" href="{prefix}index.html">Money<span class="dot">Intel</span>Daily</a>'
            f'<div class="topnav">'
            f'<a href="{YT_URL}" target="_blank" rel="noopener">YouTube</a>'
            f'<a href="{EMAIL_URL}" target="_blank" rel="noopener">Newsletter</a>'
            f'</div></div></div>')


def footer():
    return (f'<footer><div class="wrap">'
            f'<div>© 2026 {BRAND} — {html.escape(TAGLINE)}</div>'
            f'<div class="fine">Educational content only — not financial advice. Do your own research. '
            f'Some links are affiliate links; we may earn a commission at no extra cost to you.</div>'
            f'</div></footer>')


def head_block(title, desc, canonical, og_type="article", extra=""):
    t, d = html.escape(title, quote=True), html.escape(desc, quote=True)
    return (f'<meta charset="UTF-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{t}</title>\n<meta name="description" content="{d}">\n'
            f'<link rel="canonical" href="{canonical}">\n'
            f'<meta property="og:type" content="{og_type}">\n'
            f'<meta property="og:title" content="{t}">\n'
            f'<meta property="og:description" content="{d}">\n'
            f'<meta property="og:url" content="{canonical}">\n'
            f'<meta property="og:site_name" content="{BRAND}">\n'
            f'<meta name="twitter:card" content="summary">\n'
            f'<link rel="alternate" type="application/rss+xml" title="{BRAND}" href="{BASE}/feed.xml">\n'
            f'{extra}{FONTS}\n')


def post_page(p):
    url = f"{BASE}/posts/{p['slug']}.html"
    schema = ('<script type="application/ld+json">{'
              f'"@context":"https://schema.org","@type":"Article",'
              f'"headline":{esc_json(p["title"])},"datePublished":"{p["date_iso"]}",'
              f'"author":{{"@type":"Organization","name":"{BRAND}"}},'
              f'"publisher":{{"@type":"Organization","name":"{BRAND}"}},'
              f'"mainEntityOfPage":"{url}"'
              '}</script>\n')
    watch = (f'<a class="watch" href="{p["youtube"]}" target="_blank" rel="noopener">'
             f'▶ Watch this breakdown on YouTube</a>' if p["youtube"] else "")
    lead = f'<p class="lead">{html.escape(p["subtitle"])}</p>' if p["subtitle"] else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_block(f"{p['title']} | {BRAND}", p['desc'], url, extra=schema)}<link rel="stylesheet" href="../assets/style.css">
</head>
<body>
{topbar("../")}
<article><div class="wrap">
  <div class="crumb"><a href="../index.html">Home</a> › Daily Breakdown</div>
  <h1>{html.escape(p['title'])}</h1>
  <div class="byline">{BRAND} · {p['date_disp']}</div>
  {lead}
  {watch}
  {p['body']}
  <div class="cta">
    <h3>One money idea every day</h3>
    <p>Real numbers, not just headlines. Subscribe on
       <a href="{YT_URL}" target="_blank" rel="noopener">YouTube</a> or get it
       <a href="{EMAIL_URL}" target="_blank" rel="noopener">by email</a>.</p>
  </div>
  <p class="disclaimer">This article is for education and information only and is not financial advice.
  Past performance does not guarantee future results. Do your own research before investing.
  Some links above are affiliate links — we may earn a commission at no extra cost to you.</p>
</div></article>
{footer()}
</body>
</html>
"""


def esc_json(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def card(p):
    return (f'<a class="card" href="posts/{p["slug"]}.html">'
            f'<div class="ct">{p["date_disp"]}</div>'
            f'<div class="ch">{html.escape(p["title"])}</div>'
            f'<div class="cd">{html.escape(p["desc"][:150])}</div></a>')


def index_page(posts):
    cards = "".join(card(p) for p in posts)
    hero = (f'<div class="hero"><div class="wrap"><h1>{BRAND}</h1>'
            f'<p>{html.escape(TAGLINE)}</p>'
            f'<div class="hero-btns">'
            f'<a class="btn" href="{YT_URL}" target="_blank" rel="noopener">▶ Subscribe on YouTube</a>'
            f'<a class="btn ghost" href="{EMAIL_URL}" target="_blank" rel="noopener">✉ Get it by email</a>'
            f'</div></div></div>')
    body = hero + f'<div class="wrap"><div class="section-title"><span class="bar"></span>All breakdowns</div><div class="cards">{cards}</div></div>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_block(f"{BRAND} | {TAGLINE}", f"{BRAND} — {TAGLINE} Daily personal-finance breakdowns with the exact math.", f"{BASE}/", og_type="website")}<link rel="stylesheet" href="assets/style.css">
</head>
<body>
{topbar()}
{body}
{footer()}
</body>
</html>
"""


def rss(posts):
    items = ""
    for p in posts[:20]:
        pub = p["date_obj"].strftime("%a, %d %b %Y 10:00:00 +0000")
        items += (f"<item><title>{html.escape(p['title'])}</title>"
                  f"<link>{BASE}/posts/{p['slug']}.html</link>"
                  f"<guid>{BASE}/posts/{p['slug']}.html</guid>"
                  f"<pubDate>{pub}</pubDate>"
                  f"<description>{html.escape(p['desc'])}</description></item>\n")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<rss version="2.0"><channel><title>{BRAND}</title>'
            f'<link>{BASE}/</link><description>{html.escape(TAGLINE)}</description>\n'
            f'{items}</channel></rss>\n')


def main():
    posts = sorted((parse_post(f) for f in SRC.glob("*.md")),
                   key=lambda p: p["date_iso"], reverse=True)
    (ROOT / "posts").mkdir(exist_ok=True)
    for p in posts:
        (ROOT / "posts" / f"{p['slug']}.html").write_text(post_page(p), encoding="utf-8")
    (ROOT / "index.html").write_text(index_page(posts), encoding="utf-8")
    (ROOT / "feed.xml").write_text(rss(posts), encoding="utf-8")

    today = datetime.now().strftime("%Y-%m-%d")
    urls = [(f"{BASE}/", today)] + [(f"{BASE}/posts/{p['slug']}.html", p["date_iso"]) for p in posts]
    entries = "\n".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls)
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n",
                                     encoding="utf-8")
    print(f"[build] {len(posts)} posts + index + feed + sitemap done")


if __name__ == "__main__":
    main()
