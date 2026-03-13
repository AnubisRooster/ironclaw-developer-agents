"""Confluence integration using atlassian-python-api."""

from __future__ import annotations

import logging
import re
from html import unescape
from typing import Any

from atlassian import Confluence
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from security.secrets import get_secrets

logger = logging.getLogger("claw-agent.integrations.confluence")


def _strip_html(html: str) -> str:
    """Remove HTML tags and decode entities."""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return unescape(text).strip()


class ConfluenceIntegration:
    """Confluence integration for search, pages, and content."""

    def __init__(self) -> None:
        """Initialize Confluence client with url, username, and api_token from secrets."""
        secrets = get_secrets()
        self._client = Confluence(
            url=secrets.confluence_url,
            username=secrets.confluence_user,
            password=secrets.confluence_api_token,
        )
        self._logger = logger

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def search_docs(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """CQL search for Confluence documents.

        Args:
            query: CQL search query.
            limit: Maximum results to return (default 10).

        Returns:
            List of dicts with title, id, url.
        """
        self._logger.info("Searching Confluence for: %s", query)
        results = self._client.cql(query, limit=limit)
        items = results.get("results", [])
        return [
            {
                "title": item.get("content", {}).get("title", ""),
                "id": item.get("content", {}).get("id"),
                "url": f"{self._client.url}/pages/viewpage.action?pageId={item.get('content', {}).get('id')}",
            }
            for item in items
        ]

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def summarize_page(self, page_id: str) -> dict[str, Any]:
        """Get page content (stripped of HTML) with preview.

        Args:
            page_id: Confluence page ID.

        Returns:
            Dict with title, content_preview (first 2000 chars), url.
        """
        self._logger.info("Fetching page %s", page_id)
        page = self._client.get_page_by_id(page_id, expand="body.storage")
        body = page.get("body", {}).get("storage", {}).get("value", "")
        plain_text = _strip_html(body)
        content_preview = plain_text[:2000] if len(plain_text) > 2000 else plain_text
        if len(plain_text) > 2000:
            content_preview += "..."
        return {
            "title": page.get("title", ""),
            "content_preview": content_preview,
            "url": f"{self._client.url}/pages/viewpage.action?pageId={page_id}",
        }

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def create_page(
        self,
        space: str,
        title: str,
        body: str,
        parent_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a Confluence page.

        Args:
            space: Space key.
            title: Page title.
            body: Page body (HTML).
            parent_id: Parent page ID (optional).

        Returns:
            Dict with id, title, url.
        """
        self._logger.info("Creating page in space %s: %s", space, title)
        response = self._client.create_page(
            space=space,
            title=title,
            body=body,
            parent_id=parent_id,
        )
        return {
            "id": response.get("id"),
            "title": response.get("title", title),
            "url": f"{self._client.url}/pages/viewpage.action?pageId={response.get('id')}",
        }
