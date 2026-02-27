# AI Commit Message Critic

A terminal tool that uses AI to review your git commit messages — like having a Staff Engineer audit your commit hygiene.

Point it at any repo (local or remote) and it scores every commit, calls out the lazy ones, and explains why the good ones work. It can also read your staged changes and write the commit message for you.

### Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your OpenRouter key
python commit_critic.py --analyze
```

## Why?

Bad commit messages are tech debt nobody talks about. When something breaks at 2am and you're running `git bisect`, the difference between `"fix bug"` and `"fix(auth): resolve token expiration causing silent logouts"` is the difference between a 10-minute fix and a 2-hour investigation.

This tool makes that visible.

## Getting Started

### Prerequisites

- **Python 3.11+** — check with `python3 --version`
- **git** — installed and available on your PATH
- **OpenRouter account** — sign up at [openrouter.ai](https://openrouter.ai) and grab an API key from [openrouter.ai/keys](https://openrouter.ai/keys)

### Step-by-step setup

1. **Clone the repo** (skip if you already have it):
   ```bash
   git clone https://github.com/your-user/ai_commit_message_challenge.git
   cd ai_commit_message_challenge
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure your API key:**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` so it looks like this:
   ```
   OPENROUTER_API_KEY=sk-or-v1-abc123...your-key-here
   ```

4. **Verify it works:**
   ```bash
   python commit_critic.py --analyze
   ```
   You should see your repo's last 50 commits scored and grouped.

## Usage

### Analyze the current repo

Score the last 50 commits in whatever repo you're currently in:

```bash
python commit_critic.py --analyze
```

### Analyze a remote repo

Point it at any public GitHub repo — it clones temporarily and analyzes:

```bash
python commit_critic.py --analyze --url="https://github.com/steel-dev/steel-browser"
```

### Let AI write your commit message

Stage your changes first, then let the tool generate a conventional commit message. You can accept the suggestion or type your own — either way, it commits for you.

```bash
git add .
python commit_critic.py --write
```

The flow:
1. Stage files with `git add`
2. Run `--write` — the tool reads your diff and suggests a message
3. Press **Enter** to accept, or type your own message
4. The tool commits with the chosen message

If you have no staged changes, you'll see: `No staged changes found. Stage files with git add first.`

### Swapping models

By default the tool uses `google/gemini-2.5-flash`. To use a different model, set `COMMIT_CRITIC_MODEL` in your `.env` file to any model ID from [OpenRouter's catalog](https://openrouter.ai/models):

```
COMMIT_CRITIC_MODEL=anthropic/claude-sonnet-4
```

## Example: Analyzing Steel Browser

Here's what it looks like when you point it at a real repo:

```
$ python commit_critic.py --analyze --url="https://github.com/steel-dev/steel-browser"

Analyzing last 50 commits...

────────────────────────────────────────────────────────────────────────────────
💩 COMMITS THAT NEED WORK
────────────────────────────────────────────────────────────────────────────────

Commit: "docs: update README.md (#248)"
Score: 4/10
Issue: This commit message is too generic; it indicates a documentation
update but not *what* was updated or *why*.
Better: "docs: clarify installation instructions in README.md"

Commit: "fix: remove arrounious extensionsPath"
Score: 3/10
Issue: This commit is incomplete and highly ambiguous. 'arrounious' is
misspelled, and 'extensionsPath' gives no context.
Better: "fix: remove erroneous or unused extensionsPath configuration to
prevent loading incorrect paths"

────────────────────────────────────────────────────────────────────────────────
💎 WELL-WRITTEN COMMITS
────────────────────────────────────────────────────────────────────────────────

Commit: "perf: pre-compile URL pattern regexes at session start (#252)"
Score: 9/10
Why it's good: This commit clearly states the type of change (performance
improvement) and what action was taken, linking directly to the impact:
reducing runtime compilation overhead.

Commit: "fix: circular reference stack overflow in event storage (#251)"
Score: 9/10
Why it's good: This commit clearly identifies a bug type and its specific
manifestation (stack overflow), making it easy to understand the fix's
purpose and scope.

Commit: "fix: Polyfill `__name` to prevent esbuild errors in Puppeteer context (#184)"
Score: 9/10
Why it's good: This fix is outstanding, detailing the specific problem
(esbuild errors), the solution (polyfill), and the context (Puppeteer).

────────────────────────────────────────────────────────────────────────────────
📊 YOUR STATS
────────────────────────────────────────────────────────────────────────────────

Average score: 7.3/10
Vague commits: 7 (14%)
One-word commits: 0 (0%)
```

## How It Works

### Analyze Mode (`--analyze`)

Pulls the last 50 commits, sends the messages to an LLM acting as a Staff Engineer reviewer, and groups results into:

- **Commits that need work** — what's wrong and how to fix it
- **Well-written commits** — what makes them good (so you can do more of that)
- **Stats** — your average score, how many commits are vague, how many are one-word throwaways

### Write Mode (`--write`)

Reads your `git diff --staged`, figures out what you changed, and suggests a well-formatted conventional commit message. You can accept it with Enter or type your own. Either way, it commits for you.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | *(required)* | Your API key from [OpenRouter](https://openrouter.ai/keys) |
| `COMMIT_CRITIC_MODEL` | `google/gemini-2.5-flash` | Any model ID from [OpenRouter's catalog](https://openrouter.ai/models) |

## Troubleshooting

**`Error: OPENROUTER_API_KEY not set.`**
Your `.env` file is missing or doesn't contain the key. Run `cp .env.example .env` and paste your API key from [openrouter.ai/keys](https://openrouter.ai/keys).

**`No staged changes found. Stage files with git add first.`**
You ran `--write` without staging anything. Run `git add <files>` first, then try again.

**Python version errors or unexpected syntax issues**
This project requires Python 3.11+. Check your version with `python3 --version`. If you're on an older version, consider using [pyenv](https://github.com/pyenv/pyenv) to install a newer one.

## Tech Stack

- **Python 3.11+** — CLI built with [Click](https://click.palletsprojects.com/), terminal UI with [Rich](https://github.com/Textualize/rich)
- **GitPython** — for all git operations (reading commits, diffs, cloning)
- **OpenRouter** — LLM gateway (defaults to Gemini 2.5 Flash, but you can swap to Claude, GPT, or anything else they support)
