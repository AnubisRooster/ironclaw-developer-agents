# Graph Report - ironclaw-developer-agents  (2026-09-06)

## Corpus Check
- Corpus is ~27,468 words - fits in a single context window. You may not need a graph.

## Summary
- 538 nodes · 956 edges · 35 communities (22 shown, 3 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 67 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- get_secrets()
- test_database.py
- ToolSchemaRegistry
- IronClawClient
- test_agent.py
- ConversationMemory
- GmailIntegration
- cli()
- EventBus
- GitHubIntegration
- JiraIntegration
- test_workflows.py
- AgentEvent
- test_webhooks.py
- test_integrations.py
- main.py
- load_all_workflows()
- ConfluenceIntegration
- JenkinsIntegration
- conftest.py
- TestJenkinsIntegration
- fixture
- .subscribe()
- .run_workflow()
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
- `Orchestrator` --uses--> `ToolSchemaRegistry`  [INFERRED]
  agent/orchestrator.py → tools/registry.py
- `TestOrchestrator` --uses--> `Orchestrator`  [INFERRED]
  tests/test_agent.py → agent/orchestrator.py
- `EventBus` --uses--> `Event`  [INFERRED]
  events/bus.py → database/models.py

## Import Cycles
- None detected.

## Communities (35 total, 3 thin omitted)

### Community 0 - "get_secrets()"
Cohesion: 0.06
Nodes (35): BaseSettings, Enum, EventSource, get, Initialize Confluence client with url, username, and api_token from secrets., Jenkins integration using python-jenkins., Initialize Jenkins client with url, username, and password from secrets., Slack integration using slack_sdk WebClient. (+27 more)

### Community 1 - "test_database.py"
Cohesion: 0.08
Nodes (28): Conversation memory module with optional PostgreSQL persistence., Load history from the ``agent_memory`` PostgreSQL table for this session., AgentMemory, Base, Event, SQLAlchemy ORM models for PostgreSQL. Tables: events — all incoming events…, ToolResult, WorkflowRun (+20 more)

### Community 2 - "ToolSchemaRegistry"
Cohesion: 0.08
Nodes (19): asyncio, Tests for tools/registry.py — Tool Schema Registry., TestToolSchema, TestToolSchemaRegistry, Any, BaseModel, Tool Schema Registry — dynamic registration of tools with JSON schema…, Schema definition for a registered tool. (+11 more)

### Community 3 - "IronClawClient"
Cohesion: 0.08
Nodes (18): IronClawClient, Any, IronClaw client — communicates with the Rust-based OpenClaw runtime via HTTP.…, Ask IronClaw to summarise arbitrary content. Args: content: Raw text to…, Check IronClaw runtime health., HTTP client for the IronClaw (Rust OpenClaw) reasoning runtime. All reasoning —…, Send a chat request to IronClaw and return the full response. Args: messages:…, Ask IronClaw to decompose a request into an action plan. Args: user_request:… (+10 more)

### Community 4 - "test_agent.py"
Cohesion: 0.12
Nodes (16): ActionPlan, Planner, PlanStep, Any, BaseModel, Workflow planning module — delegates plan creation to IronClaw., A single step in an action plan., Structured plan for executing a user request across multiple tool calls. (+8 more)

### Community 5 - "ConversationMemory"
Cohesion: 0.10
Nodes (10): ConversationMemory, Any, Stores conversation history for the agent and provides context retrieval. In-…, Append a message to the conversation history. Args: role: Message role…, Return the most recent messages for context. Args: max_messages: Maximum number…, Return a one-line summary of the conversation., Clear all conversation history., Return messages in ``[{role, content}]`` format for IronClaw. (+2 more)

### Community 6 - "GmailIntegration"
Cohesion: 0.12
Nodes (13): GmailIntegration, Any, retry, Gmail integration using google-api-python-client., Get all messages in a thread. Args: thread_id: Gmail thread ID. Returns: Dict…, Send an email. Args: to: Recipient email address. subject: Email subject. body:…, Get thread content as raw text for LLM processing. Args: thread_id: Gmail…, Gmail integration for reading, sending, and summarizing emails. (+5 more)

### Community 7 - "cli()"
Cohesion: 0.10
Nodes (14): _chat_loop(), _print_banner(), Interactive CLI chat interface for the developer automation agent., Run the interactive prompt loop., group, cli(), Configure structured logging with redaction filter., Claw Agent — Developer Automation Agent powered by IronClaw. (+6 more)

### Community 8 - "EventBus"
Cohesion: 0.12
Nodes (14): PostgreSQL connection management using SQLAlchemy + psycopg2. Provides engine…, Context manager that commits on success and rolls back on error., session_scope(), EventBus, In-process async event bus with topic-based pub/sub and PostgreSQL persistence., Simple topic-based publish/subscribe event bus., Publish an event — persists to PostgreSQL and dispatches to subscribers., Write event to the PostgreSQL database. (+6 more)

### Community 9 - "GitHubIntegration"
Cohesion: 0.12
Nodes (12): GitHubIntegration, Any, retry, GitHub integration using PyGithub., Create a new branch from an existing branch. Args: repo: Repository in…, Get recent commits, PRs, and issues from the last N days. Args: repo:…, GitHub integration for issues, PRs, branches, and repository activity., Initialize GitHub client with token from secrets. (+4 more)

### Community 10 - "JiraIntegration"
Cohesion: 0.12
Nodes (11): JiraIntegration, Any, retry, Jira integration using the jira Python SDK., Get ticket details. Args: ticket_key: Jira issue key. Returns: Dict with key,…, Jira integration for tickets, updates, and remote links., Initialize Jira client with server URL and basic auth from secrets., Create a Jira ticket. Args: project: Project key. summary: Ticket… (+3 more)

### Community 11 - "test_workflows.py"
Cohesion: 0.20
Nodes (11): asyncio, Tests for workflows/loader.py and workflows/engine.py., TestWorkflowAction, TestWorkflowDefinition, TestWorkflowEngine, BaseModel, Load and validate YAML workflow definitions., A single step inside a workflow. (+3 more)

### Community 12 - "AgentEvent"
Cohesion: 0.20
Nodes (7): AgentEvent, BaseModel, Canonical event that flows through the internal bus., asyncio, Tests for events/types.py and events/bus.py., TestAgentEvent, TestEventBus

### Community 13 - "test_webhooks.py"
Cohesion: 0.11
Nodes (8): client(), fixture, Tests for webhooks/server.py — FastAPI endpoint validation., TestGitHubWebhook, TestHealthEndpoint, TestJenkinsWebhook, TestJiraWebhook, TestSlackWebhook

### Community 14 - "test_integrations.py"
Cohesion: 0.16
Nodes (9): Any, retry, Slack integration for messaging and channel history., Post a message to a Slack channel. Args: channel: Channel ID or name (e.g.…, Respond to a slash command via response_url. Args: response_url: The…, Read recent messages from a Slack channel. Args: channel: Channel ID (e.g.…, SlackIntegration, Tests for all integration connectors. (+1 more)

### Community 15 - "main.py"
Cohesion: 0.20
Nodes (15): Entry point called from main.py for the 'chat' command., start_chat(), command, _build_orchestrator(), chat(), Developer Automation Agent — main entry point. CLI commands: claw-agent chat —…, Wire the workflow engine to the event bus with orchestrator tools., Start an interactive chat session with the agent. (+7 more)

### Community 16 - "load_all_workflows()"
Cohesion: 0.17
Nodes (8): Path, TestLoadAllWorkflows, TestLoadWorkflow, Load workflow definitions and subscribe triggers to the event bus., load_all_workflows(), load_workflow(), Parse a single YAML workflow file into a WorkflowDefinition., Scan a directory for .yaml workflow files and load them all.

### Community 17 - "ConfluenceIntegration"
Cohesion: 0.20
Nodes (10): ConfluenceIntegration, Any, retry, Confluence integration using atlassian-python-api., Create a Confluence page. Args: space: Space key. title: Page title. body: Page…, Remove HTML tags and decode entities., Confluence integration for search, pages, and content., CQL search for Confluence documents. Args: query: CQL search query. limit:… (+2 more)

### Community 18 - "JenkinsIntegration"
Cohesion: 0.29
Nodes (7): JenkinsIntegration, Any, retry, Get console output (last 5000 chars) for a build. Args: job_name: Name of the…, Jenkins integration for triggering builds and fetching status/logs., Trigger a Jenkins build. Args: job_name: Name of the job to build. parameters:…, Get status of latest or specific build. Args: job_name: Name of the job.…

### Community 19 - "conftest.py"
Cohesion: 0.28
Nodes (8): env_secrets(), fixture, Shared fixtures for the test suite., Clear the lru_cache on get_secrets between tests so env changes take effect., Reset the database singletons between tests., Set a minimal .env-like set of secrets for testing., _reset_db_singletons(), _reset_secrets_cache()

### Community 22 - ".subscribe()"
Cohesion: 0.40
Nodes (3): Register a handler for a specific event type., Register a handler that receives every event., Subscriber

### Community 23 - ".run_workflow()"
Cohesion: 0.40
Nodes (3): Any, Dispatch a matching workflow when an event fires., Execute every action in a workflow sequentially.

## Knowledge Gaps
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_secrets()` connect `get_secrets()` to `test_database.py`, `IronClawClient`, `GmailIntegration`, `EventBus`, `GitHubIntegration`, `JiraIntegration`, `test_webhooks.py`, `main.py`, `ConfluenceIntegration`, `conftest.py`?**
  _High betweenness centrality (0.212) - this node is a cross-community bridge._
- **Why does `ToolSchemaRegistry` connect `ToolSchemaRegistry` to `test_workflows.py`, `EventBus`, `IronClawClient`, `main.py`?**
  _High betweenness centrality (0.188) - this node is a cross-community bridge._
- **Why does `Orchestrator` connect `IronClawClient` to `test_database.py`, `ToolSchemaRegistry`, `test_agent.py`, `ConversationMemory`, `main.py`?**
  _High betweenness centrality (0.163) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `AgentEvent` (e.g. with `EventBus` and `TestAgentEvent`) actually correct?**
  _`AgentEvent` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `ToolSchemaRegistry` (e.g. with `Orchestrator` and `TestToolSchemaRegistry`) actually correct?**
  _`ToolSchemaRegistry` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ConversationMemory` (e.g. with `AgentMemory` and `Orchestrator`) actually correct?**
  _`ConversationMemory` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `IronClawClient` (e.g. with `Orchestrator` and `TestIronClawClient`) actually correct?**
  _`IronClawClient` has 2 INFERRED edges - model-reasoned connections that need verification._