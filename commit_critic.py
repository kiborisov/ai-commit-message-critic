#!/usr/bin/env python3
"""AI Commit Message Critic - Analyze and improve git commit messages."""

import os
import sys
import click
from dotenv import load_dotenv

load_dotenv()


@click.command()
@click.option("--analyze", is_flag=True, help="Analyze commit history (default mode)")
@click.option("--write", is_flag=True, help="Interactive commit writer for staged changes")
@click.option("--url", default=None, help="Remote repository URL to analyze")
def main(analyze, write, url):
    """AI-powered commit message critic and writer."""
    if write and url:
        click.echo("Error: --url cannot be used with --write.", err=True)
        sys.exit(1)

    if not os.environ.get("OPENROUTER_API_KEY"):
        click.echo(
            "Error: OPENROUTER_API_KEY not set. "
            "Export it or create a .env file (see .env.example).",
            err=True,
        )
        sys.exit(1)

    if write:
        from writer import run_writer
        run_writer(os.getcwd())
    else:
        from analyzer import run_analysis
        run_analysis(os.getcwd(), remote_url=url)


if __name__ == "__main__":
    main()
