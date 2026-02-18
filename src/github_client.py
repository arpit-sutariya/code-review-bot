import os
import requests
from dataclasses import dataclass


@dataclass
class FileDiff:
    filename: str
    status: str        # added, modified, removed
    patch: str         # the actual diff
    additions: int
    deletions: int
    language: str


class GitHubClient:
    BASE_URL = "https://api.github.com"

    # File extensions we skip (no point reviewing binaries/lockfiles)
    SKIP_EXTENSIONS = {
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf",
        ".zip", ".tar", ".gz", ".lock", ".sum", ".min.js", ".min.css",
    }

    # Max lines per file to send to AI (keeps token usage reasonable)
    MAX_DIFF_LINES = 500

    def __init__(self):
        self.token = os.environ["GITHUB_TOKEN"]
        self.repo = os.environ["REPO_NAME"]
        self.pr_number = int(os.environ["PR_NUMBER"])
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get_pr_diff(self) -> list[FileDiff]:
        """Fetch changed files in the PR and return as FileDiff objects."""
        url = f"{self.BASE_URL}/repos/{self.repo}/pulls/{self.pr_number}/files"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        diffs = []
        for f in response.json():
            filename = f["filename"]

            # Skip deleted files and binary/lock files
            if f["status"] == "removed":
                continue
            if any(filename.endswith(ext) for ext in self.SKIP_EXTENSIONS):
                continue
            if not f.get("patch"):
                continue

            patch = f["patch"]

            # Truncate very large diffs
            lines = patch.splitlines()
            if len(lines) > self.MAX_DIFF_LINES:
                patch = "\n".join(lines[:self.MAX_DIFF_LINES])
                patch += f"\n\n... (truncated — {len(lines) - self.MAX_DIFF_LINES} more lines)"

            diffs.append(FileDiff(
                filename=filename,
                status=f["status"],
                patch=patch,
                additions=f["additions"],
                deletions=f["deletions"],
                language=self._detect_language(filename),
            ))

        return diffs

    def get_pr_metadata(self) -> dict:
        """Fetch PR title and description for context."""
        url = f"{self.BASE_URL}/repos/{self.repo}/pulls/{self.pr_number}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return {
            "title": data["title"],
            "body": data.get("body") or "",
            "author": data["user"]["login"],
            "base_branch": data["base"]["ref"],
            "head_branch": data["head"]["ref"],
            "changed_files": data["changed_files"],
        }

    def post_review_comment(self, body: str) -> None:
        """Post the AI review as a PR comment."""
        url = f"{self.BASE_URL}/repos/{self.repo}/issues/{self.pr_number}/comments"
        response = requests.post(url, headers=self.headers, json={"body": body})
        response.raise_for_status()
        print(f"✅ Review posted to PR #{self.pr_number}")

    def delete_previous_bot_comments(self) -> None:
        """Remove old bot review comments before posting a new one (on re-push)."""
        url = f"{self.BASE_URL}/repos/{self.repo}/issues/{self.pr_number}/comments"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        for comment in response.json():
            if comment["user"]["login"] == "github-actions[bot]" and \
               "🤖 AI Code Review" in comment.get("body", ""):
                delete_url = f"{self.BASE_URL}/repos/{self.repo}/issues/comments/{comment['id']}"
                requests.delete(delete_url, headers=self.headers)
                print(f"🗑️  Deleted old review comment {comment['id']}")

    def _detect_language(self, filename: str) -> str:
        ext_map = {
            ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
            ".jsx": "React/JSX", ".tsx": "React/TSX", ".java": "Java",
            ".cpp": "C++", ".c": "C", ".go": "Go", ".rs": "Rust",
            ".rb": "Ruby", ".php": "PHP", ".cs": "C#", ".swift": "Swift",
            ".kt": "Kotlin", ".sh": "Shell", ".yml": "YAML", ".yaml": "YAML",
            ".sql": "SQL", ".html": "HTML", ".css": "CSS",
        }
        for ext, lang in ext_map.items():
            if filename.endswith(ext):
                return lang
        return "Unknown"
