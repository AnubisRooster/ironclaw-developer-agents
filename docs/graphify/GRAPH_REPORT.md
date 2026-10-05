# Graph Report - ironclaw-developer-agents  (2026-10-05)

## Corpus Check
- 59 files · ~110,528 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 2, .example 1, .jsonl 1)

## Summary
- 595 nodes · 1120 edges · 39 communities (14 shown, 25 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 66 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- IronClawClient
- get_secrets()
- test_integrations.py
- ToolSchemaRegistry
- graphify_pipeline.py
- ConversationMemory
- confluence.py
- GitHubIntegration
- AgentEvent
- test_database.py
- main.py
- test_cli_main.py
- SlackIntegration
- redact()
- WorkflowDefinition
- cli()
- EventBus
- JiraIntegration
- postgres.py
- JenkinsIntegration
- test_workflows.py
- WorkflowEngine
- orchestrator.py
- load_all_workflows()
- AgentMemory
- ToolResult
- TestGitHubWebhook

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

### Community 0 - "IronClawClient"
Cohesion: 0.05
Nodes (9): IronClawClient, Orchestrator, ActionPlan, Planner, PlanStep, TestIronClawClient, TestOrchestrator, TestPlanModels (+1 more)

### Community 1 - "get_secrets()"
Cohesion: 0.07
Nodes (16): EventSource, AppSecrets, get_secrets(), verify_webhook_signature(), TestAppSecrets, TestVerifyWebhookSignature, client(), TestHealthEndpoint (+8 more)

### Community 2 - "test_integrations.py"
Cohesion: 0.07
Nodes (4): GmailIntegration, TestGmailIntegration, TestJenkinsIntegration, TestJiraIntegration

### Community 3 - "ToolSchemaRegistry"
Cohesion: 0.08
Nodes (5): TestToolSchema, TestToolSchemaRegistry, RegisteredTool, ToolSchema, ToolSchemaRegistry

### Community 4 - "graphify_pipeline.py"
Cohesion: 0.08
Nodes (3): env_secrets(), _reset_db_singletons(), _reset_secrets_cache()

### Community 6 - "confluence.py"
Cohesion: 0.11
Nodes (3): ConfluenceIntegration, _strip_html(), TestConfluenceIntegration

### Community 8 - "AgentEvent"
Cohesion: 0.18
Nodes (3): AgentEvent, TestAgentEvent, TestEventBus

### Community 10 - "test_database.py"
Cohesion: 0.19
Nodes (6): Base, Event, WorkflowRun, db_session(), TestEventModel, TestWorkflowRunModel

### Community 11 - "main.py"
Cohesion: 0.18
Nodes (5): _build_orchestrator(), chat(), run(), _setup_workflow_engine(), webhook_server()

### Community 12 - "test_cli_main.py"
Cohesion: 0.15
Nodes (4): _chat_loop(), _print_banner(), start_chat(), TestCLIChat

### Community 14 - "redact()"
Cohesion: 0.18
Nodes (4): redact(), RedactingFilter, TestRedact, TestRedactingFilter

### Community 15 - "WorkflowDefinition"
Cohesion: 0.23
Nodes (5): TestWorkflowAction, TestWorkflowDefinition, TestWorkflowEngine, WorkflowAction, WorkflowDefinition

### Community 17 - "cli()"
Cohesion: 0.18
Nodes (3): cli(), _setup_logging(), TestMainCLI

### Community 20 - "postgres.py"
Cohesion: 0.20
Nodes (3): check_connection(), get_engine(), get_session_factory()

## Knowledge Gaps
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ToolSchemaRegistry` connect `ToolSchemaRegistry` to `IronClawClient`, `main.py`, `WorkflowDefinition`, `typing`, `test_workflows.py`, `WorkflowEngine`, `orchestrator.py`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `AgentEvent` (e.g. with `EventBus` and `TestAgentEvent`) actually correct?**
  _`AgentEvent` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `IronClawClient` be split into smaller, more focused modules?**
  _Cohesion score 0.0546448087431694 - nodes in this community are weakly interconnected._
- **Why does `get_secrets()` connect `get_secrets()` to `IronClawClient`, `test_integrations.py`, `graphify_pipeline.py`, `confluence.py`, `GitHubIntegration`, `logging`, `main.py`, `SlackIntegration`, `JiraIntegration`, `postgres.py`, `JenkinsIntegration`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `ToolSchemaRegistry` (e.g. with `Orchestrator` and `TestToolSchemaRegistry`) actually correct?**
  _`ToolSchemaRegistry` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `get_secrets()` be split into smaller, more focused modules?**
  _Cohesion score 0.06966618287373004 - nodes in this community are weakly interconnected._
- **Why does `Orchestrator` connect `IronClawClient` to `ToolSchemaRegistry`, `ConversationMemory`, `main.py`, `orchestrator.py`, `ToolResult`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._