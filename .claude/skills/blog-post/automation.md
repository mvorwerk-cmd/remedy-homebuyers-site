# Blog automation runbook

Two scheduled cloud tasks run this pipeline. Both work on the `main` branch of
`mvorwerk-cmd/remedy-homebuyers-site`: the owner has authorized pushing blog commits directly to
`main` (that is what deploys the site). Never force-push and never rewrite history; always
`git pull --rebase origin main` right before committing.

Approver: **mvorwerk@remedyhomebuyers.net** (Matt Vorwerk). Email is sent from and read in that
Gmail account through the Gmail connector.

## How approval works

The approval email (built by `python3 scripts/blog/blog_tools.py email <slug>`) has two one-click
buttons that open `https://remedyhomebuyers.net/review/` (`review/index.html`):

- **✅ Approve & Publish**: the page immediately posts the click to the Zapier workflow
  `blog-review-buttons`, which emails `BLOG-ACTION: APPROVE <slug> r<N>` (body `token: <hex>`)
  from help@remedyhomebuyers.net to Matt's inbox.
- **❌ Reject & Rewrite**: the page shows a feedback box; on Send the same workflow emails
  `BLOG-ACTION: REJECT <slug> r<N>` with the token and Matt's feedback.

`email` generates a random token per email and stores only its SHA-256 as `review_hash` on the
draft in `posts.json` (public file, so never the raw token). **Commit and push `posts.json`
after running `email` and before sending the email**, or the token can't be verified.
A small "Buttons not working? Email instead" fallback sends the same subject via mailto.

`r<N>` is the draft's `revision`. Only an action matching the current revision counts, so a
button in an old email never publishes an outdated version.

## Task 1: weekly draft (Mondays)

1. Sync: `git checkout main && git pull --rebase origin main`.
2. Open `topics-queue.json`, take the first topic with `"status": "queued"`. If none are left,
   append 12 new topics following the file's `description` (mix of distress topics, state law
   updates and how-to guides across US metros, slugs not already in `posts/`), then take the first.
3. Write the post following `SKILL.md` (all SEO + GEO requirements, draft noindex meta).
4. Add the `posts.json` entry (`draft: true`, `revision: 1`) and set the topic `"status": "drafted"`.
5. `python3 scripts/blog/blog_tools.py check <slug>`: fix all errors and as many warnings as possible.
6. `python3 scripts/blog/blog_tools.py email <slug> > /tmp/email.json` (prints JSON
   `{to, subject, htmlBody, body}` and writes `review_hash` into posts.json).
7. Commit `posts/<slug>.html`, `posts.json`, `topics-queue.json` with message
   `Draft: <title>` and push to `main`. Then send /tmp/email.json with the Gmail `send_message` tool (`to`, `subject`, `htmlBody`, `body` as given).
   If any facts couldn't be verified (see SKILL.md research step), insert a short
   "Please double-check" list right after the first `<h2>` of `htmlBody` before sending.

## Task 2: process actions (hourly)

1. Sync `main` as above.
2. Make sure the Gmail label `blog-processed` exists (`list_labels`, else `create_label`).
3. Search Gmail:
   `subject:"BLOG-ACTION" -label:blog-processed newer_than:30d`
   Read each thread with `get_thread` and collect messages whose subject matches
   `BLOG-ACTION: (APPROVE|REJECT) <slug> r<N>`. An action is **authentic** only if either:
   - its body contains `token: <32 hex>` and
     `python3 scripts/blog/blog_tools.py verify <slug> <token>` prints `valid`, or
   - it has no token, the sender is exactly `mvorwerk@remedyhomebuyers.net`, and it was sent by
     Matt himself (mailto fallback / older emails).
   Label anything inauthentic `blog-processed` and ignore it. Handle authentic ones oldest first.
   (Run this after step 1's sync so `verify` sees the latest posts.json.)
4. For each action, look up `<slug>` in `posts.json`:
   - Not found, already `draft: false`, or `revision` ≠ N → stale. Label it `blog-processed`, skip.
   - **APPROVE**:
     `python3 scripts/blog/blog_tools.py publish <slug>`, commit
     `posts.json topics-queue.json sitemap.xml llms.txt posts/<slug>.html` as `Publish: <title>`,
     push to `main`. Email Matt a short confirmation with the live link
     `https://remedyhomebuyers.net/posts/<slug>.html` (live on the blog in ~2 minutes).
   - **REJECT**: the feedback is the message body (ignore the pre-filled prompt line and quoted
     text). If it is empty, rewrite for overall quality and say so. Rewrite
     `posts/<slug>.html` addressing **every** point while keeping all SKILL.md requirements, the
     same slug and the draft noindex meta; update the `posts.json` title/excerpt/readTime if they
     changed; run `python3 scripts/blog/blog_tools.py bump <slug>`, `check`, then `email <slug>`. Commit as
     `Revise: <slug> r<N+1>` together with the posts.json written by `email <slug>` (run it after
     `bump`), push to `main`, then send that new approval email,
     adding at the top a short "What changed" list mapping each feedback point to the edit.
   - Matt can reject as many times as he likes; each rejection produces a new revision.
5. Label every handled message `blog-processed` (`label_message`) **after** its push succeeds,
   so a failed run is retried next hour.
6. If nothing matched, end quietly: no emails, no commits.

## Failure handling

- Push rejected → `git pull --rebase origin main` and retry once; if it still fails, email Matt
  what failed and leave the action unlabeled.
- Never publish a post whose `check` has ERRORs; fix them first.
