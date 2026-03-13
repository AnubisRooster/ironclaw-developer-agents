"""Tests for cli/chat.py and main.py entry point."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner


class TestCLIChat:
    def test_start_chat_function_exists(self):
        from cli.chat import start_chat
        assert callable(start_chat)

    def test_print_banner(self, capsys):
        from cli.chat import _print_banner
        _print_banner()


class TestMainCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_cli_help(self, runner, env_secrets):
        from main import cli
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "chat" in result.output
        assert "webhook-server" in result.output
        assert "run" in result.output

    def test_chat_subcommand_help(self, runner, env_secrets):
        from main import cli
        result = runner.invoke(cli, ["chat", "--help"])
        assert result.exit_code == 0
        assert "interactive chat" in result.output.lower()

    def test_webhook_server_subcommand_help(self, runner, env_secrets):
        from main import cli
        result = runner.invoke(cli, ["webhook-server", "--help"])
        assert result.exit_code == 0
        assert "--host" in result.output
        assert "--port" in result.output

    def test_run_subcommand_help(self, runner, env_secrets):
        from main import cli
        result = runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0

    def test_no_subcommand_shows_help(self, runner, env_secrets):
        from main import cli
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert "chat" in result.output

    def test_build_orchestrator(self, env_secrets):
        with patch("integrations.slack.WebClient"), \
             patch("integrations.github_integration.Github"), \
             patch("integrations.jira_integration.JIRA"), \
             patch("integrations.confluence.Confluence"), \
             patch("integrations.jenkins.jenkins.Jenkins"), \
             patch("integrations.gmail.os.path.exists", return_value=False), \
             patch("agent.ironclaw_client.IronClawClient"):
            from main import _build_orchestrator
            orch = _build_orchestrator()
            tools = orch._registry.list_tool_names()
            assert len(tools) > 0

    def test_setup_logging(self, env_secrets, tmp_path, monkeypatch):
        monkeypatch.setattr("main._PROJECT_ROOT", tmp_path)
        from main import _setup_logging
        _setup_logging()
        assert (tmp_path / "logs").exists()
        assert (tmp_path / "logs" / "agent.log").exists()
