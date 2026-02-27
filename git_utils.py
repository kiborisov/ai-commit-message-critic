import tempfile
import git


class GitError(Exception):
    """User-facing git operation error."""


def _open_repo(path):
    try:
        repo = git.Repo(path, search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        raise GitError(f"Not a git repository: {path}")
    except git.NoSuchPathError:
        raise GitError(f"Path does not exist: {path}")
    return repo


def get_recent_commits(repo_path, count=50):
    """Get the most recent commits from a git repo."""
    repo = _open_repo(repo_path)
    if repo.head.is_valid() is False:
        return []
    commits = []
    for c in repo.iter_commits(max_count=count):
        # Use first line only — merge commits can be multi-line
        first_line = c.message.strip().split("\n")[0]
        commits.append({
            "hash": c.hexsha[:8],
            "message": first_line,
            "full_message": c.message.strip(),
            "author": str(c.author),
            "date": c.committed_datetime.strftime("%Y-%m-%d %H:%M"),
        })
    return commits


def get_staged_diff(repo_path):
    """Get the staged diff (git diff --staged)."""
    repo = _open_repo(repo_path)
    return repo.git.diff("--staged")


def get_staged_stats(repo_path):
    """Get summary stats for staged changes."""
    repo = _open_repo(repo_path)
    return repo.git.diff("--staged", "--stat")


def clone_remote(url):
    """Clone a remote repo to a temp directory and return the path.

    Raises GitError on failure (bad URL, network, auth, etc).
    """
    tmp_dir = tempfile.mkdtemp(prefix="commit_critic_")
    try:
        git.Repo.clone_from(url, tmp_dir, depth=50)
    except git.GitCommandError as e:
        raise GitError(f"Failed to clone {url}: {e.stderr.strip() if e.stderr else e}")
    return tmp_dir


def commit_with_message(repo_path, message):
    """Create a commit with the given message."""
    repo = _open_repo(repo_path)
    try:
        repo.git.commit("-m", message)
    except git.GitCommandError as e:
        raise GitError(f"Commit failed: {e.stderr.strip() if e.stderr else e}")
