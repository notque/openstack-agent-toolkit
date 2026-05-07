# ADR-001: SAP Converged Cloud Agent Toolkit Architecture

## Status

**Proposed** — 2026-05-06

## Context

We have a working [openstack-mcp-server](https://github.com/notque/openstack-mcp-server) that provides 28+ MCP tools across 8 SAP Converged Cloud services:

| Service | Project | Tools |
|---------|---------|-------|
| Compute | Nova | list servers, get server, list flavors, server actions |
| Networking | Neutron | list networks, subnets, ports, security groups |
| Block Storage | Cinder | list volumes, get volume |
| Identity | Keystone | list projects, token info, app credential CRUD |
| Quota/Usage | Limes | project/domain/cluster quota |
| Audit | Hermes | list/get audit events, list attributes |
| Metrics | Maia | PromQL query, label values, metric names |
| Registry | Keppel | list accounts, repositories, manifests |
| Endpoint Service | Archer | list/get services and endpoints |

The server handles authentication, API proxying, and response sanitization.

What's missing is the **intelligence layer** — skills, knowledge, and guardrails that teach AI agents *how* to use those tools effectively. Without this layer, agents make common mistakes:
- Creating servers without checking quota first (Limes)
- Not correlating cross-service information (e.g., server → ports → security groups)
- Misunderstanding SAP CC-specific concepts (domains, CADF events, federated registries)
- Not following security best practices (keychain storage, app credentials over passwords)
- Debugging issues without checking the audit trail (Hermes) or metrics (Maia)

AWS has released [agent-toolkit-for-aws](https://github.com/aws/agent-toolkit-for-aws) which provides a reference architecture for this pattern. We will build an equivalent purpose-built for SAP Converged Cloud.

## Decision

### Architecture: Single Plugin with Domain-Specific Skills

Since this toolkit is exclusively for SAP Converged Cloud (not vanilla OpenStack), we use a **single plugin** containing all skills. Every SAP CC user needs the full service suite — there's no "pick and choose" scenario.

```
openstack-agent-toolkit/
├── .claude-plugin/
│   └── marketplace.json              # Plugin registry
├── plugins/
│   └── sapcc/
│       ├── .claude-plugin/plugin.json
│       ├── .mcp.json                  # MCP server config
│       └── skills/
│           ├── sapcc-compute/         # Nova operations + gotchas
│           ├── sapcc-networking/      # Neutron + cross-service correlation
│           ├── sapcc-storage/         # Cinder volumes + lifecycle
│           ├── sapcc-identity/        # Keystone, domains, app credentials
│           ├── sapcc-quota/           # Limes quota management + capacity planning
│           ├── sapcc-audit/           # Hermes CADF events + compliance
│           ├── sapcc-metrics/         # Maia PromQL + alerting patterns
│           ├── sapcc-registry/        # Keppel container images + federation
│           ├── sapcc-connectivity/    # Archer endpoint services
│           └── credential-setup/      # Auth workflow (existing, enhanced)
├── rules/
│   └── sapcc-agent-rules.md           # Baseline agent behavior rules
├── knowledge/
│   ├── sapcc/
│   │   ├── services.md               # Service reference (existing)
│   │   ├── architecture.md           # Regional architecture, domain model
│   │   └── troubleshooting-flows.md  # Cross-service debugging patterns
│   └── openstack/
│       └── api-conventions.md         # Common OpenStack API patterns
├── tools/
│   └── validate.py                    # CI validation (stdlib-only)
└── docs/
    └── adr/                           # Architecture decision records
```

### Skill Inventory (10 Skills)

| Skill | MCP Tools Used | Key Content |
|-------|---------------|-------------|
| `sapcc-compute` | `nova_*` | Flavor selection, server lifecycle, gotchas (status transitions, metadata) |
| `sapcc-networking` | `neutron_*` | Network topology, port debugging, security group rules, cross-ref with nova |
| `sapcc-storage` | `cinder_*` | Volume lifecycle, attachment states, performance tiers |
| `sapcc-identity` | `keystone_*` | Domain/project model, role assignments, app credentials, service catalog |
| `sapcc-quota` | `limes_*` | Capacity planning, quota interpretation, "am I running out?" workflows |
| `sapcc-audit` | `hermes_*` | CADF event format, compliance queries, "who changed what?" workflows |
| `sapcc-metrics` | `maia_*` | PromQL patterns for SAP CC, discovering metrics, building dashboards |
| `sapcc-registry` | `keppel_*` | Image lifecycle, vulnerability scanning, cross-region federation |
| `sapcc-connectivity` | `archer_*` | Private service access, endpoint provisioning, troubleshooting |
| `credential-setup` | `keystone_*` | Guided auth setup (migrated + enhanced from current) |

### Skill Structure (from AWS reference pattern)

Each skill follows this template:

```markdown
---
name: sapcc-compute
description: >-
  Manage compute instances on SAP Converged Cloud. Covers server lifecycle,
  flavor selection, status transitions, and cross-service correlation with
  networking and storage. Use when creating, debugging, or managing VMs.
  NOT for container workloads (use sapcc-registry) or bare metal.
version: 1
metadata:
  service: [nova]
  task: [create, debug, manage]
  persona: [developer, platform-engineer]
allowed-tools: [Read]
---

# SAP CC Compute

## Service Overview
[Decision tables, quick-start commands]

## Gotchas
[Numbered list of common agent mistakes — THE most important section]

## Common Workflows
[Step-by-step procedures referencing MCP tools]

## Troubleshooting
[Failure modes with diagnostic steps]

## Security Considerations
[Mandatory section]
```

### Gotchas: The Core Innovation

The AWS toolkit's most valuable pattern is the **Gotchas section** — numbered corrections for mistakes agents consistently make. For SAP CC, examples include:

**sapcc-compute:**
1. Always check quota via `limes_get_project_quota` before attempting server creation
2. Server status `SHUTOFF` ≠ deleted — the instance still consumes quota
3. Use `neutron_list_ports` with `device_id` to find a server's network interfaces (not in nova response)

**sapcc-quota:**
1. Limes quota values are in base units — RAM is MiB, not GB
2. `physical_usage` may exceed `usage` due to snapshots and replicas
3. Domain quota is a cap on the sum of project quotas, not a pool

**sapcc-audit:**
1. Hermes events use CADF `target_type` format: `compute/server`, not `nova/server`
2. Time filters use `gte:` and `lte:` prefix syntax, not standard query params
3. Event `outcome` is `success`/`failure`/`pending`, not HTTP status codes

### MCP Server Configuration

The `.mcp.json` bundles the server binary config:

```json
{
  "mcpServers": {
    "sapcc": {
      "command": "openstack-mcp-server",
      "env": {
        "OS_AUTH_URL": "${OS_AUTH_URL}",
        "OS_APPLICATION_CREDENTIAL_ID": "${OS_APPLICATION_CREDENTIAL_ID}",
        "OS_APPCRED_SECRET_CMD": "${OS_APPCRED_SECRET_CMD}",
        "OS_REGION_NAME": "${OS_REGION_NAME}"
      }
    }
  }
}
```

### Rules File (`sapcc-agent-rules.md`)

```markdown
# SAP Converged Cloud Guidance

- Use the SAP CC MCP Server for all OpenStack/SAP CC interactions.
- Before starting a task, check whether a relevant sapcc-* skill is available.
  Load the skill and prefer its guidance over general knowledge.
- SAP CC uses a Domain → Project hierarchy. Always be aware of the current
  project scope (check with keystone_token_info if uncertain).
- For any operation that creates or resizes resources, check quota first
  via limes_get_project_quota.
- When debugging issues, check the audit trail (hermes_list_events) and
  metrics (maia_query) before guessing.
- Credentials never reach the LLM — the MCP server holds secrets in process
  memory. Never ask the user for passwords or tokens.
- When uncertain about SAP CC-specific behavior (Limes, Hermes, Maia,
  Keppel, Archer), load the relevant skill rather than guessing.
```

### Validation (`tools/validate.py`)

Stdlib-only Python script validates:
- Plugin manifest structure
- Skill frontmatter (name matches directory, kebab-case, description ≥ 20 chars)
- MCP config structure
- Cross-references (skills don't reference non-existent tools)

## Consequences

### Positive
- **Single install** — `sapcc` plugin gives users everything they need
- **Progressive disclosure** — Skills load on-demand (~50 tokens at startup each)
- **Gotchas prevent mistakes** — Most value comes from corrections, not tutorials
- **Cross-service skills** — Each skill documents how it relates to other services
- **Portable** — Works with Claude Code, Codex, and any agent supporting skills format
- **Testable** — `validate.py` catches structural issues before merge

### Negative
- **Two repos** — MCP server and toolkit evolve separately (different cadences)
- **Sync risk** — New MCP tools need matching skill updates
- **Knowledge capture** — Gotchas require real-world agent usage to discover

### Mitigations
- CI validation ensures skills only reference tools that exist in MCP server
- `version` field in plugin.json tracks minimum MCP server version
- Gotchas section is a living document — add entries as we discover agent mistakes
- The existing `credential-setup` skill proves the pattern works

## Alternatives Considered

### 1. Two plugins (openstack-core + sapcc-platform)
**Rejected** — This is exclusively for SAP CC. There's no use case where someone wants Nova skills without Limes or Hermes. One plugin, one install.

### 2. Embed skills in the MCP server repo
**Rejected** — Couples Go tool implementation with prompt engineering. Different audiences, different change frequencies.

### 3. Monolithic CLAUDE.md with all knowledge
**Rejected** — Bloats context window. Progressive disclosure is essential with 10 skills × ~500 lines each.

### 4. Web-hosted skills with runtime discovery
**Rejected for now** — Adds infrastructure dependency. Local-first matches our team size. Can add later.

## References

- [AWS Agent Toolkit for AWS](https://github.com/aws/agent-toolkit-for-aws) — Reference implementation
- [openstack-mcp-server](https://github.com/notque/openstack-mcp-server) — Our MCP server (Go)
- [Claude Code Plugin Docs](https://docs.anthropic.com/en/docs/claude-code/plugins) — Plugin format spec
