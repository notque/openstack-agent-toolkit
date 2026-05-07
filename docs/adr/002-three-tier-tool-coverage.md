<!--
SPDX-FileCopyrightText: 2026 SAP SE or an SAP affiliate company

SPDX-License-Identifier: Apache-2.0
-->

# ADR-002: Three-Tier Tool Coverage Model

## Status

Accepted

## Date

2026-05-07

## Context

The openstack-mcp-server implements a three-tier tool visibility model:

```
MCP_READ_ONLY=true  (default):  91 read-only tools
MCP_READ_ONLY=false:           +16 write tools (107 total)
MCP_ADMIN_TOOLS=true:          +12 admin tools (119 total)
```

The agent toolkit must mirror this tiering in its skill documentation so that:
1. Engineers get complete documentation for every tool available to them
2. Skills don't reference tools that aren't visible in the current configuration
3. Admin-only operations are clearly marked to prevent confusion when tools don't appear
4. Write operations include safety guidance (pre-checks, confirmation, rollback)

## Decision

### Skill Structure

Each service skill documents ALL tools for that service across all tiers, using clear markers:

```markdown
## MCP Tools

### Read Tools (always available)
| Tool | Purpose | Key Parameters |
...

### Write Tools (requires MCP_READ_ONLY=false)
| Tool | Purpose | Key Parameters |
...

### Admin Tools (requires MCP_ADMIN_TOOLS=true)
| Tool | Purpose | Key Parameters |
...
```

### Tier Markers

- Read tools: No marker (default)
- Write tools: Section header states the env requirement
- Admin tools: Section header states the env requirement AND minimum role (cloud_admin)

### Safety Layers for Write Tools

Write tool documentation includes:
1. **Pre-check requirement** — what to verify before calling (quota, state, dependencies)
2. **Confirmation pattern** — what to tell the user and what approval looks like
3. **Post-check** — how to verify the action succeeded
4. **Rollback guidance** — what to do if it fails or was unintended

### Hook Enforcement

The `destructive-action-gate.py` PreToolUse hook enforces user approval for all write tools classified as destructive. This is the **enforcement layer** — skills provide the **guidance layer**.

### Rules File

The global rules file (`rules/sapcc-agent-rules.md`) documents:
- The three-tier model and how to detect which tier is active
- That tools may not appear if the tier isn't enabled
- That admin tools require cloud_admin role

## Consequences

### Positive
- 100% tool coverage — every engineer sees docs for every tool they can use
- Clear "why can't I see this tool?" answers (tier not enabled)
- Write operations have structured safety guidance
- Admin operations clearly marked to prevent role confusion

### Negative
- Skills become longer (more tools = more lines) — mitigated by reference files
- Must sync with MCP server on every tool addition — mitigated by validate.py

### Neutral
- Progressive disclosure still works — agent loads full skill only when needed
- Hook enforcement is independent of skill content (defense in depth)

## Alternatives Considered

1. **Separate skills per tier** (e.g., `sapcc-compute-admin`) — Rejected: splits related knowledge artificially, makes cross-referencing harder
2. **Only document read tools** — Rejected: engineers with write access get no guidance
3. **Document all tools flat without tier markers** — Rejected: confusing when tools don't appear

## Implementation

1. Update all 18 service skills with complete tool tables (read/write/admin sections)
2. Add three-tier model documentation to rules file
3. Update destructive-action-gate.py hook to cover new write tools
4. Update knowledge/services.md with tier legend
