import sys

from rich.console import Console
from rich.rule import Rule

from git_utils import get_staged_diff, get_staged_stats, commit_with_message, GitError
from llm import suggest_commit_message, LLMError

console = Console()


def run_writer(repo_path):
    """Run interactive commit writer mode."""
    try:
        diff = get_staged_diff(repo_path)
        if not diff:
            console.print(
                "[red]No staged changes found.[/red] "
                "Stage files with [cyan]git add[/cyan] first."
            )
            return

        # Show staged stats
        stats = get_staged_stats(repo_path)
        summary_line = _parse_stat_summary(stats)
        console.print(f"\nAnalyzing staged changes... ({summary_line})\n")

        # Single LLM call: get both summary and suggestion
        with console.status("Generating commit message...", spinner="dots"):
            changes_summary, suggestion = suggest_commit_message(diff)

        if changes_summary:
            console.print("[bold]Changes detected:[/bold]")
            console.print(changes_summary)
            console.print()

        console.print("[bold]Suggested commit message:[/bold]")
        console.print(Rule(style="bold"))
        console.print(suggestion)
        console.print(Rule(style="bold"))
        console.print()

        user_input = console.input(
            "Press [bold]Enter[/bold] to accept, or type your own message:\n> "
        )

        message = user_input.strip() if user_input.strip() else suggestion
        commit_with_message(repo_path, message)
        console.print("\n[green]Committed successfully![/green]")

    except GitError as e:
        console.print(f"[red]Git error:[/red] {e}")
        sys.exit(1)
    except LLMError as e:
        console.print(f"[red]LLM error:[/red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Aborted.[/yellow]")


def _parse_stat_summary(stats):
    """Extract summary line from git diff --stat output."""
    lines = stats.strip().split("\n")
    if lines:
        return lines[-1].strip()
    return "changes detected"
