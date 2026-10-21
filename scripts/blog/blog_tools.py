#!/usr/bin/env python3
"""Helpers for the blog draft -> email approval -> publish pipeline.

Usage (run from the repo root):
  python3 scripts/blog/blog_tools.py check <slug>        SEO/GEO lint a post; exits 1 on errors
  python3 scripts/blog/blog_tools.py email <slug>        print approval email JSON; writes a new review_hash to posts.json
  python3 scripts/blog/blog_tools.py verify <slug> <tok> check a review token from an approval click
  python3 scripts/blog/blog_tools.py bump <slug>         increment a draft's revision (after a regenerate)
  python3 scripts/blog/blog_tools.py publish <slug>      flip draft -> live, drop noindex, sync sitemap + llms.txt
  python3 scripts/blog/blog_tools.py sitemap             sync blog URLs in sitemap.xml from posts.json
  python3 scripts/blog/blog_tools.py llms                regenerate llms.txt from posts.json
"""
import hashlib
import html
import json
import re
import secrets
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
SITE = "https://remedyhomebuyers.net"
APPROVER = "mvorwerk@remedyhomebuyers.net"
NOINDEX = '<meta name="robots" content="noindex"> <!-- draft -->'


def load(name):
    return json.loads((ROOT / name).read_text())


def save(name, data):
    if name == "posts.json":
        # Keep the existing one-post-per-line layout so diffs stay readable.
        rows = ",\n".join("    " + json.dumps(p, ensure_ascii=False) for p in data["posts"])
        rest = {k: v for k, v in data.items() if k != "posts"}
        extra = "".join(f",\n  {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in rest.items())
        text = '{\n  "posts": [\n' + rows + "\n  ]" + extra + "\n}\n"
    else:
        text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    (ROOT / name).write_text(text)


def find_post(posts, slug):
    for p in posts["posts"]:
        if p["slug"] == slug:
            return p
    sys.exit(f"slug not found in posts.json: {slug}")


def post_url(p):
    if p.get("url"):
        return SITE + p["url"].rstrip("/") + "/"
    return f"{SITE}/posts/{p['slug']}.html"


# ---------- check ----------

def check(slug):
    path = ROOT / "posts" / f"{slug}.html"
    src = path.read_text()
    errors, warnings = [], []

    def need(cond, msg):
        (None if cond else errors.append(msg))

    def want(cond, msg):
        (None if cond else warnings.append(msg))

    title = re.search(r"<title>(.*?)</title>", src, re.S)
    need(title, "missing <title>")
    if title:
        n = len(html.unescape(title.group(1)))
        want(30 <= n <= 65, f"<title> is {n} chars (aim 30-65)")
    desc = re.search(r'<meta name="description" content="([^"]*)"', src)
    need(desc, "missing meta description")
    if desc:
        n = len(html.unescape(desc.group(1)))
        want(120 <= n <= 160, f"meta description is {n} chars (aim 120-160)")
    need(f'rel="canonical" href="{SITE}/posts/{slug}.html"' in src, "canonical URL missing or wrong")
    need('property="og:image"' in src, "missing og:image")
    need(src.count("<h1") == 1, f"expected exactly one <h1>, found {src.count('<h1')}")
    h2s = re.findall(r"<h2[^>]*>(.*?)</h2>", src, re.S)
    want(len(h2s) >= 5, f"only {len(h2s)} <h2> sections (aim 5+)")

    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, re.S)
    types = []
    for b in blocks:
        try:
            data = json.loads(b)
        except json.JSONDecodeError as e:
            errors.append(f"invalid JSON-LD: {e}")
            continue
        for item in data.get("@graph", [data]) if isinstance(data, dict) else data:
            types.append(item.get("@type"))
    need("Article" in types or "BlogPosting" in types, "missing Article JSON-LD")
    want("FAQPage" in types, "missing FAQPage JSON-LD (GEO: AI engines lift Q&A pairs)")

    body = re.search(r'<article class="post-body">(.*?)</article>', src, re.S)
    need(body, 'missing <article class="post-body">')
    if body:
        text = re.sub(r"<[^>]+>", " ", body.group(1))
        words = len(text.split())
        want(1400 <= words <= 2600, f"body is {words} words (aim 1,500-2,000)")
        first_p = re.search(r"<p>(.*?)</p>", body.group(1), re.S)
        if first_p:
            n = len(re.sub(r"<[^>]+>", "", first_p.group(1)).split())
            want(n <= 90, f"first paragraph is {n} words; open with a short direct answer (GEO)")
        want('class="key-takeaways"' in src or 'class="tldr"' in src,
             "no key-takeaways / TL;DR box near the top (GEO answer-first)")
        internal = re.findall(r'href="\.\./(cities/[^"]+|posts/[^"]+|[a-z-]+/?)"', body.group(1))
        want(len(internal) >= 2, f"only {len(internal)} internal links to city pages/posts/guides (aim 2+)")
        external = re.findall(r'href="https?://(?!remedyhomebuyers\.net)[^"]+"', body.group(1))
        want(len(external) >= 2, f"only {len(external)} outbound source citations (GEO: cite statutes/.gov, aim 2+)")
        need("(888) 438-0201" in src or "8884380201" in src, "phone number missing from CTA")
    images = load("topic-images.json")
    verified = set(sum(images["by_category"].values(), [])) | {images["fallback"]}
    hero = re.search(r'property="og:image" content="([^"]*)"', src)
    need(not hero or hero.group(1) in verified,
         "header image is not in topic-images.json (unverified images can 404 on the blog)")
    for img in re.findall(r"<img[^>]*>", src):
        if 'alt="' not in img or 'alt=""' in img:
            errors.append(f"image missing alt text: {img[:80]}")

    banned = ["act now", "limited time", "dream home", "forever home", "you'll regret", "60 seconds",
              "no matter what"]
    low = src.lower()
    for b in banned:
        want(not re.search(rf"\b{re.escape(b)}\b", low), f'brand.md "avoid" phrase found: "{b}"')

    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


