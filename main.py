"""Developer Automation Agent — main entry point.

CLI commands:
    claw-agent chat            — interactive chat with the agent
    claw-agent run             — start the webhook server (background daemon mode)
    claw-agent webhook-server  — start the webhook server (foreground)
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click
import uvicorn
from dotenv import load_dotenv

load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from security.secrets import RedactingFilter, get_secrets


def _setup_logging() -> None:
    """Configure structured logging with redaction filter."""
    log_dir = _PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    log_file = log_dir / "agent.log"
    handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)
    for handler in logging.root.handlers:
        handler.addFilter(RedactingFilter())


def _build_orchestrator():
    """Create the Orchestrator with all integrations registered as tools."""
    from agent.ironclaw_client import IronClawClient
    from agent.orchestrator import Orchestrator
    from tools.registry import ToolSchemaRegistry
    from integrations.slack import SlackIntegration
    from integrations.github_integration import GitHubIntegration
    from integrations.jira_integration import JiraIntegration
    from integrations.confluence import ConfluenceIntegration
    from integrations.jenkins import JenkinsIntegration
    from integrations.gmail import GmailIntegration

    registry = ToolSchemaRegistry()
    ironclaw = IronClawClient()
    orch = Orchestrator(ironclaw=ironclaw, registry=registry)
    secrets = get_secrets()

    # --- Slack tools ---
    if secrets.slack_bot_token:
        slack = SlackIntegration()
        registry.register_tool(
            name="slack.send_message",
            description="Send a message to a Slack channel",
            parameters={
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "Channel ID or name"},
                    "text": {"type": "string", "description": "Message text"},
                },
                "required": ["channel", "text"],
            },
            handler=slack.send_message,
        )
        registry.register_tool(
            name="slack.read_channel",
            description="Read recent messages from a Slack channel",
            parameters={
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "Channel ID"},
                    "limit": {"type": "integer", "description": "Max messages", "default": 50},
                },
                "required": ["channel"],
            },
            handler=slack.read_channel_history,
        )

    # --- GitHub tools ---
    if secrets.github_token:
        gh = GitHubIntegration()
        registry.register_tool(
            name="github.create_issue",
            description="Create a GitHub issue",
            parameters={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository in owner/name format"},
                    "title": {"type": "string", "description": "Issue title"},
                    "body": {"type": "string", "description": "Issue body", "default": ""},
                },
                "required": ["repo", "title"],
            },
            handler=gh.create_issue,
        )
        registry.register_tool(
            name="github.summarize_pr",
            description="Summarize a GitHub pull request",
            parameters={
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "pr_number": {"type": "integer"},
                },
                "required": ["repo", "pr_number"],
            },
            handler=gh.summarize_pull_request,
        )
        registry.register_tool(
            name="github.comment_pr",
            description="Comment on a GitHub pull request",
            parameters={
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "pr_number": {"type": "integer"},
                    "comment": {"type": "string"},
                },
                "required": ["repo", "pr_number", "comment"],
            },
            handler=gh.comment_on_pr,
        )
        registry.register_tool(
            name="github.create_branch",
            description="Create a new Git branch",
            parameters={
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "branch_name": {"type": "string"},
                    "from_branch": {"type": "string", "default": "main"},
                },
                "required": ["repo", "branch_name"],
            },
            handler=gh.create_branch,
        )

    # --- Jira tools ---
    if secrets.jira_api_token:
        jira = JiraIntegration()
        registry.register_tool(
            name="jira.create_ticket",
            description="Create a Jira ticket",
            parameters={
                "type": "object",
                "properties": {
                    "project": {"type": "string"},
                    "summary": {"type": "string"},
                    "description": {"type": "string", "default": ""},
                    "issue_type": {"type": "string", "default": "Task"},
                },
                "required": ["project", "summary"],
            },
            handler=jira.create_ticket,
        )
        registry.register_tool(
            name="jira.update_ticket",
            description="Update a Jira ticket",
            parameters={
                "type": "object",
                "properties": {
                    "ticket_key": {"type": "string"},
                },
                "required": ["ticket_key"],
            },
            handler=jira.update_ticket,
        )
        registry.register_tool(
            name="jira.get_issue",
            description="Get details of a Jira issue",
            parameters={
                "type": "object",
                "properties": {
                    "ticket_key": {"type": "string"},
                },
                "required": ["ticket_key"],
            },
            handler=jira.get_ticket_details,
        )

    # --- Confluence tools ---
    if secrets.confluence_api_token:
        conf = ConfluenceIntegration()
        registry.register_tool(
            name="confluence.search_docs",
            description="Search Confluence documentation",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                },
                "required": ["query"],
            },
            handler=conf.search_docs,
        )
        registry.register_tool(
            name="confluence.summarize_page",
            description="Summarize a Confluence page",
            parameters={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string"},
                },
                "required": ["page_id"],
            },
            handler=conf.summarize_page,
        )
        registry.register_tool(
            name="confluence.create_page",
            description="Create a Confluence page",
            parameters={
                "type": "object",
                "properties": {
                    "space": {"type": "string"},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "parent_id": {"type": "string"},
                },
                "required": ["space", "title", "body"],
            },
            handler=conf.create_page,
        )

    # --- Jenkins tools ---
    if secrets.jenkins_api_token:
        jenkins = JenkinsIntegration()
        registry.register_tool(
            name="jenkins.trigger_build",
            description="Trigger a Jenkins build",
            parameters={
                "type": "object",
                "properties": {
                    "job_name": {"type": "string"},
                    "parameters": {"type": "object", "default": {}},
                },
                "required": ["job_name"],
            },
            handler=jenkins.trigger_build,
        )
        registry.register_tool(
            name="jenkins.fetch_logs",
            description="Fetch Jenkins build logs",
            parameters={
                "type": "object",
                "properties": {
                    "job_name": {"type": "string"},
                    "build_number": {"type": "integer"},
                },
                "required": ["job_name"],
            },
            handler=jenkins.fetch_build_logs,
        )

    # --- Gmail tools ---
    gmail = GmailIntegration()
    registry.register_tool(
        name="gmail.read_thread",
        description="Read and summarize a Gmail thread",
        parameters={
            "type": "object",
            "properties": {
                "thread_id": {"type": "string"},
            },
            "required": ["thread_id"],
        },
        handler=gmail.summarize_thread,
    )
    registry.register_tool(
        name="gmail.send_email",
        description="Send an email via Gmail",
        parameters={
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
        handler=gmail.send_email,
    )

    # --- Agent tools (delegated to IronClaw) ---
    registry.register_tool(
        name="agent.summarize",
        description="Summarize arbitrary content using the AI reasoning engine",
        parameters={
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Text to summarize"},
                "instruction": {"type": "string", "description": "Optional focus directive", "default": ""},
            },
            "required": ["content"],
        },
        handler=orch.summarize,
    )

    return orch


def _setup_workflow_engine(orchestrator):
    """Wire the workflow engine to the event bus with orchestrator tools."""
    from workflows.engine import WorkflowEngine

    engine = WorkflowEngine(
        workflow_dir=str(_PROJECT_ROOT / "workflows"),
        registry=orchestrator.registry,
    )
    engine.load()
    return engine


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Claw Agent — Developer Automation Agent powered by IronClaw."""
    _setup_logging()
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
def chat():
    """Start an interactive chat session with the agent."""
    from cli.chat import start_chat
    orchestrator = _build_orchestrator()
    _setup_workflow_engine(orchestrator)
    start_chat(orchestrator)


@cli.command(name="webhook-server")
@click.option("--host", default=None, help="Bind host (default from .env or 0.0.0.0)")
@click.option("--port", default=None, type=int, help="Bind port (default from .env or 8080)")
def webhook_server(host: str | None, port: int | None):
    """Start the webhook server in the foreground."""
    secrets = get_secrets()
    bind_host = host or secrets.webhook_host
    bind_port = port or secrets.webhook_port

    orchestrator = _build_orchestrator()
    _setup_workflow_engine(orchestrator)

    logging.getLogger("claw-agent").info(
        "Starting webhook server on %s:%s", bind_host, bind_port
    )
    uvicorn.run(
        "webhooks.server:app",
        host=bind_host,
        port=bind_port,
        log_level="info",
    )


@cli.command()
@click.option("--host", default=None)
@click.option("--port", default=None, type=int)
def run(host: str | None, port: int | None):
    """Start the agent daemon (webhook server + workflow engine)."""
    ctx = click.get_current_context()
    ctx.invoke(webhook_server, host=host, port=port)


if __name__ == "__main__":
    cli()
