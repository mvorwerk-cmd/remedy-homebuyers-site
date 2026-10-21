# Remedy Home Buyers — Marketing Site

Static marketing site for [remedyhomebuyers.net](https://remedyhomebuyers.net). Deployed via GitHub Pages from the `main` branch.

> **Tagline:** Sell Smart. Live Easy.

## Repository Structure

```
remedy-homebuyers-site/
├── index.html              # Main SPA — home, how it works, success stories, FAQ, blog, offer form
├── logo.png                # Site logo (used in nav, footer, favicon, OG image)
├── CNAME                   # Custom domain config (remedyhomebuyers.net)
├── robots.txt              # SEO crawler rules
├── sitemap.xml             # SEO sitemap
│
├── brand.md                # Mission, values, voice — source-of-truth for all content
├── topics-queue.json       # Upcoming blog topics for the weekly automation
├── topic-images.json       # Verified-working Unsplash URLs by topic category
│
├── posts.json              # Manifest of all blog posts shown on /#blog
├── posts/                  # Long-form blog post HTML files
│   └── {slug}.html
│
├── cities/                 # 100+ city landing pages for local SEO
│   └── {city-slug}.html
│
├── google/                 # Redirect to Google Reviews
├── schedule/               # Redirect to Calendly
│
├── rehab/, eap/, stopforeclosure/, badagent/, equity/,
├── probate-guide/, bypass-probate/, probate-sale/, probate-rent/,
├── repair/, tenant/, vacant/   # 12 drip-campaign articles at vanity paths
│
└── .gitignore
```

## Deployment

Pushes to `main` are auto-deployed by GitHub Pages within ~1–2 minutes.

### Local push workflow

```bash
cd /Users/rezielmartinez/RemedyHomeBuyers/remedy-homebuyers-site
# Make changes...
git add <files>
git commit -m "What you changed"
git pull --rebase --autostash    # always pull first — automation commits to main too
git push
```

The `--rebase --autostash` flow keeps history clean and avoids merge commits when the scheduled blog automation has also pushed.

## Form → Lead Pipeline

Both forms (`heroForm` in the hero, `offerForm` on the offer page) post to a Zapier webhook (`hooks.zapier.com/hooks/catch/17291088/2numbkl/`).

The Zap:
1. Catches the submission
2. Filters by `Source` field — only `remedyhomebuyers.net` continues (blocks rogue traffic from copied templates)
3. Creates a Lead in REsimpli CRM with structured Street / City / State / ZIP fields
4. Appends a row to a Google Sheet for backup

Both forms include a hidden **honeypot field** (`name="website"`). If filled, the submission is silently dropped client-side without firing the webhook — blocks the majority of bot abuse.

## Blog Automation

Runs as two scheduled Claude Code cloud tasks (no laptop needs to be on). Full runbook:
[`.claude/skills/blog-post/automation.md`](.claude/skills/blog-post/automation.md). Writing rules
(SEO + GEO) live in [`.claude/skills/blog-post/SKILL.md`](.claude/skills/blog-post/SKILL.md).

### Weekly draft — Mondays ~8:45 AM Pacific
1. Picks the first `queued` topic in `topics-queue.json`
2. Writes a 1,500–2,000 word post following `brand.md` and the SEO/GEO skill
3. Commits `posts/{slug}.html` + `posts.json` (`draft: true`, hidden from `/#blog`, `noindex`) to `main`
4. Emails Matt the draft with **✅ Approve & Publish** and **❌ Reject & Rewrite** buttons

### Action processor — hourly
The buttons are one click: they open `/review/` on the site, which posts to the private Zapier
workflow **blog-review-buttons**; it emails `BLOG-ACTION: APPROVE|REJECT {slug} r{N}` (with a
one-time token checked against `review_hash` in `posts.json`) to Matt's inbox for the processor.
- `APPROVE` → `scripts/blog/blog_tools.py publish` flips `draft: false`, updates `sitemap.xml` and `llms.txt`, pushes to `main`, emails a confirmation
- `REJECT` → rewrites the post using Matt's notes, bumps the revision, emails the new draft — repeats until approved

### Helper script
```bash
python3 scripts/blog/blog_tools.py check <slug>    # SEO/GEO lint
python3 scripts/blog/blog_tools.py publish <slug>  # publish a draft manually
python3 scripts/blog/blog_tools.py sitemap         # resync blog URLs in sitemap.xml
```

## Editing Common Files

| File | What you'd change | When |
|---|---|---|
| `topics-queue.json` | Add new topic+city ideas | Anytime — automation picks the next `queued` one |
| `brand.md` | Update mission/voice/values | When brand evolves |
| `topic-images.json` | Add/swap verified Unsplash URLs by category | When you want fresher imagery |
| `posts.json` | Manual edit only for drafts you want to publish/discard outside the automation flow | Rare |
| `index.html` | Site structure, nav, hero, footer, forms | When changing the homepage SPA |

## Meta (Facebook) Pixel

**Pixel ID:** `38058926033723355` (active — installed across `index.html` and all 12 vanity-path pages)

Events tracked:
- **PageView** — fires on every route
- **Lead** — fires on successful form submission (hero form + offer form) with payload `{content_name: <formId>, source: 'remedyhomebuyers.net'}`. Honeypot bot submissions do NOT fire it.

### For the FB ads specialist

Recommended follow-ups after being invited to the repo:

1. Verify events in [Meta Events Manager → Test Events](https://business.facebook.com/events_manager). Load `remedyhomebuyers.net`, submit the hero form with a test address, confirm `PageView` + `Lead` fire.
2. Complete **Domain Verification** for `remedyhomebuyers.net` in Meta Business Manager → Brand Safety.
3. Set up **Aggregated Event Measurement** — prioritize `Lead` as the highest-value event for iOS 14+ attribution.
4. Optional: add **Conversions API** (server-side) by extending the existing Zap that pushes to REsimpli to also POST to Meta's CAPI endpoint. This recovers lost attribution from ad blockers and iOS.
5. If you want richer events (`ViewContent` on blog posts, `InitiateCheckout` on "Get Offer" click), the pixel snippet is in `<head>` of `index.html` — add `fbq('track', ...)` calls where relevant.

## Vanity Redirect URLs

| URL | Redirects to |
|---|---|
| `/google` | Google Reviews page |
| `/schedule` | Matt's Calendly |

Used in drip campaigns, SMS, business cards.

## Contact

**Matt Vorwerk**
Email: mvorwerk@remedyhomebuyers.net
Phone: (888) 438-0201
Office: 1401 21st Street Suite R, Sacramento, CA 95811
