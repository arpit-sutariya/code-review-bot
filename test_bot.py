import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from github_client import GitHubClient, FileDiff
from ai_provider import build_review_prompt


# ─── GitHubClient unit tests ─────────────────────────────────────────────────

class TestLanguageDetection:
    def setup_method(self):
        # Set dummy env vars so GitHubClient can be instantiated
        os.environ.setdefault("GITHUB_TOKEN", "test")
        os.environ.setdefault("REPO_NAME", "owner/repo")
        os.environ.setdefault("PR_NUMBER", "1")
        self.client = GitHubClient()

    def test_detects_python(self):
        assert self.client._detect_language("main.py") == "Python"

    def test_detects_javascript(self):
        assert self.client._detect_language("app.js") == "JavaScript"

    def test_detects_typescript(self):
        assert self.client._detect_language("index.ts") == "TypeScript"

    def test_detects_go(self):
        assert self.client._detect_language("server.go") == "Go"

    def test_unknown_extension(self):
        assert self.client._detect_language("Makefile") == "Unknown"

    def test_detects_yaml(self):
        assert self.client._detect_language("docker-compose.yml") == "YAML"


class TestSkipExtensions:
    def setup_method(self):
        os.environ.setdefault("GITHUB_TOKEN", "test")
        os.environ.setdefault("REPO_NAME", "owner/repo")
        os.environ.setdefault("PR_NUMBER", "1")
        self.client = GitHubClient()

    def test_skips_png(self):
        assert ".png" in self.client.SKIP_EXTENSIONS

    def test_skips_lock_files(self):
        assert ".lock" in self.client.SKIP_EXTENSIONS

    def test_skips_minified_js(self):
        assert ".min.js" in self.client.SKIP_EXTENSIONS


# ─── Prompt builder tests ─────────────────────────────────────────────────────

class TestBuildReviewPrompt:
    def setup_method(self):
        self.diffs = [
            FileDiff(
                filename="app.py",
                status="modified",
                patch="@@ -1,3 +1,5 @@\n def foo():\n-    pass\n+    x = 1/0\n+    return x",
                additions=2,
                deletions=1,
                language="Python",
            )
        ]
        self.metadata = {
            "title": "Fix authentication bug",
            "author": "testuser",
            "body": "Fixes a critical auth issue",
            "base_branch": "main",
            "head_branch": "fix/auth",
            "changed_files": 1,
        }

    def test_prompt_contains_pr_title(self):
        prompt = build_review_prompt(self.diffs, self.metadata)
        assert "Fix authentication bug" in prompt

    def test_prompt_contains_filename(self):
        prompt = build_review_prompt(self.diffs, self.metadata)
        assert "app.py" in prompt

    def test_prompt_contains_diff(self):
        prompt = build_review_prompt(self.diffs, self.metadata)
        assert "1/0" in prompt

    def test_prompt_contains_author(self):
        prompt = build_review_prompt(self.diffs, self.metadata)
        assert "testuser" in prompt

    def test_prompt_contains_language(self):
        prompt = build_review_prompt(self.diffs, self.metadata)
        assert "Python" in prompt

    def test_empty_diffs_still_builds(self):
        prompt = build_review_prompt([], self.metadata)
        assert "Fix authentication bug" in prompt

    def test_prompt_contains_branch_info(self):
        prompt = build_review_prompt(self.diffs, self.metadata)
        assert "fix/auth" in prompt
        assert "main" in prompt
