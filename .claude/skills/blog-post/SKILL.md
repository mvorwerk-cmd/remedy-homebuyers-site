---
name: blog-post
description: Write, revise, check, and publish Remedy Home Buyers blog posts with SEO and GEO (generative engine optimization) built in. Use for any new blog post, a rewrite after rejection feedback, an SEO/GEO pass on an existing post, or running the weekly draft / approval-email / publish automation.
---

# Remedy Home Buyers blog posts (SEO + GEO)

Every post must rank in Google **and** be the source AI answer engines (Google AI Overviews,
ChatGPT search, Perplexity, Copilot) quote and cite. The automation runbook (weekly draft,
approval email, processing Approve/Reject clicks) is in [automation.md](automation.md).

## Before writing

1. Read `brand.md` — voice, values, the "avoid" list. Author is always **Matt Vorwerk**.
2. Read the most recent published file in `posts/` and copy its full HTML shell (head, inline
   `<style>`, nav, hero, image, `<article class="post-body">`, cta-box, footer). Do not invent a
   new layout. Add the extra CSS below once inside `<style>`.
3. Pick the header image from `topic-images.json` (`by_category[<category>]`, else `fallback`).
   Never invent Unsplash IDs. Avoid reusing the image of the previous 2 posts if possible.
4. Research the topic: current state statutes, county/city specifics, fees, timelines. Prefer
   primary sources (state legislature code sites, county court / register of wills pages,
   `.gov` agencies, HUD, CFPB, IRS). Verify every number you state; if you can't verify it,
   leave it out.
   If fetching a source fails (network policy, timeout), use WebSearch and rely on results from
   official domains (`.gov`, state legislature sites) — the search snippet plus URL is an
   acceptable citation. If a specific figure still can't be confirmed, write around it (explain
   the rule and link the official page) instead of stating the number. Never abandon the draft
   because one source is unreachable: finish it and list anything you couldn't verify under
   "Please double-check" at the top of the approval email.

## SEO requirements

- **Slug**: lowercase-hyphenated, `<topic>-<city>-<st>` (e.g. `inherited-house-philadelphia-pa`).
- **`<title>`**: 30–65 chars, primary keyword first, ends `| Remedy Home Buyers` when it fits.
- **Meta description**: 120–160 chars, keyword + concrete benefit, no clickbait.
- **Canonical**, `og:title`, `og:description`, `og:type=article`, `og:url`, `og:image` — all set.
- **One `<h1>`** (the post title). 5+ `<h2>` sections; `<h3>` for sub-points. Phrase many `<h2>`s
  as the questions people actually type ("How long does probate take in Pennsylvania?").
- **Length**: 1,500–2,000 words of body. Short paragraphs (2–4 sentences).
- **Keywords**: primary keyword in title, H1, first 100 words, one H2, meta description, and image
  alt. Use natural variants ("inherited house", "inherited property", "sell a house in probate").
  Never keyword-stuff — it does not help in Google and measurably *hurts* in AI engines.
- **Internal links** (2+, relative `../` paths): the matching `cities/<city>.html` page if one
  exists (`ls cities/`), 1–2 related posts in `posts/`, and/or a guide at a vanity path
  (`../probate-guide/`, `../stopforeclosure/`, `../bypass-probate/`, `../probate-sale/`, …).
- **Images**: descriptive `alt` on every `<img>`.

## GEO requirements (being cited by AI answers)

These come from the generative-engine-optimization research (Aggarwal et al., *GEO*, KDD 2024 —
citing sources, adding statistics, and adding quotations raised visibility in AI answers by
roughly 30–40%; keyword stuffing lowered it) and from current answer-engine practice.

1. **Answer first.** The first paragraph (≤ 90 words) directly answers the title's question in
   plain English. Then a `<div class="key-takeaways">` box with 3–5 one-line bullets — the
   facts an AI summary would lift (timelines, dollar thresholds, statute numbers).
2. **Cite sources inline.** Every legal or numeric claim links to its primary source with an
   outbound link (`target="_blank" rel="noopener"`), e.g. "under
   <a href="https://www.legis.state.pa.us/...">20 Pa.C.S. § 3532</a>". Aim for 4+ citations.
   End the article with a short `<h2>Sources</h2>` list.
