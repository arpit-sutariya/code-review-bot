import sys
import os
from github_client import GitHubClient
from ai_provider import get_ai_provider, build_review_prompt


def main():
    print("🚀 Starting AI Code Review...")

    # ── 1. Init GitHub client ────────────────────────────────────────────────
    github = GitHubClient()

    # ── 2. Fetch PR metadata and diff ────────────────────────────────────────
    print("📥 Fetching PR metadata...")
    pr_metadata = github.get_pr_metadata()
    print(f"   PR: '{pr_metadata['title']}' by @{pr_metadata['author']}")

    print("📂 Fetching changed files...")
    diffs = github.get_pr_diff()

    if not diffs:
        print("⚠️  No reviewable files found (all files were deleted or binary). Skipping review.")
        github.post_review_comment(
            "## 🤖 AI Code Review\n\n"
            "No reviewable source files found in this PR "
            "(files may be binary, deleted, or lock files). Skipping review."
        )
        return

    print(f"   Found {len(diffs)} file(s) to review:")
    for d in diffs:
        print(f"   • {d.filename} ({d.language}) +{d.additions}/-{d.deletions}")

    # ── 3. Build prompt ───────────────────────────────────────────────────────
    print("📝 Building review prompt...")
    prompt = build_review_prompt(diffs, pr_metadata)
    print(f"   Prompt length: {len(prompt)} characters")

    # ── 4. Run AI review ──────────────────────────────────────────────────────
    print("🤖 Running AI review...")
    provider = get_ai_provider()
    review = provider.review(prompt)
    print("   Review generated successfully.")

    # ── 5. Post to GitHub ─────────────────────────────────────────────────────
    print("💬 Posting review to GitHub...")
    github.delete_previous_bot_comments()

    # Append a small footer
    footer = (
        "\n\n---\n"
        f"*Reviewed by AI Code Review Bot · "
        f"Provider: `{os.environ.get('AI_PROVIDER', 'anthropic')}` · "
        f"{len(diffs)} file(s) reviewed*"
    )
    github.post_review_comment(review + footer)
    print("✅ Done!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
