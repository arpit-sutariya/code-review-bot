import os
from abc import ABC, abstractmethod


SYSTEM_PROMPT = """You are an expert code reviewer with deep knowledge across all programming languages and software engineering best practices. Your job is to review code diffs from pull requests.

You review for THREE things only:
1. **Bugs & Logic Errors** — off-by-one errors, null/undefined handling, incorrect conditions, race conditions, unhandled exceptions
2. **Code Style & Best Practices** — naming conventions, function length, DRY violations, unclear code, missing docstrings on public APIs
3. **Performance Issues** — unnecessary loops, N+1 queries, inefficient data structures, missing indexes, memory leaks

IMPORTANT RULES:
- Only comment on the NEW code (lines starting with +), not removed lines (-)
- Be specific — reference the exact line or function
- Be constructive and actionable — always suggest the fix, not just the problem
- If code is clean, say so clearly — do not invent issues
- Prioritize issues: 🔴 Critical, 🟡 Minor, 🟢 Suggestion
- Skip comments about missing tests unless the change is clearly untested risky logic
- Keep your tone like a friendly senior engineer, not a harsh critic
"""

def build_review_prompt(diffs, pr_metadata) -> str:
    """Build the full review prompt from PR metadata and file diffs."""
    files_section = ""
    for diff in diffs:
        files_section += f"""
### `{diff.filename}` ({diff.language}) — +{diff.additions}/-{diff.deletions}
```diff
{diff.patch}
```
"""

    return f"""Please review this pull request.

**PR Title:** {pr_metadata['title']}
**Author:** {pr_metadata['author']}
**Branch:** `{pr_metadata['head_branch']}` → `{pr_metadata['base_branch']}`
**Description:** {pr_metadata['body'] or 'No description provided.'}
**Files changed:** {pr_metadata['changed_files']}

---

## Changed Files
{files_section}

---

Provide your review in this exact markdown format:

## 🤖 AI Code Review

### Summary
[2-3 sentence overview of what this PR does and your overall impression]

### Issues Found

[For each issue use this format:]
**`filename.py`** — [Issue title]
- **Severity:** 🔴 Critical / 🟡 Minor / 🟢 Suggestion
- **Problem:** [What's wrong]
- **Fix:**
```language
[corrected code snippet]
```

### ✅ What Looks Good
[Briefly mention 1-3 things done well — specific functions or patterns]

### Final Verdict
[One line: Approve / Request Changes / Needs Discussion]

If there are zero issues, say so clearly and approve. Do not manufacture problems.
"""


# ─── Base class ──────────────────────────────────────────────────────────────

class AIProvider(ABC):
    @abstractmethod
    def review(self, prompt: str) -> str:
        pass


# ─── Anthropic ───────────────────────────────────────────────────────────────

class AnthropicProvider(AIProvider):
    MODEL = "claude-opus-4-6"

    def review(self, prompt: str) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        message = client.messages.create(
            model=self.MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text


# ─── OpenAI ──────────────────────────────────────────────────────────────────

class OpenAIProvider(AIProvider):
    MODEL = "gpt-4o"

    def review(self, prompt: str) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model=self.MODEL,
            max_tokens=4096,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content


# ─── Factory ─────────────────────────────────────────────────────────────────

def get_ai_provider() -> AIProvider:
    """Return the correct AI provider based on the AI_PROVIDER env var."""
    provider = os.environ.get("AI_PROVIDER", "anthropic").lower()

    if provider == "anthropic":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY is not set")
        print("🧠 Using Anthropic (Claude)")
        return AnthropicProvider()

    elif provider == "openai":
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is not set")
        print("🧠 Using OpenAI (GPT-4o)")
        return OpenAIProvider()

    else:
        raise ValueError(f"Unknown AI_PROVIDER: '{provider}'. Use 'anthropic' or 'openai'.")
