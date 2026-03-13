"""Developer Automation Agent — main entry point.

CLI commands:
    claw-agent chat            — interactive chat with the agent
    claw-agent run             — start the webhook server (background daemon mode)
    claw-agent webhook-server  — start the webhook server (foreground)
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import click
import uvicorn
from dotenv import load_dotenv

load_dotenv()

# Ensure the project root is on sys.path so sibling package imports work,
# especially when running from a PyInstaller bundle.
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
    from agent.orchestrator import Orchestrator
    from integrations.slack import SlackIntegration
    from integrations.github_integration import GitHubIntegration
    from integrations.jira_integration import JiraIntegration
    from integrations.confluence import ConfluenceIntegration
    from integrations.jenkins import JenkinsIntegration
    from integrations.gmail import GmailIntegration

    orch = Orchestrator()
    secrets = get_secrets()

    # --- Slack tools ---
    if secrets.slack_bot_token:
        slack = SlackIntegration()
        orch.register_tool("slack.send_message", slack.send_message, "Send a message to a Slack channel")
        orch.register_tool("slack.read_channel_history", slack.read_channel_history, "Read recent messages from a Slack channel")

    # --- GitHub tools ---
    if secrets.github_token:
        gh = GitHubIntegration()
        orch.register_tool("github.create_issue", gh.create_issue, "Create a GitHub issue")
        orch.register_tool("github.summarize_pull_request", gh.summarize_pull_request, "Summarize a GitHub pull request")
        orch.register_tool("github.comment_on_pr", gh.comment_on_pr, "Comment on a GitHub pull request")
        orch.register_tool("github.create_branch", gh.create_branch, "Create a new Git branch")
        orch.register_tool("github.get_repo_activity", gh.get_repo_activity, "Get recent repository activity")

    # --- Jira tools ---
    if secrets.jira_api_token:
        jira = JiraIntegration()
        orch.register_tool("jira.create_ticket", jira.create_ticket, "Create a Jira ticket")
        orch.register_tool("jira.update_ticket", jira.update_ticket, "Update a Jira ticket")
        orch.register_tool("jira.link_github_issue", jira.link_github_issue, "Link a GitHub issue to a Jira ticket")
        orch.register_tool("jira.get_ticket_details", jira.get_ticket_details, "Get details of a Jira ticket")

    # --- Confluence tools ---
    if secrets.confluence_api_token:
        conf = ConfluenceIntegration()
        orch.register_tool("confluence.search_docs", conf.search_docs, "Search Confluence documentation")
        orch.register_tool("confluence.summarize_page", conf.summarize_page, "Summarize a Confluence page")
        orch.register_tool("confluence.create_page", conf.create_page, "Create a Confluence page")

    # --- Jenkins tools ---
    if secrets.jenkins_api_token:
        jenkins = JenkinsIntegration()
        orch.register_tool("jenkins.trigger_build", jenkins.trigger_build, "Trigger a Jenkins build")
        orch.register_tool("jenkins.get_build_status", jenkins.get_build_status, "Get Jenkins build status")
        orch.register_tool("jenkins.fetch_build_logs", jenkins.fetch_build_logs, "Fetch Jenkins build logs")

    # --- Gmail tools ---
    gmail = GmailIntegration()
    orch.register_tool("gmail.read_emails", gmail.read_emails, "Read emails from Gmail")
    orch.register_tool("gmail.summarize_thread", gmail.summarize_thread, "Summarize a Gmail thread")
    orch.register_tool("gmail.send_email", gmail.send_email, "Send an email via Gmail")
    orch.register_tool("gmail.extract_action_items", gmail.extract_action_items, "Extract action items from a Gmail thread")

    return orch


def _setup_workflow_engine(orchestrator):
    """Wire the workflow engine to the event bus with orchestrator tools."""
    from workflows.engine import WorkflowEngine

    engine = WorkflowEngine(workflow_dir=str(_PROJECT_ROOT / "workflows"))
    for name in orchestrator._registry.list_tools():
        tool_func = orchestrator._registry.get_tool(name)
        if tool_func:
            engine.register_tool(name, tool_func)
    engine.load()
    return engine


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Claw Agent — Developer Automation Agent."""
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