# ---------- email ----------

def email(slug):
    """Print the approval email. Also stores a fresh review-token hash in posts.json,
    so commit + push posts.json before sending the email."""
    posts = load("posts.json")
    p = find_post(posts, slug)
    rev = p.get("revision", 1)
    token = secrets.token_hex(16)
    p["review_hash"] = hashlib.sha256(token.encode()).hexdigest()
    save("posts.json", posts)
    tag = f"{slug} r{rev}"
    preview = f"{SITE}/posts/{slug}.html"

    def review(action):
        return f"{SITE}/review/?a={action}&s={quote(slug)}&r={rev}&t={token}"

    def mailto(action, body):
        subject = quote(f"BLOG-ACTION: {action} {tag}")
        text = quote(body + "\n\ntoken: " + token)
        return f"mailto:{APPROVER}?subject={subject}&body={text}"

    approve, reject = review("approve"), review("reject")
    btn = ("display:inline-block;padding:14px 28px;border-radius:10px;color:#fff;"
           "text-decoration:none;font-weight:700;font-size:16px;margin:6px")
    esc = html.escape
    revision_note = (f'<p style="color:#5a6675;font-size:14px">Revision {rev}: rewritten from your feedback.</p>'
                     if rev > 1 else "")
    body_html = f"""<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:640px;margin:0 auto;color:#1a2332">
<h2 style="color:#0a2540;margin:0 0 6px">New blog draft ready for review</h2>
{revision_note}
<img src="{esc(p.get('image', ''))}" alt="" style="width:100%;border-radius:12px;margin:12px 0">
<h3 style="color:#0a2540;margin:8px 0">{esc(p['title'])}</h3>
<p style="color:#5a6675">{esc(p.get('excerpt', ''))}</p>
<p><a href="{preview}" style="color:#0a6b43;font-weight:700">Read the full draft &rarr;</a>
<span style="color:#5a6675;font-size:13px">(hidden from the blog until approved)</span></p>
<div style="text-align:center;margin:28px 0">
<a href="{esc(approve)}" style="{btn};background:#0a6b43">&#9989; Approve &amp; Publish</a>
<a href="{esc(reject)}" style="{btn};background:#b42318">&#10060; Reject &amp; Rewrite</a>
</div>
<p style="color:#5a6675;font-size:13px">One click: Approve publishes the post within about an hour.
Reject opens a page where you type what to change; the rewrite is emailed back to you.</p>
<p style="color:#9aa5b1;font-size:12px">Buttons not working? Email instead:
<a href="{esc(mailto('APPROVE', 'Approved - publish it.'))}" style="color:#9aa5b1">approve</a> &middot;
<a href="{esc(mailto('REJECT', 'What should change?'))}" style="color:#9aa5b1">reject</a> &middot; Ref: {esc(tag)}</p>
</div>"""
    text = (f"New blog draft: {p['title']}\nPreview: {preview}\n\n"
            f"Approve: {approve}\nReject: {reject}\n\nRef: {tag}")
    print(json.dumps({"to": [APPROVER], "subject": f"Blog draft for approval: {p['title']} ({tag})",
                      "htmlBody": body_html, "body": text}, indent=2))


