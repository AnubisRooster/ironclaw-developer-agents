# Graph Report - ironclaw-developer-agents  (2026-09-28)

## Corpus Check
- 59 files · ~110,670 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 2, .example 1, .jsonl 1)

## Summary
- 595 nodes · 1106 edges · 25 communities (15 shown, 10 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 66 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- AgentEvent
- get_secrets()
- IronClawClient
- engine.py
- test_integrations.py
- ToolSchemaRegistry
- main.py
- ConversationMemory
- graphify_pipeline.py
- GitHubIntegration
- test_webhooks.py
- ConfluenceIntegration
- SlackIntegration
- redact()
- JiraIntegration

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
- `EventBus` --uses--> `Event`  [INFERRED]
  events/bus.py → database/models.py
- `WorkflowEngine` --uses--> `WorkflowRun`  [INFERRED]
  workflows/engine.py → database/models.py

## Import Cycles
- None detected.

## Communities (25 total, 10 thin omitted)

### Community 0 - "AgentEvent"
Cohesion: 0.05
Nodes (38): EventBus, Simple topic-based publish/subscribe event bus., Register a handler for a specific event type., Register a handler that receives every event., Publish an event — persists to PostgreSQL and dispatches to subscribers., Write event to the PostgreSQL database., AgentEvent, BaseModel (+30 more)

### Community 1 - "get_secrets()"
Cohesion: 0.06
Nodes (53): IronClaw client — communicates with the Rust-based OpenClaw runtime via HTTP.…, atlassian, base64, BaseSettings, email_mime_text, Enum, EventSource, fastapi (+45 more)

### Community 2 - "IronClawClient"
Cohesion: 0.05
Nodes (32): IronClawClient, Any, Ask IronClaw to summarise arbitrary content. Args: content: Raw text to…, Check IronClaw runtime health., HTTP client for the IronClaw (Rust OpenClaw) reasoning runtime. All reasoning —…, Send a chat request to IronClaw and return the full response. Args: messages:…, Ask IronClaw to decompose a request into an action plan. Args: user_request:…, Orchestrator (+24 more)

### Community 3 - "engine.py"
Cohesion: 0.06
Nodes (44): Conversation memory module with optional PostgreSQL persistence., Write current history to the ``agent_memory`` PostgreSQL table., Agent orchestrator — the central coordinator of the Developer Automation Agent.…, Execute a tool and persist the result. Args: tool_name: Name of the registered…, collections, contextlib, AgentMemory, Base (+36 more)

### Community 4 - "test_integrations.py"
Cohesion: 0.05
Nodes (24): GmailIntegration, Any, retry, Get all messages in a thread. Args: thread_id: Gmail thread ID. Returns: Dict…, Send an email. Args: to: Recipient email address. subject: Email subject. body:…, Get thread content as raw text for LLM processing. Args: thread_id: Gmail…, Gmail integration for reading, sending, and summarizing emails., Initialize Gmail API service using credentials from secrets. (+16 more)

### Community 5 - "ToolSchemaRegistry"
Cohesion: 0.06
Nodes (25): asyncio, pytest, asyncio, Tests for tools/registry.py — Tool Schema Registry., TestToolSchema, TestToolSchemaRegistry, fixture, Any (+17 more)

### Community 6 - "main.py"
Cohesion: 0.06
Nodes (37): _chat_loop(), _print_banner(), Interactive CLI chat interface for the developer automation agent., Run the interactive prompt loop., Entry point called from main.py for the 'chat' command., start_chat(), click, click_testing (+29 more)

### Community 7 - "ConversationMemory"
Cohesion: 0.10
Nodes (10): ConversationMemory, Any, Stores conversation history for the agent and provides context retrieval. In-…, Append a message to the conversation history. Args: role: Message role…, Return the most recent messages for context. Args: max_messages: Maximum number…, Return a one-line summary of the conversation., Clear all conversation history., Return messages in ``[{role, content}]`` format for IronClaw. (+2 more)

### Community 8 - "graphify_pipeline.py"
Cohesion: 0.10
Nodes (20): graphify_analyze, graphify_build, graphify_cluster, graphify_detect, graphify_export, graphify_extract, graphify_llm, graphify_report (+12 more)

### Community 9 - "GitHubIntegration"
Cohesion: 0.13
Nodes (11): GitHubIntegration, Any, retry, Create a new branch from an existing branch. Args: repo: Repository in…, Get recent commits, PRs, and issues from the last N days. Args: repo:…, GitHub integration for issues, PRs, branches, and repository activity., Initialize GitHub client with token from secrets., Create a GitHub issue. Args: repo: Repository in owner/name format. title:… (+3 more)

### Community 10 - "test_webhooks.py"
Cohesion: 0.11
Nodes (9): fastapi_testclient, client(), fixture, Tests for webhooks/server.py — FastAPI endpoint validation., TestGitHubWebhook, TestHealthEndpoint, TestJenkinsWebhook, TestJiraWebhook (+1 more)

### Community 11 - "ConfluenceIntegration"
Cohesion: 0.13
Nodes (11): ConfluenceIntegration, Any, retry, Create a Confluence page. Args: space: Space key. title: Page title. body: Page…, Remove HTML tags and decode entities., Confluence integration for search, pages, and content., Initialize Confluence client with url, username, and api_token from secrets., CQL search for Confluence documents. Args: query: CQL search query. limit:… (+3 more)

### Community 12 - "SlackIntegration"
Cohesion: 0.15
Nodes (9): Any, retry, Slack integration for messaging and channel history., Initialize Slack WebClient with token from secrets., Post a message to a Slack channel. Args: channel: Channel ID or name (e.g.…, Respond to a slash command via response_url. Args: response_url: The…, Read recent messages from a Slack channel. Args: channel: Channel ID (e.g.…, SlackIntegration (+1 more)

### Community 13 - "redact()"
Cohesion: 0.18
Nodes (7): LogRecord, Logging filter that scrubs sensitive patterns from log records., Replace known secret patterns with <REDACTED>., redact(), RedactingFilter, TestRedact, TestRedactingFilter

### Community 14 - "JiraIntegration"
Cohesion: 0.21
Nodes (9): JiraIntegration, Any, retry, Get ticket details. Args: ticket_key: Jira issue key. Returns: Dict with key,…, Jira integration for tickets, updates, and remote links., Initialize Jira client with server URL and basic auth from secrets., Create a Jira ticket. Args: project: Project key. summary: Ticket…, Update ticket fields. Args: ticket_key: Jira issue key (e.g. PROJ-123).… (+1 more)

## Knowledge Gaps
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ToolSchemaRegistry` connect `ToolSchemaRegistry` to `AgentEvent`, `IronClawClient`, `engine.py`, `main.py`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **Why does `get_secrets()` connect `get_secrets()` to `IronClawClient`, `engine.py`, `test_integrations.py`, `main.py`, `graphify_pipeline.py`, `GitHubIntegration`, `test_webhooks.py`, `ConfluenceIntegration`, `SlackIntegration`, `JiraIntegration`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Why does `Orchestrator` connect `IronClawClient` to `engine.py`, `ToolSchemaRegistry`, `main.py`, `ConversationMemory`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `AgentEvent` (e.g. with `EventBus` and `TestAgentEvent`) actually correct?**
  _`AgentEvent` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `ToolSchemaRegistry` (e.g. with `Orchestrator` and `TestToolSchemaRegistry`) actually correct?**
  _`ToolSchemaRegistry` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ConversationMemory` (e.g. with `AgentMemory` and `Orchestrator`) actually correct?**
  _`ConversationMemory` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `IronClawClient` (e.g. with `Orchestrator` and `TestIronClawClient`) actually correct?**
  _`IronClawClient` has 2 INFERRED edges - model-reasoned connections that need verification._