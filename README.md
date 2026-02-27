# AI Commit Message Critic

A terminal tool that uses AI to review your git commit messages — like having a Staff Engineer audit your commit hygiene.

Point it at any repo (local or remote) and it scores every commit, calls out the lazy ones, and explains why the good ones work. It can also read your staged changes and write the commit message for you.

## Why?

Bad commit messages are tech debt nobody talks about. When something breaks at 2am and you're running `git bisect`, the difference between `"fix bug"` and `"fix(auth): resolve token expiration causing silent logouts"` is the difference between a 10-minute fix and a 2-hour investigation.

This tool makes that visible.

## Getting Started

```bash
# 1. Set up the environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Add your API key (get one at https://openrouter.ai/keys)
cp .env.example .env
# Edit .env and paste your OpenRouter key

# 3. Analyze a repo
python commit_critic.py --analyze
```

That's it. Three steps.

## Usage

**Analyze the current repo's last 50 commits:**
```bash
python commit_critic.py --analyze
```

**Analyze any public repo by URL:**
```bash
python commit_critic.py --analyze --url="https://github.com/steel-dev/steel-browser"
```

**Let AI write your next commit message:**
```bash
git add .
python commit_critic.py --write
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

## Tech Stack

- **Python 3.11+** — CLI built with [Click](https://click.palletsprojects.com/), terminal UI with [Rich](https://github.com/Textualize/rich)
- **GitPython** — for all git operations (reading commits, diffs, cloning)
- **OpenRouter** — LLM gateway (defaults to Gemini 2.5 Flash, but you can swap to Claude, GPT, or anything else they support)
