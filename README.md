# 🤖 AI Code Review Bot

A GitHub Actions bot that automatically reviews every Pull Request using AI — detecting bugs, performance issues, and style violations, then posting a structured review comment directly on the PR.

Supports both **Anthropic (Claude)** and **OpenAI (GPT-4o)** — switchable with a single config variable.

---

## 📸 Example Review Output

```
## 🤖 AI Code Review

### Summary
This PR adds a user authentication endpoint. The overall structure is clean,
but there is a critical division-by-zero risk and one minor naming issue.

### Issues Found

**`auth.py`** — Potential ZeroDivisionError
- **Severity:** 🔴 Critical
- **Problem:** `rate = requests / elapsed` will crash if elapsed is 0 on first call
- **Fix:**
  elapsed = max(time.time() - start_time, 0.001)
  rate = requests / elapsed

**`utils.py`** — Unclear variable name
- **Severity:** 🟢 Suggestion
- **Problem:** `x2` is not descriptive — consider `retry_count`

### ✅ What Looks Good
- JWT expiry logic is correctly implemented
- Password hashing uses bcrypt with appropriate cost factor

### Final Verdict
Request Changes
```

---

## ⚙️ How It Works

```
PR Opened / Updated
       ↓
GitHub Actions Triggered
       ↓
Fetch PR diff via GitHub API
       ↓
Build structured prompt with diff + PR metadata
       ↓
Send to Claude or GPT-4o
       ↓
Post review as PR comment
```

---

## 🚀 Setup — Add to Any Repo in 3 Steps

### Step 1 — Copy the workflow file
Copy `.github/workflows/code-review.yml` into your repository.

### Step 2 — Add your API key as a GitHub Secret
Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `OPENAI_API_KEY` | Your OpenAI API key (if using OpenAI) |

### Step 3 — Set your preferred AI provider
Go to **Settings → Secrets and variables → Actions → Variables → New repository variable**

| Variable | Value |
|---|---|
| `AI_PROVIDER` | `anthropic` or `openai` (default: `anthropic`) |

That's it. Open a PR and the bot will review it automatically.

---

## 📁 Project Structure

```
code-review-bot/
├── .github/
│   └── workflows/
│       ├── code-review.yml   # Triggered on every PR open/update
│       └── tests.yml         # Runs pytest on push to main
├── src/
│   ├── main.py               # Orchestrates the full review flow
│   ├── github_client.py      # GitHub API — fetch diffs, post comments
│   └── ai_provider.py        # Anthropic + OpenAI providers + prompt builder
├── tests/
│   └── test_bot.py           # Unit tests for core logic
├── requirements.txt
└── README.md
```

---

## 🔍 What It Reviews

| Category | Examples |
|---|---|
| 🐛 Bugs & Logic Errors | Off-by-one, null handling, unhandled exceptions, race conditions |
| 🎨 Code Style | Naming, DRY violations, function length, missing docstrings |
| ⚡ Performance | N+1 queries, unnecessary loops, inefficient data structures |

---

## 🛠️ Local Development

```bash
git clone https://github.com/your-username/code-review-bot.git
cd code-review-bot
pip install -r requirements.txt

# Run tests
pytest tests/ -v
```

To test the bot locally against a real PR:
```bash
export GITHUB_TOKEN=your_token
export ANTHROPIC_API_KEY=your_key
export AI_PROVIDER=anthropic
export REPO_NAME=owner/repo
export PR_NUMBER=1
export BASE_SHA=abc123
export HEAD_SHA=def456

cd src && python main.py
```

---

## 🤝 Using This in Your Own Project

This bot is designed to be dropped into any existing GitHub repository — it does not require any changes to your codebase. Just add the workflow file and secrets.

---

## 📄 License

MIT
# test