3. **Statistics with specifics.** Concrete numbers, dates, and named places beat adjectives:
   "the 4.578% Philadelphia realty transfer tax", not "high transfer taxes".
4. **Quotable, self-contained sentences.** Each section should open with a sentence that makes
   sense if quoted alone ("In Texas, a will can be probated as a muniment of title, which
   transfers the house without appointing an executor."). Define every term the first time.
5. **Expert voice.** Include 1–2 short first-person notes from Matt grounded in what we actually
   see working with sellers ("In our experience…"). Do not fabricate testimonials, client
   stories with specific people, or quotes attributed to real officials.
6. **FAQ section + FAQPage schema.** An `<h2>Frequently Asked Questions</h2>` with 3–5 `<h3>`
   questions and 40–80-word answers, mirrored exactly in a FAQPage JSON-LD block.
7. **Freshness.** Include the year where it matters ("in 2026"); keep `datePublished` /
   `dateModified` accurate.
8. **Comparison tables** where options are compared (agent vs. cash buyer vs. FSBO vs. rent):
   AI engines extract tables well. Use a plain `<table class="compare">`.
9. **Honesty = trust signals.** Say when selling to a cash buyer is *not* the best option
   (brand value). Include the not-legal-advice note and suggest an attorney/HUD counselor.

## Structured data (two JSON-LD blocks in `<head>`)

Keep the existing `Article` block (headline, description, image, datePublished, dateModified,
author Person "Matt Vorwerk", publisher Organization with logo, mainEntityOfPage, keywords),
and add:

```html
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
  {"@type":"Question","name":"<question exactly as the h3>",
   "acceptedAnswer":{"@type":"Answer","text":"<answer exactly as on the page>"}}
]}
</script>
```

## Extra CSS (add inside the post's `<style>`)

```css
.key-takeaways{background:var(--light);border:1px solid var(--border);border-radius:var(--radius);padding:20px 24px;margin:8px 0 32px}
.key-takeaways h2{font-size:18px;margin:0 0 10px}
.key-takeaways ul{margin:0}
table.compare{width:100%;border-collapse:collapse;font-size:15px;margin:0 0 24px}
table.compare th,table.compare td{border:1px solid var(--border);padding:10px;text-align:left;vertical-align:top}
table.compare th{background:var(--light);color:var(--navy)}
```

## Article skeleton

1. Direct-answer intro paragraph (≤ 90 words) + empathetic second paragraph.
2. Key takeaways box.
3. 5–8 `<h2>` sections: the process step by step, state/city specifics, costs and taxes,
   timelines, options (with comparison table), honest trade-offs.
4. FAQ (3–5 Q&As).
5. "Where to start" next steps + city page link.
6. Not-legal-advice note.
7. `<h2>Sources</h2>` list.
8. The standard `cta-box` with "Get My Free Cash Offer →" and `(888) 438-0201` as a
   `tel:8884380201` link (`class="cta-phone"`).

## Drafts

A draft carries `<meta name="robots" content="noindex"> <!-- draft -->` on its own line right
after `<meta name="viewport" …>` so Google doesn't index it before approval. `publish` removes it.

## Check before saving

```bash
python3 scripts/blog/blog_tools.py check <slug>
```

Fix every ERROR. Fix WARNs unless there is a clear reason not to (say why in the email notes).
Also validate the JSON files parse: `python3 -c "import json;json.load(open('posts.json'))"`.

## posts.json entry

Insert at the top of `posts`, one line, same keys as the others:
`slug, title, date (YYYY-MM-DD), author, excerpt (≈ 250–300 chars, plain-English summary
naming the statutes/numbers covered), image, tags ([Category, City, State]), readTime
("N min read", words/220 rounded), draft: true, revision: 1`.

## Publishing

```bash
python3 scripts/blog/blog_tools.py publish <slug>
```

Flips `draft` → false, sets the date to today, removes noindex, marks the topic `published`,
and regenerates the blog URLs in `sitemap.xml` and `llms.txt`. The post then appears on the
site's blog section (`/#blog`) after GitHub Pages redeploys `main` (~1–2 min).
