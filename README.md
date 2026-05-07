<!--
SPDX-FileCopyrightText: 2026 SAP SE or an SAP affiliate company

SPDX-License-Identifier: Apache-2.0
-->

# SAP Converged Cloud Agent Toolkit

Help AI coding agents operate SAP Converged Cloud infrastructure.

The Agent Toolkit gives AI agents the skills, knowledge, and guardrails to work with SAP CC services effectively. It works with Claude Code, Codex, and any agent supporting the skills format.

## Prerequisites

| Requirement | Purpose |
|-------------|---------|
| [openstack-mcp-server](https://github.com/notque/openstack-mcp-server) | Runtime providing authenticated API tools (required) |
| SAP CC credentials | Application credential or username+password for your region |
| OS keychain | macOS Keychain, Linux `pass`, or `secret-tool` for secret storage |
| Claude Code ≥ 1.0 or Codex | Agent runtime supporting plugin format |

### MCP Server Setup

```bash
# Install the MCP server binary
go install github.com/notque/openstack-mcp-server@latest

# Or download pre-built binary from releases
# https://github.com/notque/openstack-mcp-server/releases
```

### Credential Setup

After installing the plugin, run the `credential-setup` skill:
```
/sapcc:credential-setup
```

This guides you through storing credentials in your OS keychain. Supports:
- **Application credentials** (recommended) — scoped, revocable
- **Username + password** — via keychain-backed retrieval commands

Environment variables used by the MCP server:
| Variable | Description |
|----------|-------------|
| `OS_AUTH_URL` | Keystone endpoint (e.g., `https://identity-3.<region>.cloud.example.com/v3`) |
| `OS_USERNAME` | SAP CC username (if using password auth) |
| `OS_PW_CMD` | Command to retrieve password from keychain |
| `OS_APPLICATION_CREDENTIAL_ID` | App credential ID (if using app creds) |
| `OS_APPCRED_SECRET_CMD` | Command to retrieve app credential secret |
| `OS_PROJECT_NAME` | Default project scope |
| `OS_DOMAIN_NAME` | Domain (e.g., `my-domain`) |
| `MCP_READ_ONLY` | `true` (default) = read-only tools; `false` = enable write tools |
| `MCP_ADMIN_TOOLS` | `true` = enable admin tools (requires `cloud_admin` role) |

## Quick Start

### Claude Code

```
/plugin marketplace add notque/openstack-agent-toolkit
/plugin install sapcc@openstack-agent-toolkit
```

### Manual Installation

Copy skills to your agent's skills location:

| Agent | Path |
|-------|------|
| Claude Code | `~/.claude/skills/` or `.claude/skills/` |
| Codex | `~/.codex/skills/` or `.agents/skills/` |

## Verify Installation

Quick smoke test to confirm everything works:

```bash
# 1. Check plugin validates
python3 tools/validate.py --plugin sapcc

# 2. Confirm MCP server starts (should show tool list)
openstack-mcp-server --list-tools

# 3. Test read-only API call (requires valid credentials)
# In your agent, ask: "What project am I authenticated to?"
# Expected: agent calls keystone_token_info and reports project/domain
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  AI Agent (Claude Code, Codex, etc.)                             │
├─────────────────────────────────────────────────────────────────┤
│  Agent Toolkit (this repo)          │  MCP Server                │
│  • Skills (domain workflows)        │  • Tool implementations    │
│  • Knowledge (SAP CC context)       │  • Auth management          │
│  • Rules (guardrails)               │  • API proxying             │
│  • Gotchas (mistake prevention)     │  • Response sanitization    │
└─────────────────────────────────────────────────────────────────┘
```

**MCP Server** ([openstack-mcp-server](https://github.com/notque/openstack-mcp-server)) = runtime providing 119 typed tools across 12 services, gated by environment variables
**Agent Toolkit** (this repo) = intelligence layer teaching agents *when* and *how* to use those tools

### Three-Tier Tool Model

Tools are exposed progressively based on environment configuration:

| Tier | Env Variable | Tools | Use Case |
|------|-------------|-------|----------|
| **Read** (default) | `MCP_READ_ONLY=true` | 91 tools | Safe exploration, monitoring, investigation |
| **Write** | `MCP_READ_ONLY=false` | +16 tools | Resource creation, modification, deletion |
| **Admin** | `MCP_ADMIN_TOOLS=true` | +12 tools | Cloud admin operations (hypervisors, agents, chassis) |

All write tools enforce a **confirmation pattern** — they return a preview unless `confirmed=true` is passed. The `destructive-action-gate` hook additionally blocks deletes and power-state changes until the user explicitly approves.

## Task Routing

When you ask the agent a question, it auto-selects the appropriate skill:

| Your question is about... | Skill loaded | MCP tools used |
|---------------------------|-------------|----------------|
| Servers, VMs, flavors, start/stop | `sapcc-compute` | `nova_*` |
| Networks, subnets, ports, security groups | `sapcc-networking` | `neutron_*` |
| Volumes, snapshots, attachments | `sapcc-storage` | `cinder_*` |
| Projects, domains, users, roles | `sapcc-identity` | `keystone_*` |
| Quota, usage, capacity | `sapcc-quota` | `limes_*` |
| Audit events, who changed what | `sapcc-audit` | `hermes_*` |
| Monitoring, PromQL, alerts | `sapcc-metrics` | `maia_*` |
| Container images, vulnerabilities | `sapcc-registry` | `keppel_*` |
| Private endpoints, service connectivity | `sapcc-connectivity` | `archer_*` |
| DNS zones, recordsets | `sapcc-dns` | `designate_*` |
| Load balancers, pools, listeners | `sapcc-loadbalancer` | `octavia_*` |
| Images, snapshots, image properties | `sapcc-images` | `glance_*` |
| Object storage, containers, objects | `sapcc-object-storage` | `swift_*` |
| Secrets, certificates, keys | `sapcc-secrets` | `barbican_*` |
| Autoscaling policies | `sapcc-autoscaling` | `castellum_*` (planned) |
| Shared file systems, shares, exports | `sapcc-shared-storage` | `manila_*` |
| Baremetal provisioning | `sapcc-baremetal` | `ironic_*` |
| Email notifications | `sapcc-email` | `cronus_*` (planned) |
| Auth setup, credential config | `credential-setup` | (guided wizard) |

## What's Included

### Plugin

| Plugin | Description |
|--------|-------------|
| [sapcc](plugins/sapcc/) | All SAP CC skills and MCP server configuration. Covers compute, networking, storage, identity, quota, audit, metrics, registry, and endpoint services. |

### Skills (19 total)

| Skill | Service | Key Capability |
|-------|---------|----------------|
| [sapcc-compute](plugins/sapcc/skills/sapcc-compute/) | [Nova](https://github.com/openstack/nova) | Server lifecycle, flavor selection, cross-service correlation |
| [sapcc-networking](plugins/sapcc/skills/sapcc-networking/) | [Neutron](https://github.com/openstack/neutron) | Network topology, security groups, connectivity debugging |
| [sapcc-storage](plugins/sapcc/skills/sapcc-storage/) | [Cinder](https://github.com/openstack/cinder) | Volume lifecycle, attachment states, performance tiers |
| [sapcc-identity](plugins/sapcc/skills/sapcc-identity/) | [Keystone](https://github.com/openstack/keystone) | Domain/project model, app credentials, service catalog |
| [sapcc-quota](plugins/sapcc/skills/sapcc-quota/) | [Limes](https://github.com/sapcc/limes) | Quota interpretation, capacity planning, usage tracking |
| [sapcc-audit](plugins/sapcc/skills/sapcc-audit/) | [Hermes](https://github.com/sapcc/hermes) | CADF events, compliance queries, change investigation |
| [sapcc-metrics](plugins/sapcc/skills/sapcc-metrics/) | [Maia](https://github.com/sapcc/maia) | PromQL queries, metric discovery, monitoring |
| [sapcc-registry](plugins/sapcc/skills/sapcc-registry/) | [Keppel](https://github.com/sapcc/keppel) | Container images, vulnerability status, federation |
| [sapcc-connectivity](plugins/sapcc/skills/sapcc-connectivity/) | [Archer](https://github.com/sapcc/archer) | Private endpoint services, service discovery |
| [sapcc-dns](plugins/sapcc/skills/sapcc-dns/) | [Designate](https://github.com/openstack/designate) | DNS zones, recordsets, zone transfers |
| [sapcc-loadbalancer](plugins/sapcc/skills/sapcc-loadbalancer/) | [Octavia](https://github.com/openstack/octavia) | Load balancers, pools, health monitors |
| [sapcc-images](plugins/sapcc/skills/sapcc-images/) | [Glance](https://github.com/openstack/glance) | Image management, properties, visibility |
| [sapcc-object-storage](plugins/sapcc/skills/sapcc-object-storage/) | [Swift](https://github.com/openstack/swift) | Object storage, containers, large objects |
| [sapcc-secrets](plugins/sapcc/skills/sapcc-secrets/) | [Barbican](https://github.com/openstack/barbican) | Secret management, certificates, keys |
| [sapcc-autoscaling](plugins/sapcc/skills/sapcc-autoscaling/) | [Castellum](https://github.com/sapcc/castellum) | Autoscaling policies, resource operations |
| [sapcc-shared-storage](plugins/sapcc/skills/sapcc-shared-storage/) | [Manila](https://github.com/openstack/manila) | Shared file systems, exports, share networks |
| [sapcc-baremetal](plugins/sapcc/skills/sapcc-baremetal/) | [Ironic](https://github.com/openstack/ironic) | Baremetal provisioning, node lifecycle |
| [sapcc-email](plugins/sapcc/skills/sapcc-email/) | [Cronus](https://github.com/sapcc/cronus) | Email notifications, SMTP relay |
| [credential-setup](plugins/sapcc/skills/credential-setup/) | [Keystone](https://github.com/openstack/keystone) | Guided auth setup with keychain storage |

### Rules

The [rules file](rules/sapcc-agent-rules.md) provides baseline agent behavior:
- Check quota before resource creation
- Error handling patterns (401/403/404/409/429/5xx)
- Rate limiting and pagination guidance
- Destructive operation confirmation requirements
- Stop conditions and maximum depth directives
- Role awareness for operations

### Knowledge

| Topic | Description |
|-------|-------------|
| [SAP CC Services](knowledge/sapcc/services.md) | Service reference: APIs, tool prefixes, common operations by role |

## How Skills Work

Skills use progressive disclosure:

1. At startup, the agent reads only skill name + description (~50 tokens each)
2. When a task matches, the full skill loads (~200-400 lines of instructions)
3. Reference files load on-demand for deep-dive content
4. Skill context releases when the task completes

19 skills installed = ~950 tokens at startup. Full context only when needed.

## Security Philosophy

- **Credentials never reach the LLM** — MCP server holds secrets in process memory
- **Application credentials over passwords** — scoped, revocable, no password exposure
- **Keychain storage** — secrets retrieved via system commands, never in config files
- **Defense in depth** — response sanitization catches accidental leakage
- **Destructive operations require confirmation** — skills enforce user consent
- **Audit trail** — all API actions logged to Hermes with credential identity

## Validation

```bash
python3 tools/validate.py
```

Validates all plugin manifests, skill frontmatter, and MCP configs. Runs in CI on every push and PR.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding skills and improving documentation.

## Related

- [openstack-mcp-server](https://github.com/notque/openstack-mcp-server) — The Go MCP server this toolkit complements
- [go-api-declarations](https://github.com/sapcc/go-api-declarations) — Canonical Go type definitions for SAP CC APIs (CADF, Limes, Castellum)
- [hermescli](https://github.com/sapcc/hermescli) — CLI for Hermes audit service
- [limesctl](https://github.com/sapcc/limesctl) — CLI for Limes quota service
- [AWS Agent Toolkit](https://github.com/aws/agent-toolkit-for-aws) — Similar pattern for AWS (reference architecture)

## License

Copyright 2026 SAP SE or an SAP affiliate company. Licensed under the [Apache License 2.0](LICENSE).
