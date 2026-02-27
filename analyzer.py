import shutil
import sys

from rich.console import Console
from rich.rule import Rule

from git_utils import get_recent_commits, clone_remote, GitError
from llm import analyze_commits, LLMError

console = Console()


def _section_header(emoji, title):
    console.print()
    console.print(Rule(style="bold"))
    console.print(f"{emoji} [bold]{title}[/bold]")
    console.print(Rule(style="bold"))
    console.print()


def run_analysis(repo_path, remote_url=None):
    """Run commit analysis mode."""
    cloned_path = None

    try:
        if remote_url:
            with console.status(f"Cloning [cyan]{remote_url}[/cyan]..."):
                cloned_path = clone_remote(remote_url)
            repo_path = cloned_path

        console.print("\nAnalyzing last 50 commits...\n")

        commits = get_recent_commits(repo_path, count=50)
        if not commits:
            console.print("[red]No commits found in this repository.[/red]")
            return

        with console.status(
            f"Analyzing {len(commits)} commits...", spinner="dots"
        ):
            results = analyze_commits(commits)

        if not results:
            console.print("[red]LLM returned no results.[/red]")
            return

        needs_work = [r for r in results if r["score"] <= 5]
        well_written = [r for r in results if r["score"] > 5]

        # Needs work section
        _section_header("\U0001f4a9", "COMMITS THAT NEED WORK")

        if needs_work:
            for r in needs_work:
                score_color = "red" if r["score"] <= 3 else "yellow"
                console.print(f'Commit: [white]"{r["message"]}"[/white]')
                console.print(f'Score: [{score_color}]{r["score"]}/10[/{score_color}]')
                if r["issue"]:
                    console.print(f'Issue: {r["issue"]}')
                if r["suggestion"]:
                    console.print(f'Better: [green]"{r["suggestion"]}"[/green]')
                console.print()
        else:
            console.print("[green]None! All commits look good.[/green]\n")

        # Well-written section
        _section_header("\U0001f48e", "WELL-WRITTEN COMMITS")

        if well_written:
            for r in well_written:
                score_color = "green" if r["score"] >= 8 else "cyan"
                console.print(f'Commit: [white]"{r["message"]}"[/white]')
                console.print(f'Score: [{score_color}]{r["score"]}/10[/{score_color}]')
                if r["praise"]:
                    console.print(f'Why it\'s good: {r["praise"]}')
                console.print()
        else:
            console.print("[yellow]No well-written commits found.[/yellow]\n")

        # Stats section
        _section_header("\U0001f4ca", "YOUR STATS")
        _print_stats(results)

    except GitError as e:
        console.print(f"[red]Git error:[/red] {e}")
        sys.exit(1)
    except LLMError as e:
        console.print(f"[red]LLM error:[/red] {e}")
        sys.exit(1)
    finally:
        if cloned_path:
            shutil.rmtree(cloned_path, ignore_errors=True)


def _print_stats(results):
    total = len(results)
    scores = [r["score"] for r in results]
    avg_score = sum(scores) / total
    vague_count = sum(1 for r in results if r["score"] <= 5)
    one_word_count = sum(
        1 for r in results if len(r["message"].split()) == 1
    )

    console.print(f"Average score: [bold]{avg_score:.1f}/10[/bold]")
    console.print(
        f"Vague commits: [yellow]{vague_count}[/yellow] "
        f"({vague_count * 100 // total}%)"
    )
    console.print(
        f"One-word commits: [yellow]{one_word_count}[/yellow] "
        f"({one_word_count * 100 // total}%)"
    )
    console.print()
