# Graph Report - ironclaw-developer-agents  (2026-10-26)

## Corpus Check
- 59 files · ~76,699 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 2, .example 1, .jsonl 1)

## Summary
- 658 nodes · 1267 edges · 30 communities (15 shown, 15 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 154 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- IronClawClient
- secrets.py
- ToolSchemaRegistry
- main.py
- get_secrets()
- AgentEvent
- test_integrations.py
- test_workflows.py
- integrations
- ConversationMemory
- test_database.py
- GmailIntegration
- graphify_pipeline.py
- GitHubIntegration
- JenkinsIntegration
- JiraIntegration
- redact()
- build_failed.yaml
- jira_created.yaml
- pr_opened.yaml

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

## Communities (30 total, 15 thin omitted)

### Community 0 - "IronClawClient"
Cohesion: 0.06
Nodes (9): IronClawClient, Orchestrator, ActionPlan, Planner, PlanStep, TestIronClawClient, TestOrchestrator, TestPlanModels (+1 more)

### Community 1 - "secrets.py"
Cohesion: 0.05
Nodes (6): check_connection(), get_engine(), get_session(), get_session_factory(), session_scope(), _strip_html()

### Community 2 - "ToolSchemaRegistry"
Cohesion: 0.07
Nodes (6): TestToolSchema, TestToolSchemaRegistry, RegisteredTool, ToolSchema, ToolSchemaRegistry, WorkflowEngine

### Community 3 - "main.py"
Cohesion: 0.06
Nodes (12): _chat_loop(), _print_banner(), start_chat(), _build_orchestrator(), chat(), cli(), run(), _setup_logging() (+4 more)

### Community 4 - "get_secrets()"
Cohesion: 0.07
Nodes (16): AppSecrets, get_secrets(), verify_webhook_signature(), TestAppSecrets, TestVerifyWebhookSignature, client(), TestGitHubWebhook, TestHealthEndpoint (+8 more)

### Community 5 - "AgentEvent"
Cohesion: 0.09
Nodes (5): EventBus, AgentEvent, EventSource, TestAgentEvent, TestEventBus

### Community 6 - "test_integrations.py"
Cohesion: 0.08
Nodes (4): ConfluenceIntegration, SlackIntegration, TestConfluenceIntegration, TestSlackIntegration

### Community 7 - "test_workflows.py"
Cohesion: 0.11
Nodes (9): TestLoadAllWorkflows, TestLoadWorkflow, TestWorkflowAction, TestWorkflowDefinition, TestWorkflowEngine, load_all_workflows(), load_workflow(), WorkflowAction (+1 more)

### Community 8 - "integrations"
Cohesion: 0.07
Nodes (29): agent, log_file, log_level, name, version, enabled, database, url (+21 more)

### Community 10 - "test_database.py"
Cohesion: 0.14
Nodes (10): AgentMemory, Base, Event, ToolResult, WorkflowRun, db_session(), TestAgentMemoryModel, TestEventModel (+2 more)

### Community 12 - "graphify_pipeline.py"
Cohesion: 0.10
Nodes (3): env_secrets(), _reset_db_singletons(), _reset_secrets_cache()

### Community 16 - "redact()"
Cohesion: 0.20
Nodes (4): redact(), RedactingFilter, TestRedact, TestRedactingFilter

### Community 17 - "build_failed.yaml"
Cohesion: 0.18
Nodes (10): actions, args, description, on_failure, tool, channel, description, enabled (+2 more)

### Community 18 - "jira_created.yaml"
Cohesion: 0.18
Nodes (10): actions, args, description, on_failure, tool, channel, description, enabled (+2 more)

### Community 19 - "pr_opened.yaml"
Cohesion: 0.18
Nodes (10): actions, args, description, on_failure, tool, channel, description, enabled (+2 more)

## Knowledge Gaps
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ToolSchemaRegistry` connect `ToolSchemaRegistry` to `IronClawClient`, `secrets.py`, `main.py`, `AgentEvent`, `test_workflows.py`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `AgentEvent` (e.g. with `EventBus` and `TestAgentEvent`) actually correct?**
  _`AgentEvent` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `IronClawClient` be split into smaller, more focused modules?**
  _Cohesion score 0.05913461538461538 - nodes in this community are weakly interconnected._
- **Why does `get_secrets()` connect `get_secrets()` to `IronClawClient`, `secrets.py`, `main.py`, `test_integrations.py`, `GmailIntegration`, `graphify_pipeline.py`, `GitHubIntegration`, `JenkinsIntegration`, `JiraIntegration`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `ToolSchemaRegistry` (e.g. with `Orchestrator` and `TestToolSchemaRegistry`) actually correct?**
  _`ToolSchemaRegistry` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `secrets.py` be split into smaller, more focused modules?**
  _Cohesion score 0.051715309779825906 - nodes in this community are weakly interconnected._
- **Why does `Orchestrator` connect `IronClawClient` to `secrets.py`, `ToolSchemaRegistry`, `main.py`, `ConversationMemory`, `test_database.py`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._