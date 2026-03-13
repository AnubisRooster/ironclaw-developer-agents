"""FastAPI webhook server — receives events from GitHub, Jira, Jenkins, and Slack."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any, Dict

from fastapi import FastAPI, Header, HTTPException, Request

from events.bus import event_bus
from events.types import AgentEvent, EventSource
from security.secrets import get_secrets, verify_webhook_signature

logger = logging.getLogger("claw-agent.webhooks")

app = FastAPI(
    title="Claw Agent Webhooks",
    version="0.1.0",
    docs_url="/docs",
)


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------

@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
):
    body = await request.body()
    secrets = get_secrets()

    if secrets.github_webhook_secret:
        if not x_hub_signature_256:
            raise HTTPException(status_code=401, detail="Missing signature")
        if not verify_webhook_signature(
            body, x_hub_signature_256, secrets.github_webhook_secret, "sha256"
        ):
            raise HTTPException(status_code=403, detail="Invalid signature")

    payload: Dict[str, Any] = json.loads(body)
    action = payload.get("action", "")
    event_type = f"github.{x_github_event or 'unknown'}"
    if action:
        event_type = f"{event_type}.{action}"

    event = AgentEvent(
        event_type=event_type,
        source=EventSource.GITHUB,
        payload=payload,
    )
    logger.info("Received GitHub webhook: %s", event_type)
    await event_bus.publish(event)
    return {"accepted": True, "event_type": event_type}


# ---------------------------------------------------------------------------
# Jira
# ---------------------------------------------------------------------------

@app.post("/webhooks/jira")
async def jira_webhook(request: Request):
    body = await request.body()
    secrets = get_secrets()

    if secrets.jira_webhook_secret:
        sig = request.headers.get("x-hub-signature", "")
        if not verify_webhook_signature(
            body, sig, secrets.jira_webhook_secret, "sha256"
        ):
            raise HTTPException(status_code=403, detail="Invalid signature")

    payload: Dict[str, Any] = json.loads(body)
    webhook_event = payload.get("webhookEvent", "unknown")
    event_type = f"jira.{webhook_event}".replace(":", ".").replace("_", ".")

    event = AgentEvent(
        event_type=event_type,
        source=EventSource.JIRA,
        payload=payload,
    )
    logger.info("Received Jira webhook: %s", event_type)
    await event_bus.publish(event)
    return {"accepted": True, "event_type": event_type}


# ---------------------------------------------------------------------------
# Jenkins
# ---------------------------------------------------------------------------

@app.post("/webhooks/jenkins")
async def jenkins_webhook(request: Request):
    body = await request.body()
    secrets = get_secrets()

    if secrets.jenkins_webhook_secret:
        sig = request.headers.get("x-jenkins-signature", "")
        if sig and not verify_webhook_signature(
            body, sig, secrets.jenkins_webhook_secret, "sha256"
        ):
            raise HTTPException(status_code=403, detail="Invalid signature")

    payload: Dict[str, Any] = json.loads(body)
    build_phase = payload.get("build", {}).get("phase", "unknown").lower()
    build_status = payload.get("build", {}).get("status", "").lower()
    job_name = payload.get("name", "unknown")

    event_type = f"jenkins.build.{build_phase}"
    if build_status:
        event_type = f"jenkins.build.{build_status}"

    event = AgentEvent(
        event_type=event_type,
        source=EventSource.JENKINS,
        payload={**payload, "job_name": job_name},
    )
    logger.info("Received Jenkins webhook: %s", event_type)
    await event_bus.publish(event)
    return {"accepted": True, "event_type": event_type}


# ---------------------------------------------------------------------------
# Slack
# ---------------------------------------------------------------------------

@app.post("/webhooks/slack")
async def slack_webhook(request: Request):
    body = await request.body()
    secrets = get_secrets()

    if secrets.slack_signing_secret:
        timestamp = request.headers.get("x-slack-request-timestamp", "")
        slack_sig = request.headers.get("x-slack-signature", "")
        sig_basestring = f"v0:{timestamp}:{body.decode()}"
        computed = (
            "v0="
            + hmac.new(
                secrets.slack_signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256,
            ).hexdigest()
        )
        if not hmac.compare_digest(computed, slack_sig):
            raise HTTPException(status_code=403, detail="Invalid Slack signature")

    payload: Dict[str, Any] = json.loads(body)

    # Handle Slack URL verification challenge
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}

    event_type_raw = payload.get("event", {}).get("type", "command")
    event_type = f"slack.{event_type_raw}.received"

    event = AgentEvent(
        event_type=event_type,
        source=EventSource.SLACK,
        payload=payload,
    )
    logger.info("Received Slack webhook: %s", event_type)
    await event_bus.publish(event)
    return {"accepted": True, "event_type": event_type}
