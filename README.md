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

Two scheduled Claude tasks running on the owner's Mac:

### `weekly-blog-post`
Runs every Monday at 9 AM local. For each run:
1. Reads `topics-queue.json` → picks the first `status: "queued"` topic
2. Reads `brand.md` for voice + `topic-images.json` for image selection
3. Generates a 1,500–2,000 word SEO-optimized post in the established blog template
4. Commits 3 files via Zapier MCP (GitHub: Create or Update File):
   - `posts/{slug}.html` (new)
   - `posts.json` (updated with new entry, `draft: true`)
   - `topics-queue.json` (topic marked `drafted`)
5. Emails Matt the draft with `✅ Approve & Publish` and `❌ Reject & Discard` buttons

### `blog-action-processor`
Runs every 15 minutes. Scans Gmail for emails with subject `BLOG-ACTION:` (sent by the approve/reject Zap when buttons are clicked). For each:
- `APPROVE` → flips `draft: false` in `posts.json`, marks topic `published` in `topics-queue.json`
- `REJECT` → removes the entry from `posts.json`, marks topic `rejected` in `topics-queue.json`
- Sends Matt a confirmation email

If you don't click either button, the draft sits indefinitely with `draft: true` (invisible on `/#blog`).

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
