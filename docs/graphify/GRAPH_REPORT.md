# Graph Report - ironclaw-developer-agents  (2026-09-14)

## Corpus Check
- 59 files · ~101,863 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 2, .example 1, .jsonl 1)

## Summary
- 539 nodes · 956 edges · 33 communities (18 shown, 5 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 67 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- AgentEvent
- EventBus
- ToolSchemaRegistry
- IronClawClient
- get_secrets()
- ConversationMemory
- GmailIntegration
- JiraIntegration
- test_webhooks.py
- redact()
- GitHubIntegration
- main.py
- cli()
- ConfluenceIntegration
- SlackIntegration
- test_cli_main.py
- JenkinsIntegration
- conftest.py
- fixture
- TestJenkinsIntegration
- test_integrations.py
- TestGitHubIntegration
- graphify_pipeline.py

## God Nodes (most connected - your core abstractions)
1. `AgentEvent` - 35 edges
2. `ToolSchemaRegistry` - 34 edges
3. `get_secrets()` - 32 edges
4. `ConversationMemory` - 26 edges
5. `IronClawClient` - 20 edges
6. `EventBus` - 18 edges
7. `Orchestrator` - 17 edges
8. `WorkflowEngine` - 17 edges
9. `_build_orchestrator()` - 16 edges
10. `GmailIntegration` - 15 edges

## Surprising Connections (you probably didn't know these)
- `ConversationMemory` --uses--> `AgentMemory`  [INFERRED]
  agent/memory.py → database/models.py
- `Orchestrator` --uses--> `ToolResult`  [INFERRED]
  agent/orchestrator.py → database/models.py
- `TestOrchestrator` --uses--> `Orchestrator`  [INFERRED]
  tests/test_agent.py → agent/orchestrator.py
- `WorkflowEngine` --uses--> `WorkflowRun`  [INFERRED]
  workflows/engine.py → database/models.py
- `TestEventBus` --uses--> `EventBus`  [INFERRED]
  tests/test_events.py → events/bus.py

## Import Cycles
- None detected.

## Communities (33 total, 5 thin omitted)

### Community 0 - "AgentEvent"
Cohesion: 0.06
Nodes (33): AgentEvent, BaseModel, Canonical event that flows through the internal bus., Path, asyncio, fixture, Tests for events/types.py and events/bus.py., TestAgentEvent (+25 more)

### Community 1 - "EventBus"
Cohesion: 0.06
Nodes (41): Conversation memory module with optional PostgreSQL persistence., Write current history to the ``agent_memory`` PostgreSQL table., Agent orchestrator — the central coordinator of the Developer Automation Agent.…, AgentMemory, Base, Event, SQLAlchemy ORM models for PostgreSQL. Tables: events — all incoming events…, ToolResult (+33 more)

### Community 2 - "ToolSchemaRegistry"
Cohesion: 0.05
Nodes (27): Orchestrator, Any, Execute a tool and persist the result. Args: tool_name: Name of the registered…, Delegate summarisation to IronClaw. Registered as the ``agent.summarize`` tool…, Main agent orchestrator: manages IronClaw, memory, and tool execution. The…, Convenience method to register a tool on the embedded registry., Process a user message through the IronClaw reasoning loop. 1. Add message to…, fixture (+19 more)

### Community 3 - "IronClawClient"
Cohesion: 0.07
Nodes (24): IronClawClient, Any, Ask IronClaw to summarise arbitrary content. Args: content: Raw text to…, Check IronClaw runtime health., HTTP client for the IronClaw (Rust OpenClaw) reasoning runtime. All reasoning —…, Send a chat request to IronClaw and return the full response. Args: messages:…, Ask IronClaw to decompose a request into an action plan. Args: user_request:…, ActionPlan (+16 more)

### Community 4 - "get_secrets()"
Cohesion: 0.08
Nodes (31): IronClaw client — communicates with the Rust-based OpenClaw runtime via HTTP.…, BaseSettings, Enum, EventSource, Event type definitions for the internal event bus., get, Confluence integration using atlassian-python-api., GitHub integration using PyGithub. (+23 more)

### Community 5 - "ConversationMemory"
Cohesion: 0.10
Nodes (10): ConversationMemory, Any, Stores conversation history for the agent and provides context retrieval. In-…, Append a message to the conversation history. Args: role: Message role…, Return the most recent messages for context. Args: max_messages: Maximum number…, Return a one-line summary of the conversation., Clear all conversation history., Return messages in ``[{role, content}]`` format for IronClaw. (+2 more)

### Community 6 - "GmailIntegration"
Cohesion: 0.13
Nodes (12): GmailIntegration, Any, retry, Get all messages in a thread. Args: thread_id: Gmail thread ID. Returns: Dict…, Send an email. Args: to: Recipient email address. subject: Email subject. body:…, Get thread content as raw text for LLM processing. Args: thread_id: Gmail…, Gmail integration for reading, sending, and summarizing emails., Initialize Gmail API service using credentials from secrets. (+4 more)

### Community 7 - "JiraIntegration"
Cohesion: 0.14
Nodes (10): JiraIntegration, Any, retry, Get ticket details. Args: ticket_key: Jira issue key. Returns: Dict with key,…, Jira integration for tickets, updates, and remote links., Initialize Jira client with server URL and basic auth from secrets., Create a Jira ticket. Args: project: Project key. summary: Ticket…, Update ticket fields. Args: ticket_key: Jira issue key (e.g. PROJ-123).… (+2 more)

### Community 8 - "test_webhooks.py"
Cohesion: 0.11
Nodes (8): client(), fixture, Tests for webhooks/server.py — FastAPI endpoint validation., TestGitHubWebhook, TestHealthEndpoint, TestJenkinsWebhook, TestJiraWebhook, TestSlackWebhook

### Community 9 - "redact()"
Cohesion: 0.18
Nodes (7): LogRecord, Logging filter that scrubs sensitive patterns from log records., Replace known secret patterns with <REDACTED>., redact(), RedactingFilter, TestRedact, TestRedactingFilter

### Community 10 - "GitHubIntegration"
Cohesion: 0.19
Nodes (10): GitHubIntegration, Any, retry, Create a new branch from an existing branch. Args: repo: Repository in…, Get recent commits, PRs, and issues from the last N days. Args: repo:…, GitHub integration for issues, PRs, branches, and repository activity., Initialize GitHub client with token from secrets., Create a GitHub issue. Args: repo: Repository in owner/name format. title:… (+2 more)

### Community 11 - "main.py"
Cohesion: 0.21
Nodes (13): command, _build_orchestrator(), chat(), Developer Automation Agent — main entry point. CLI commands: claw-agent chat —…, Wire the workflow engine to the event bus with orchestrator tools., Start an interactive chat session with the agent., Start the webhook server in the foreground., Start the agent daemon (webhook server + workflow engine). (+5 more)

### Community 12 - "cli()"
Cohesion: 0.18
Nodes (8): group, cli(), Configure structured logging with redaction filter., Claw Agent — Developer Automation Agent powered by IronClaw., _setup_logging(), pass_context, fixture, TestMainCLI

### Community 13 - "ConfluenceIntegration"
Cohesion: 0.19
Nodes (10): ConfluenceIntegration, Any, retry, Create a Confluence page. Args: space: Space key. title: Page title. body: Page…, Remove HTML tags and decode entities., Confluence integration for search, pages, and content., Initialize Confluence client with url, username, and api_token from secrets., CQL search for Confluence documents. Args: query: CQL search query. limit:… (+2 more)

### Community 14 - "SlackIntegration"
Cohesion: 0.21
Nodes (8): Any, retry, Slack integration for messaging and channel history., Initialize Slack WebClient with token from secrets., Post a message to a Slack channel. Args: channel: Channel ID or name (e.g.…, Respond to a slash command via response_url. Args: response_url: The…, Read recent messages from a Slack channel. Args: channel: Channel ID (e.g.…, SlackIntegration

### Community 15 - "test_cli_main.py"
Cohesion: 0.24
Nodes (8): _chat_loop(), _print_banner(), Interactive CLI chat interface for the developer automation agent., Run the interactive prompt loop., Entry point called from main.py for the 'chat' command., start_chat(), Tests for cli/chat.py and main.py entry point., TestCLIChat

### Community 16 - "JenkinsIntegration"
Cohesion: 0.23
Nodes (8): JenkinsIntegration, Any, retry, Get console output (last 5000 chars) for a build. Args: job_name: Name of the…, Jenkins integration for triggering builds and fetching status/logs., Initialize Jenkins client with url, username, and password from secrets., Trigger a Jenkins build. Args: job_name: Name of the job to build. parameters:…, Get status of latest or specific build. Args: job_name: Name of the job.…

### Community 17 - "conftest.py"
Cohesion: 0.28
Nodes (8): env_secrets(), fixture, Shared fixtures for the test suite., Clear the lru_cache on get_secrets between tests so env changes take effect., Reset the database singletons between tests., Set a minimal .env-like set of secrets for testing., _reset_db_singletons(), _reset_secrets_cache()

## Knowledge Gaps
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_secrets()` connect `get_secrets()` to `EventBus`, `IronClawClient`, `GmailIntegration`, `JiraIntegration`, `test_webhooks.py`, `GitHubIntegration`, `main.py`, `ConfluenceIntegration`, `SlackIntegration`, `JenkinsIntegration`, `conftest.py`?**
  _High betweenness centrality (0.211) - this node is a cross-community bridge._
- **Why does `ToolSchemaRegistry` connect `ToolSchemaRegistry` to `AgentEvent`, `EventBus`, `main.py`?**
  _High betweenness centrality (0.190) - this node is a cross-community bridge._
- **Why does `Orchestrator` connect `ToolSchemaRegistry` to `main.py`, `EventBus`, `IronClawClient`, `ConversationMemory`?**
  _High betweenness centrality (0.163) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `AgentEvent` (e.g. with `EventBus` and `TestAgentEvent`) actually correct?**
  _`AgentEvent` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `ToolSchemaRegistry` (e.g. with `Orchestrator` and `TestToolSchemaRegistry`) actually correct?**
  _`ToolSchemaRegistry` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ConversationMemory` (e.g. with `AgentMemory` and `Orchestrator`) actually correct?**
  _`ConversationMemory` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `IronClawClient` (e.g. with `Orchestrator` and `TestIronClawClient`) actually correct?**
  _`IronClawClient` has 2 INFERRED edges - model-reasoned connections that need verification._