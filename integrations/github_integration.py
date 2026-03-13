"""GitHub integration using PyGithub."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from github import Github
from github.GithubException import GithubException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from security.secrets import get_secrets

logger = logging.getLogger("claw-agent.integrations.github_integration")


class GitHubIntegration:
    """GitHub integration for issues, PRs, branches, and repository activity."""

    def __init__(self) -> None:
        """Initialize GitHub client with token from secrets."""
        secrets = get_secrets()
        self._client = Github(secrets.github_token)
        self._logger = logger

    @retry(
        retry=retry_if_exception_type((GithubException, Exception)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def create_issue(
        self, repo: str, title: str, body: str = ""
    ) -> dict[str, Any]:
        """Create a GitHub issue.

        Args:
            repo: Repository in owner/name format.
            title: Issue title.
            body: Issue body (optional).

        Returns:
            Dict with number, url, title.
        """
        self._logger.info("Creating issue in %s: %s", repo, title)
        repository = self._client.get_repo(repo)
        issue = repository.create_issue(title=title, body=body)
        return {
            "number": issue.number,
            "url": issue.html_url,
            "title": issue.title,
        }

    @retry(
        retry=retry_if_exception_type((GithubException, Exception)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def summarize_pull_request(
        self, repo: str, pr_number: int
    ) -> dict[str, Any]:
        """Get PR details including title, body, changed files, additions, deletions.

        Args:
            repo: Repository in owner/name format.
            pr_number: Pull request number.

        Returns:
            Structured dict with title, body, changed_files_count, additions, deletions, url, state.
        """
        self._logger.info("Fetching PR %s in %s", pr_number, repo)
        repository = self._client.get_repo(repo)
        pr = repository.get_pull(pr_number)
        return {
            "title": pr.title,
            "body": pr.body or "",
            "changed_files_count": pr.changed_files,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "url": pr.html_url,
            "state": pr.state,
        }

    @retry(
        retry=retry_if_exception_type((GithubException, Exception)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def comment_on_pr(
        self, repo: str, pr_number: int, comment: str
    ) -> dict[str, Any]:
        """Add a comment to a pull request.

        Args:
            repo: Repository in owner/name format.
            pr_number: Pull request number.
            comment: Comment text.

        Returns:
            Dict with html_url and id.
        """
        self._logger.info("Commenting on PR %s in %s", pr_number, repo)
        repository = self._client.get_repo(repo)
        pr = repository.get_pull(pr_number)
        issue_comment = pr.create_issue_comment(comment)
        return {
            "html_url": issue_comment.html_url,
            "id": issue_comment.id,
        }

    @retry(
        retry=retry_if_exception_type((GithubException, Exception)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def create_branch(
        self,
        repo: str,
        branch_name: str,
        from_branch: str = "main",
    ) -> dict[str, Any]:
        """Create a new branch from an existing branch.

        Args:
            repo: Repository in owner/name format.
            branch_name: Name of the new branch.
            from_branch: Base branch (default main).

        Returns:
            Dict with ref, url.
        """
        self._logger.info("Creating branch %s from %s in %s", branch_name, from_branch, repo)
        repository = self._client.get_repo(repo)
        source_branch = repository.get_branch(from_branch)
        ref = repository.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=source_branch.commit.sha,
        )
        return {
            "ref": ref.ref,
            "url": f"{repository.html_url}/tree/{branch_name}",
        }

    @retry(
        retry=retry_if_exception_type((GithubException, Exception)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def get_repo_activity(self, repo: str, days: int = 1) -> dict[str, Any]:
        """Get recent commits, PRs, and issues from the last N days.

        Args:
            repo: Repository in owner/name format.
            days: Number of days to look back (default 1).

        Returns:
            Dict with commits, pull_requests, issues lists.
        """
        self._logger.info("Fetching repo activity for %s (last %s days)", repo, days)
        repository = self._client.get_repo(repo)
        since = datetime.now(timezone.utc) - timedelta(days=days)

        commits = []
        for commit in repository.get_commits(since=since):
            commits.append({
                "sha": commit.sha[:7],
                "message": commit.commit.message,
                "author": commit.commit.author.name,
                "date": commit.commit.author.date.isoformat() if commit.commit.author.date else None,
            })

        pull_requests = []
        for pr in repository.get_pulls(state="all"):
            if pr.updated_at and pr.updated_at.replace(tzinfo=timezone.utc) >= since:
                pull_requests.append({
                    "number": pr.number,
                    "title": pr.title,
                    "state": pr.state,
                    "url": pr.html_url,
                })

        issues = []
        for issue in repository.get_issues(state="all"):
            if issue.updated_at and issue.updated_at.replace(tzinfo=timezone.utc) >= since and not issue.pull_request:
                issues.append({
                    "number": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "url": issue.html_url,
                })

        return {
            "commits": commits,
            "pull_requests": pull_requests,
            "issues": issues,
        }
