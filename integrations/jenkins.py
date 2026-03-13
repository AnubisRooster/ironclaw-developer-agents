"""Jenkins integration using python-jenkins."""

from __future__ import annotations

import logging
from typing import Any

import jenkins
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from security.secrets import get_secrets

logger = logging.getLogger("claw-agent.integrations.jenkins")


class JenkinsIntegration:
    """Jenkins integration for triggering builds and fetching status/logs."""

    def __init__(self) -> None:
        """Initialize Jenkins client with url, username, and password from secrets."""
        secrets = get_secrets()
        self._client = jenkins.Jenkins(
            secrets.jenkins_url,
            username=secrets.jenkins_user,
            password=secrets.jenkins_api_token,
        )
        self._logger = logger

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def trigger_build(
        self, job_name: str, parameters: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Trigger a Jenkins build.

        Args:
            job_name: Name of the job to build.
            parameters: Optional dict of build parameters.

        Returns:
            Dict with job, queue_id.
        """
        self._logger.info("Triggering build for job %s", job_name)
        queue_item = self._client.build_job(job_name, parameters=parameters or {})
        return {
            "job": job_name,
            "queue_id": queue_item,
        }

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def get_build_status(
        self, job_name: str, build_number: int | None = None
    ) -> dict[str, Any]:
        """Get status of latest or specific build.

        Args:
            job_name: Name of the job.
            build_number: Specific build number, or None for latest.

        Returns:
            Dict with job, number, status, url, duration.
        """
        self._logger.info("Fetching build status for %s #%s", job_name, build_number or "latest")
        if build_number is None:
            build_info = self._client.get_job_info(job_name)
            last_build = build_info.get("lastBuild")
            if not last_build:
                return {
                    "job": job_name,
                    "number": None,
                    "status": "unknown",
                    "url": None,
                    "duration": None,
                }
            build_number = last_build.get("number")

        build_info = self._client.get_build_info(job_name, build_number)
        return {
            "job": job_name,
            "number": build_info.get("number"),
            "status": build_info.get("result", "RUNNING"),
            "url": build_info.get("url"),
            "duration": build_info.get("duration"),
        }

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def fetch_build_logs(
        self, job_name: str, build_number: int | None = None
    ) -> dict[str, Any]:
        """Get console output (last 5000 chars) for a build.

        Args:
            job_name: Name of the job.
            build_number: Specific build number, or None for latest.

        Returns:
            Dict with job, number, log_tail.
        """
        self._logger.info("Fetching build logs for %s #%s", job_name, build_number or "latest")
        if build_number is None:
            build_info = self._client.get_job_info(job_name)
            last_build = build_info.get("lastBuild")
            if not last_build:
                return {"job": job_name, "number": None, "log_tail": ""}
            build_number = last_build.get("number")

        full_log = self._client.get_build_console_output(job_name, build_number)
        log_tail = full_log[-5000:] if len(full_log) > 5000 else full_log
        return {
            "job": job_name,
            "number": build_number,
            "log_tail": log_tail,
        }
