# SAP Converged Cloud Agent Toolkit

Help AI coding agents operate SAP Converged Cloud infrastructure.

The Agent Toolkit gives AI agents the skills, knowledge, and guardrails to work with SAP CC services effectively. It works with Claude Code, Codex, and any agent supporting the skills format.

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

**MCP Server** ([openstack-mcp-server](https://github.com/notque/openstack-mcp-server)) = runtime providing typed tools (28+ API operations)
**Agent Toolkit** (this repo) = intelligence layer teaching agents *when* and *how* to use those tools

## What's Included

### Plugin

| Plugin | Description |
|--------|-------------|
| [sapcc](plugins/sapcc/) | All SAP CC skills and MCP server configuration. Covers compute, networking, storage, identity, quota, audit, metrics, registry, and endpoint services. |

### Skills

| Skill | Service | Key Capability |
|-------|---------|----------------|
| [sapcc-compute](plugins/sapcc/skills/sapcc-compute/) | Nova | Server lifecycle, flavor selection, cross-service correlation |
| [sapcc-networking](plugins/sapcc/skills/sapcc-networking/) | Neutron | Network topology, security groups, connectivity debugging |
| [sapcc-storage](plugins/sapcc/skills/sapcc-storage/) | Cinder | Volume lifecycle, attachment states, performance tiers |
| [sapcc-identity](plugins/sapcc/skills/sapcc-identity/) | Keystone | Domain/project model, app credentials, service catalog |
| [sapcc-quota](plugins/sapcc/skills/sapcc-quota/) | Limes | Quota interpretation, capacity planning, usage tracking |
| [sapcc-audit](plugins/sapcc/skills/sapcc-audit/) | Hermes | CADF events, compliance queries, change investigation |
| [sapcc-metrics](plugins/sapcc/skills/sapcc-metrics/) | Maia | PromQL queries, metric discovery, monitoring |
| [sapcc-registry](plugins/sapcc/skills/sapcc-registry/) | Keppel | Container images, vulnerability status, federation |
| [sapcc-connectivity](plugins/sapcc/skills/sapcc-connectivity/) | Archer | Private endpoint services, service discovery |
| [credential-setup](plugins/sapcc/skills/credential-setup/) | Keystone | Guided auth setup with keychain storage |

### Rules

The [rules file](rules/sapcc-agent-rules.md) provides baseline agent behavior:
- Check quota before resource creation
- Use audit trail for debugging
- Never expose credentials to the LLM
- Load skills before guessing at SAP CC-specific behavior

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

10 skills installed = ~500 tokens at startup. Full context only when needed.

## Security Philosophy

- **Credentials never reach the LLM** — MCP server holds secrets in process memory
- **Application credentials over passwords** — scoped, revocable, no password exposure
- **Keychain storage** — secrets retrieved via system commands, never in config files
- **Defense in depth** — response sanitization catches accidental leakage
- **Destructive operations require confirmation** — skills enforce user consent

## Validation

```bash
python3 tools/validate.py
```

Validates all plugin manifests, skill frontmatter, and MCP configs. Runs in CI.

## Related

- [openstack-mcp-server](https://github.com/notque/openstack-mcp-server) — The Go MCP server this toolkit complements
- [AWS Agent Toolkit](https://github.com/aws/agent-toolkit-for-aws) — Similar pattern for AWS (reference architecture)
