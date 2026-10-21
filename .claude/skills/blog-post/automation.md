# Blog automation runbook

Two scheduled cloud tasks run this pipeline. Both work on the `main` branch of
`mvorwerk-cmd/remedy-homebuyers-site`: the owner has authorized pushing blog commits directly to
`main` (that is what deploys the site). Never force-push and never rewrite history; always
`git pull --rebase origin main` right before committing.

Approver: **mvorwerk@remedyhomebuyers.net** (Matt Vorwerk). Email is sent from and read in that
Gmail account through the Gmail connector.

## How approval works

The approval email (built by `python3 scripts/blog/blog_tools.py email <slug>`) has two buttons:

- **✅ Approve & Publish** opens a pre-filled email to Matt himself with subject
  `BLOG-ACTION: APPROVE <slug> r<N>`. He presses Send.
- **❌ Reject & Rewrite** opens a pre-filled email with subject
  `BLOG-ACTION: REJECT <slug> r<N>`. He types what should change and presses Send.

`r<N>` is the draft's `revision` in `posts.json`. Only an action matching the current revision
counts, so clicking a button in an old email never publishes an outdated version.

## Task 1: weekly draft (Mondays)

1. Sync: `git checkout main && git pull --rebase origin main`.
2. Open `topics-queue.json`, take the first topic with `"status": "queued"`. If none are left,
   append 12 new topics following the file's `description` (mix of distress topics, state law
   updates and how-to guides across US metros, slugs not already in `posts/`), then take the first.
3. Write the post following `SKILL.md` (all SEO + GEO requirements, draft noindex meta).
4. Add the `posts.json` entry (`draft: true`, `revision: 1`) and set the topic `"status": "drafted"`.
5. `python3 scripts/blog/blog_tools.py check <slug>`: fix all errors and as many warnings as possible.
6. Commit `posts/<slug>.html`, `posts.json`, `topics-queue.json` with message
   `Draft: <title>` and push to `main`.
7. `python3 scripts/blog/blog_tools.py email <slug>` prints JSON `{to, subject, htmlBody, body}`.
   Send it with the Gmail `send_message` tool (`to`, `subject`, `htmlBody`, `body` as given).

## Task 2: process actions (hourly)

1. Sync `main` as above.
2. Make sure the Gmail label `blog-processed` exists (`list_labels`, else `create_label`).
3. Search Gmail:
   `from:mvorwerk@remedyhomebuyers.net subject:"BLOG-ACTION" -label:blog-processed newer_than:30d`
   Read each thread with `get_thread` and collect messages whose subject matches
   `BLOG-ACTION: (APPROVE|REJECT) <slug> r<N>` and whose sender is exactly
   `mvorwerk@remedyhomebuyers.net`. Ignore anything else (e.g. old Zapier emails from
   `help@remedyhomebuyers.net`). Handle them oldest first.
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
     changed; run `python3 scripts/blog/blog_tools.py bump <slug>`, then `check`. Commit as
     `Revise: <slug> r<N+1>`, push to `main`, then send the new approval email (from `email <slug>`),
     adding at the top a short "What changed" list mapping each feedback point to the edit.
   - Matt can reject as many times as he likes; each rejection produces a new revision.
5. Label every handled message `blog-processed` (`label_message`) **after** its push succeeds,
   so a failed run is retried next hour.
6. If nothing matched, end quietly: no emails, no commits.

## Failure handling

- Push rejected → `git pull --rebase origin main` and retry once; if it still fails, email Matt
  what failed and leave the action unlabeled.
- Never publish a post whose `check` has ERRORs; fix them first.
