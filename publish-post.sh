#!/usr/bin/env bash
# publish-post.sh — Interactively flip a blog post's draft flag to false
# and push the change to GitHub. Replaces the flaky scheduled-task automation.
#
# Usage:
#   cd /Users/rezielmartinez/RemedyHomeBuyers/remedy-homebuyers-site
#   ./publish-post.sh
#
# Requires: git (already configured), jq (install with: brew install jq)

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

# Check jq is installed
if ! command -v jq >/dev/null 2>&1; then
  echo "❌ jq is not installed. Install with:  brew install jq"
  exit 1
fi

# Sync with remote
echo "→ Pulling latest from GitHub..."
git pull --rebase --autostash >/dev/null 2>&1 || {
  echo "❌ git pull failed. Fix conflicts and retry."
  exit 1
}

# List all drafts
DRAFTS_JSON=$(jq -r '[.posts[] | select(.draft == true) | {slug, title, date}]' posts.json)
DRAFT_COUNT=$(echo "$DRAFTS_JSON" | jq 'length')

if [ "$DRAFT_COUNT" -eq 0 ]; then
  echo "✓ No drafts pending. Nothing to publish."
  exit 0
fi

echo ""
echo "Pending drafts:"
echo "---------------"
echo "$DRAFTS_JSON" | jq -r 'to_entries[] | "  [\(.key + 1)] \(.value.date)  \(.value.slug)\n      \(.value.title)"'
echo ""

# Prompt selection
read -rp "Enter number to publish (or 0 to cancel): " CHOICE

if [ "$CHOICE" = "0" ] || [ -z "$CHOICE" ]; then
  echo "Cancelled."
  exit 0
fi

# Validate choice
if ! [[ "$CHOICE" =~ ^[0-9]+$ ]] || [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -gt "$DRAFT_COUNT" ]; then
  echo "❌ Invalid choice."
  exit 1
fi

# Extract selected slug
INDEX=$((CHOICE - 1))
SELECTED_SLUG=$(echo "$DRAFTS_JSON" | jq -r ".[$INDEX].slug")
SELECTED_TITLE=$(echo "$DRAFTS_JSON" | jq -r ".[$INDEX].title")

echo ""
echo "→ Publishing: $SELECTED_TITLE"
echo "  Slug: $SELECTED_SLUG"

# Flip draft to false in posts.json (preserve everything else)
jq --arg slug "$SELECTED_SLUG" \
   '(.posts[] | select(.slug == $slug) | .draft) = false' \
   posts.json > posts.json.tmp && mv posts.json.tmp posts.json

# Also update topics-queue.json if the slug matches a topic there
if jq --arg slug "$SELECTED_SLUG" '.topics[] | select(.slug == $slug)' topics-queue.json >/dev/null 2>&1; then
  jq --arg slug "$SELECTED_SLUG" \
     '(.topics[] | select(.slug == $slug) | .status) = "published"' \
     topics-queue.json > topics-queue.json.tmp && mv topics-queue.json.tmp topics-queue.json
  echo "  Also marked topic 'published' in topics-queue.json"
fi

# Commit and push
echo "→ Committing and pushing..."
git add posts.json topics-queue.json
git commit -m "Publish: $SELECTED_TITLE" >/dev/null
git push >/dev/null 2>&1 || {
  echo "❌ git push failed. Run 'git push' manually to see the error."
  exit 1
}

echo ""
echo "✅ Published! Live at:"
echo "   https://remedyhomebuyers.net/posts/$SELECTED_SLUG.html"
echo ""
echo "   Blog index will refresh in ~1-2 minutes."
