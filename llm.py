import json
import os
from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError, APIError


MODEL = os.environ.get("COMMIT_CRITIC_MODEL", "google/gemini-2.5-flash")
MAX_DIFF_CHARS = 80_000  # ~20k tokens, safe for most models


class LLMError(Exception):
    """User-facing LLM error."""


_client = None


def _client_instance():
    global _client
    if _client is None:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise LLMError(
                "OPENROUTER_API_KEY not set. Export it or add it to a .env file."
            )
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    return _client


def _call(messages, max_tokens):
    """Wrapper around API call with error handling."""
    client = _client_instance()
    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=max_tokens,
            messages=messages,
        )
    except AuthenticationError:
        raise LLMError("Invalid API key. Check your OPENROUTER_API_KEY.")
    except RateLimitError:
        raise LLMError("Rate limited. Wait a moment and retry.")
    except APIConnectionError:
        raise LLMError("Cannot connect to OpenRouter. Check your network.")
    except APIError as e:
        raise LLMError(f"API error: {e}")
    content = response.choices[0].message.content
    if not content:
        raise LLMError("LLM returned an empty response. Try again.")
    return content.strip()


def _extract_json(text):
    """Extract JSON array from LLM response, handling markdown code blocks
    and stray characters from model artifacts."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1:
        text = text[start:end + 1]

    # First try parsing as-is
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Clean up common model artifacts: stray characters before }, ], or ,
    import re
    cleaned = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)  # strip non-ASCII junk
    cleaned = re.sub(r'\s*[A-Z]\}', '}', cleaned)        # "X}" -> "}"
    cleaned = re.sub(r'\s*[A-Z]\]', ']', cleaned)        # "X]" -> "]"
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise LLMError(
            f"Failed to parse LLM response as JSON: {e}\n"
            f"Raw response (first 500 chars): {text[:500]}"
        )


def _truncate_diff(diff):
    """Truncate diff to fit within context window."""
    if len(diff) <= MAX_DIFF_CHARS:
        return diff
    half = MAX_DIFF_CHARS // 2
    return (
        diff[:half]
        + f"\n\n... [truncated {len(diff) - MAX_DIFF_CHARS} characters] ...\n\n"
        + diff[-half:]
    )


def analyze_commits(commits):
    """Score a list of commit messages via LLM.

    Returns list of dicts with hash, message, score, issue/praise, suggestion.
    """
    commits_text = "\n".join(
        f'{i+1}. [{c["hash"]}] {c["message"]}'
        for i, c in enumerate(commits)
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a Staff Engineer at a top-tier tech company doing a code review "
                "focused on commit hygiene. You have strong opinions about git history being "
                "a form of documentation. You've seen thousands of repos and know exactly what "
                "separates a commit log that tells a story from one that's useless noise. "
                "Be direct, opinionated, and specific — don't sugarcoat bad commits, and when "
                "something is good, explain exactly why it matters for the team. "
                "Respond with ONLY valid JSON, no markdown, no commentary."
            ),
        },
        {
            "role": "user",
            "content": f"""Review these commit messages like you're auditing git hygiene for a team. For each commit, return a JSON array element with:
- "index": 1-based position
- "score": integer 1-10
- "issue": if score <= 5, a pointed 1-sentence critique (e.g. "This tells the next developer nothing — good luck bisecting when this breaks in prod."). Empty string if score > 5.
- "praise": if score > 5, a punchy 1-sentence reason it's good (e.g. "Scoped to a single concern, links cause to effect — this is what makes git blame useful."). Empty string if score <= 5.
- "suggestion": if score <= 5, rewrite it as a proper conventional commit. Empty string if score > 5.

Scoring — be harsh, this is a real review:
1-2: Garbage. Zero signal. ("fix", "wip", "update", "stuff")
3-4: Lazy. You can guess something changed but you'd have to read the diff. ("fixed bug", "updated styles", "changes")
5: Mediocre. Gets the point across but no scope, no context, no craft.
6-7: Solid. Clear what changed, but missing the "why" or proper conventional format.
8-9: Strong. Conventional format, scoped, tells you what AND why. You'd approve this in review.
10: Textbook. Perfect conventional commit. Scope, intent, impact. Future you says thanks.

Commits:
{commits_text}""",
        },
    ]

    text = _call(messages, max_tokens=8192)
    results = _extract_json(text)

    # Build index map for resilience against missing/reordered results
    result_map = {r["index"]: r for r in results}
    merged = []
    for i, commit in enumerate(commits):
        r = result_map.get(i + 1)
        if r:
            merged.append({
                "hash": commit["hash"],
                "message": commit["message"],
                "author": commit["author"],
                "date": commit["date"],
                "score": max(1, min(10, int(r.get("score", 5)))),
                "issue": r.get("issue", ""),
                "praise": r.get("praise", ""),
                "suggestion": r.get("suggestion", ""),
            })
        else:
            merged.append({
                "hash": commit["hash"],
                "message": commit["message"],
                "author": commit["author"],
                "date": commit["date"],
                "score": 5,
                "issue": "(not scored by LLM)",
                "praise": "",
                "suggestion": "",
            })
    return merged


def suggest_commit_message(diff):
    """Given a staged diff, return (changes_summary, commit_message)."""
    diff = _truncate_diff(diff)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a Staff Engineer writing a commit message. You believe git history "
                "is documentation — every commit should tell the next developer what changed, "
                "why, and what to watch out for. You use conventional commits religiously. "
                "You scope tightly and describe impact, not just mechanics."
            ),
        },
        {
            "role": "user",
            "content": f"""Look at this diff and write the commit message a Staff Engineer would write.

Respond with exactly two sections separated by "====SEPARATOR====":

SECTION 1: A bullet-point summary of the high-level changes (3-5 bullets, each starting with "- "). Focus on intent and impact, not just file names.

====SEPARATOR====

SECTION 2: The commit message in conventional commit format:
type(scope): concise description of what and why

- Specific change 1
- Specific change 2

Be opinionated about the scope and type. Don't be vague. Respond with ONLY these two sections.

Diff:
{diff}""",
        },
    ]

    text = _call(messages, max_tokens=1024)

    if "====SEPARATOR====" in text:
        parts = text.split("====SEPARATOR====", 1)
        return parts[0].strip(), parts[1].strip()
    return "", text
