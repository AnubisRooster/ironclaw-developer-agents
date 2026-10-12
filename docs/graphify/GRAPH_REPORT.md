# Graph Report - ironclaw-developer-agents  (2026-10-12)

## Corpus Check
- 59 files · ~110,734 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 2, .example 1, .jsonl 1)

## Summary
- 595 nodes · 1162 edges · 39 communities (14 shown, 25 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 108 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- logging
- IronClawClient
- ToolSchemaRegistry
- ConversationMemory
- test_integrations.py
- confluence.py
- graphify_pipeline.py
- GitHubIntegration
- AgentEvent
- test_webhooks.py
- main.py
- test_cli_main.py
- SlackIntegration
- redact()
- WorkflowDefinition
- server.py
- cli()
- EventBus
- JiraIntegration
- get_secrets()
- JenkinsIntegration
- test_workflows.py
- WorkflowEngine
- load_all_workflows()
- TestJiraIntegration
- TestJenkinsIntegration
- verify_webhook_signature()

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

## Communities (39 total, 25 thin omitted)

### Community 0 - "logging"
Cohesion: 0.05
Nodes (15): AgentMemory, Base, Event, ToolResult, WorkflowRun, check_connection(), get_engine(), get_session() (+7 more)

### Community 1 - "IronClawClient"
Cohesion: 0.06
Nodes (9): IronClawClient, Orchestrator, ActionPlan, Planner, PlanStep, TestIronClawClient, TestOrchestrator, TestPlanModels (+1 more)

### Community 2 - "ToolSchemaRegistry"
Cohesion: 0.10
Nodes (5): TestToolSchema, TestToolSchemaRegistry, RegisteredTool, ToolSchema, ToolSchemaRegistry

### Community 5 - "confluence.py"
Cohesion: 0.11
Nodes (3): ConfluenceIntegration, _strip_html(), TestConfluenceIntegration

### Community 6 - "graphify_pipeline.py"
Cohesion: 0.10
Nodes (3): env_secrets(), _reset_db_singletons(), _reset_secrets_cache()

### Community 8 - "AgentEvent"
Cohesion: 0.18
Nodes (3): AgentEvent, TestAgentEvent, TestEventBus

### Community 9 - "test_webhooks.py"
Cohesion: 0.11
Nodes (6): client(), TestGitHubWebhook, TestHealthEndpoint, TestJenkinsWebhook, TestJiraWebhook, TestSlackWebhook

### Community 10 - "main.py"
Cohesion: 0.18
Nodes (5): _build_orchestrator(), chat(), run(), _setup_workflow_engine(), webhook_server()

### Community 11 - "test_cli_main.py"
Cohesion: 0.15
Nodes (4): _chat_loop(), _print_banner(), start_chat(), TestCLIChat

### Community 13 - "redact()"
Cohesion: 0.20
Nodes (4): redact(), RedactingFilter, TestRedact, TestRedactingFilter

### Community 14 - "WorkflowDefinition"
Cohesion: 0.23
Nodes (5): TestWorkflowAction, TestWorkflowDefinition, TestWorkflowEngine, WorkflowAction, WorkflowDefinition

### Community 15 - "server.py"
Cohesion: 0.25
Nodes (6): EventSource, github_webhook(), health(), jenkins_webhook(), jira_webhook(), slack_webhook()

### Community 17 - "cli()"
Cohesion: 0.18
Nodes (3): cli(), _setup_logging(), TestMainCLI

### Community 20 - "get_secrets()"
Cohesion: 0.22
Nodes (3): AppSecrets, get_secrets(), TestAppSecrets

## Knowledge Gaps
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ToolSchemaRegistry` connect `ToolSchemaRegistry` to `logging`, `IronClawClient`, `main.py`, `WorkflowDefinition`, `test_workflows.py`, `WorkflowEngine`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `AgentEvent` (e.g. with `EventBus` and `TestAgentEvent`) actually correct?**
  _`AgentEvent` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `logging` be split into smaller, more focused modules?**
  _Cohesion score 0.05405405405405406 - nodes in this community are weakly interconnected._
- **Why does `get_secrets()` connect `get_secrets()` to `logging`, `IronClawClient`, `test_integrations.py`, `confluence.py`, `graphify_pipeline.py`, `GitHubIntegration`, `test_webhooks.py`, `main.py`, `SlackIntegration`, `server.py`, `secrets.py`, `JiraIntegration`, `JenkinsIntegration`, `gmail.py`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `ToolSchemaRegistry` (e.g. with `Orchestrator` and `TestToolSchemaRegistry`) actually correct?**
  _`ToolSchemaRegistry` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `IronClawClient` be split into smaller, more focused modules?**
  _Cohesion score 0.059562841530054644 - nodes in this community are weakly interconnected._
- **Why does `Orchestrator` connect `IronClawClient` to `logging`, `main.py`, `ToolSchemaRegistry`, `ConversationMemory`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._