def verify(slug, token):
    """Exit 0 if token matches the draft's stored review hash."""
    p = find_post(load("posts.json"), slug)
    ok = bool(p.get("review_hash")) and hashlib.sha256(token.strip().lower().encode()).hexdigest() == p["review_hash"]
    print("valid" if ok else "invalid")
    sys.exit(0 if ok else 1)


# ---------- bump / publish ----------

def bump(slug):
    posts = load("posts.json")
    p = find_post(posts, slug)
    p["revision"] = p.get("revision", 1) + 1
    save("posts.json", posts)
    print(f"{slug} now at revision {p['revision']}")


def publish(slug):
    posts = load("posts.json")
    p = find_post(posts, slug)
    old_date, new_date = p["date"], date.today().isoformat()
    p["date"] = new_date  # show as newest on /#blog
    p["draft"] = False
    p.pop("revision", None)
    p.pop("review_hash", None)
    save("posts.json", posts)

    queue = load("topics-queue.json")
    for t in queue["topics"]:
        if t["slug"] == slug:
            t["status"] = "published"
    save("topics-queue.json", queue)

    path = ROOT / "posts" / f"{slug}.html"
    if path.exists():
        src = path.read_text().replace(NOINDEX + "\n", "").replace(NOINDEX, "")
        src = re.sub(r'"(datePublished|dateModified)": "[^"]*"', rf'"\1": "{new_date}"', src)
        pretty = lambda d: f"{d:%B} {d.day}, {d.year}"
        src = src.replace(f"<span>{pretty(date.fromisoformat(old_date))}</span>",
                          f"<span>{pretty(date.fromisoformat(new_date))}</span>")
        path.write_text(src)
    sitemap()
    llms()
    print(f"published {slug}: {post_url(p)}")


# ---------- sitemap / llms.txt ----------

def sitemap():
    posts = load("posts.json")
    path = ROOT / "sitemap.xml"
    src = path.read_text()
    live = [p for p in posts["posts"] if not p.get("draft")]
    live_urls = {post_url(p) for p in live}
    # Drop existing blog entries (posts/ and vanity articles), keep everything else.
    vanity = {post_url(p) for p in posts["posts"] if p.get("url")}
    lines = [ln for ln in src.splitlines()
             if not ("/posts/" in ln or any(f"<loc>{u}</loc>" in ln or f"<loc>{u.rstrip('/')}</loc>" in ln
                                             for u in vanity))]
    entries = [f"  <url><loc>{post_url(p)}</loc><lastmod>{p['date']}</lastmod>"
               f"<changefreq>monthly</changefreq><priority>0.7</priority></url>"
               for p in sorted(live, key=lambda p: p["date"], reverse=True)]
    close = lines.index("</urlset>")
    lines[close:close] = entries
    path.write_text("\n".join(lines) + "\n")
    print(f"sitemap.xml: {len(live_urls)} blog URLs")


def llms():
    posts = load("posts.json")
    live = sorted([p for p in posts["posts"] if not p.get("draft")], key=lambda p: p["date"], reverse=True)
    out = [
        "# Remedy Home Buyers",
        "",
        "> Direct cash home buyers (not agents). We buy houses as-is, pay all closing costs, charge no "
        "commissions, and can close in as few as 7 days. Founded by Matt Vorwerk. Phone: (888) 438-0201.",
        "",
        "We publish plain-English guides for homeowners in hard situations: foreclosure, inherited property "
        "and probate, divorce, code violations, tenant-occupied sales, tax liens, and state law updates. "
        "Guides are educational, cite primary sources, and are honest about when listing with an agent "
        "is the better option.",
        "",
        "## Key pages",
        f"- [Home and free cash offer]({SITE}/): How our cash offers work (ARV minus repairs, costs, and a fair margin)",
        f"- [Blog]({SITE}/#blog): All homeowner guides",
        "",
        "## Guides",
    ]
    for p in live:
        excerpt = re.sub(r"\s+", " ", p.get("excerpt", "")).strip()
        if len(excerpt) > 200:
            excerpt = excerpt[:197].rsplit(" ", 1)[0] + "..."
        out.append(f"- [{p['title']}]({post_url(p)}): {excerpt}")
    (ROOT / "llms.txt").write_text("\n".join(out) + "\n")
    print(f"llms.txt: {len(live)} guides")


if __name__ == "__main__":
    cmds = {"check": check, "email": email, "bump": bump, "publish": publish, "verify": verify, "sitemap": sitemap, "llms": llms}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    fn = cmds[sys.argv[1]]
    fn(*sys.argv[2:])
