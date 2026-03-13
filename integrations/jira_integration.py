"""Jira integration using the jira Python SDK."""

from __future__ import annotations

import logging
from typing import Any

from jira import JIRA
from jira.exceptions import JIRAError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from security.secrets import get_secrets

logger = logging.getLogger("claw-agent.integrations.jira_integration")


class JiraIntegration:
    """Jira integration for tickets, updates, and remote links."""

    def __init__(self) -> None:
        """Initialize Jira client with server URL and basic auth from secrets."""
        secrets = get_secrets()
        self._client = JIRA(
            server=secrets.jira_url,
            basic_auth=(secrets.jira_user, secrets.jira_api_token),
        )
        self._logger = logger

    @retry(
        retry=retry_if_exception_type((JIRAError, Exception)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def create_ticket(
        self,
        project: str,
        summary: str,
        description: str = "",
        issue_type: str = "Task",
    ) -> dict[str, Any]:
        """Create a Jira ticket.

        Args:
            project: Project key.
            summary: Ticket summary/title.
            description: Ticket description (optional).
            issue_type: Issue type (default Task).

        Returns:
            Dict with key, url, summary.
        """
        self._logger.info("Creating ticket in project %s: %s", project, summary)
        issue = self._client.create_issue(
            project=project,
            summary=summary,
            description=description,
            issuetype={"name": issue_type},
        )
        return {
            "key": issue.key,
            "url": f"{self._client.server_url}/browse/{issue.key}",
            "summary": issue.fields.summary,
        }

    @retry(
        retry=retry_if_exception_type((JIRAError, Exception)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def update_ticket(self, ticket_key: str, **fields: Any) -> dict[str, Any]:
        """Update ticket fields.

        Args:
            ticket_key: Jira issue key (e.g. PROJ-123).
            **fields: Field names and values to update.

        Returns:
            Dict with key and updated status.
        """
        self._logger.info("Updating ticket %s with fields: %s", ticket_key, list(fields.keys()))
        issue = self._client.issue(ticket_key)
        issue.update(fields=fields)
        return {
            "key": ticket_key,
            "updated": True,
        }

    @retry(
        retry=retry_if_exception_type((JIRAError, Exception)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def link_github_issue(
        self, ticket_key: str, github_url: str
    ) -> dict[str, Any]:
        """Add a remote link to a GitHub issue.

        Args:
            ticket_key: Jira issue key.
            github_url: URL of the GitHub issue.

        Returns:
            Dict with key and link status.
        """
        self._logger.info("Linking GitHub issue %s to ticket %s", github_url, ticket_key)
        self._client.add_simple_link(
            ticket_key,
            object={"url": github_url, "title": "GitHub Issue"},
        )
        return {
            "key": ticket_key,
            "github_url": github_url,
            "linked": True,
        }

    @retry(
        retry=retry_if_exception_type((JIRAError, Exception)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def get_ticket_details(self, ticket_key: str) -> dict[str, Any]:
        """Get ticket details.

        Args:
            ticket_key: Jira issue key.

        Returns:
            Dict with key, summary, status, assignee, description.
        """
        self._logger.info("Fetching ticket details for %s", ticket_key)
        issue = self._client.issue(ticket_key)
        assignee = issue.fields.assignee
        return {
            "key": issue.key,
            "summary": issue.fields.summary or "",
            "status": str(issue.fields.status) if issue.fields.status else "",
            "assignee": assignee.displayName if assignee else None,
            "description": issue.fields.description or "",
        }
