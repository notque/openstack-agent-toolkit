---
name: sapcc-audit
description: >
  Audit trail investigation on SAP Converged Cloud using Hermes.
  Triggers: audit, who changed, what happened, hermes, events, compliance,
  CADF, activity log, trace action, who did, what was done, event history
version: 1.0.0
metadata:
  service: [hermes]
  task: [investigate, compliance, trace, audit]
  persona: [platform-engineer, security, developer]
---

# SAP CC Audit (Hermes)

Hermes is SAP CC's centralized audit service. It records all API actions across all OpenStack services in CADF (Cloud Auditing Data Federation) format. Events are immutable — the audit trail cannot be modified or deleted by tenants.

## MCP Tools

### Read Tools (always available)

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `hermes_list_events` | Search/filter audit events | `target_type`, `target_id`, `initiator_name`, `initiator_id`, `action`, `outcome`, `observer_type`, `time_gte`, `time_lte`, `limit`, `offset`, `sort` |
| `hermes_get_event` | Full CADF event by UUID | `event_id` (**required**) |
| `hermes_list_attributes` | Discover valid filter values | `attribute` (**required**: target_type, action, outcome, observer_type, initiator_type) |

> All Hermes tools are read-only. No write or admin tiers exist — audit events are immutable.

### Guardrails

- **10,000 offset ceiling**: Queries beyond offset 10,000 return HTTP 500. Use time-based windowing to stay below this limit.
- **Time format**: ISO 8601 UTC timestamps (e.g., `2024-03-15T14:22:00Z`)
- **Sort format**: `field:direction` (e.g., `time:desc`, `target_type:asc,time:desc`)

## CADF Event Model

Every audit event follows this structure:

```
initiator (who) → action (what) → target (to what) → outcome (result)
```

| Field | Description | Example |
|-------|-------------|---------|
| `initiator.name` | Username who performed the action | `D012345` |
| `action` | The operation performed | `update` |
| `target.type_uri` | Resource type in slash format | `compute/server` |
| `target.id` | UUID of the affected resource | `abc-123-def` |
| `outcome` | Result of the operation | `success` |
| `eventTime` | When it occurred (UTC) | `2024-03-15T14:22:01Z` |

See `references/cadf-event-format.md` for the full event schema.

## Gotchas

### 1. target_type uses SLASH format — not service names

Correct: `compute/server`, `network/port`, `identity/project`, `dns/zone`
Wrong: `nova/server`, `server`, `neutron/port`, `VM`

The format is `<service-category>/<resource>`. Call `hermes_list_attributes` with `attribute=target_type` to discover valid values if unsure.

### 2. Time filters use PREFIX syntax

The parameter name itself encodes the comparison:
- `time_gte="2024-01-01T00:00:00Z"` — events at or after this time
- `time_lte="2024-01-01T23:59:59Z"` — events at or before this time

The value is a plain ISO 8601 timestamp. Do NOT embed operators in the value string.

### 3. outcome values are words, NOT HTTP status codes

Valid outcomes: `success`, `failure`, `pending`

NOT: `200`, `404`, `500`, `created`, `error`. Use `hermes_list_attributes` with `attribute=outcome` to confirm.

### 4. action values are present-tense verbs

Valid: `create`, `update`, `delete`, `read`, `authenticate`, `start`, `stop`

NOT past tense: `created`, `updated`, `deleted`. NOT nouns: `creation`, `deletion`. Call `hermes_list_attributes` with `attribute=action` to see all tracked actions.

### 5. hermes_list_attributes is your discovery tool — call it first

When unsure about valid filter values for target_type, action, or outcome, always call `hermes_list_attributes` before `hermes_list_events`. Avoids empty results from typos or wrong format.

### 6. Default limit is 50 — increase for comprehensive audits

If you need a complete picture (compliance reviews, full resource history), set `limit=200` or higher. Default 50 may miss critical events in active projects.

### 7. sort uses "field:direction" format

Format: `sort="time:desc"` or `sort="time:asc"`

Default is newest first (`time:desc`). Use `time:asc` when building a chronological narrative of what happened.

### 8. Events have ingestion delay

Events appear seconds to minutes after the action occurs. If you just performed an action and see no event, wait 30-60 seconds and retry. Do not tell the user "no events exist" immediately after an action.

### 9. initiator_name is the username, not UUID

Filter by human-readable username (e.g., `D012345`, `technical_user_xyz`), not the user's Keystone UUID. This is the name that appears in Keystone token info.

### 10. Hard limit at 10,000 events — API returns 500 beyond this offset

The Hermes API has a hard ceiling at offset 10,000. If you set `limit=15000` or paginate past 10,000 events, the server returns HTTP 500 (not a helpful error). For large audit queries:

- **Narrow with time ranges** — use `time_gte`/`time_lte` to window your query below 10k results
- **Narrow with filters** — add `target_type`, `action`, or `outcome` to reduce result set
- **Use time-based cursoring** — query a time window, note the last event's time, use it as the next window's boundary

The CLI tool [hermescli](https://github.com/sapcc/hermescli) has an `--over-10k-fix` flag that automates this workaround. The MCP tool does not — you must manage it manually by keeping queries scoped.

### 11. Sort supports multiple keys beyond just time

Valid sort fields: `time`, `observer_type`, `target_type`, `target_id`, `initiator_type`, `initiator_id`, `outcome`, `action`.

Each supports `:asc` or `:desc` suffix. Multiple sort keys can be comma-separated: `sort="target_type:asc,time:desc"`. Default direction is ascending if omitted.

### 12. Full event detail includes request/response attachments

`hermes_get_event` returns the complete CADF event including `attachments` — these contain the actual API request body and response. Essential for answering "what exactly changed?" (e.g., which field was updated, what value was set).

## Common Workflows

### "Who changed resource X?"

```
1. hermes_list_events(target_id="<resource-uuid>", sort="time:desc", limit=20)
2. Review initiator.name on each event → identifies who made changes
3. For detail on a specific change: hermes_get_event(event_id) → check attachments
```

### "What happened in the last hour?"

```
1. Calculate time_gte = current time minus 1 hour (ISO 8601 UTC)
2. hermes_list_events(time_gte="2024-03-15T13:00:00Z", limit=100)
3. Group by target_type for overview, or filter by action/outcome
```

### "What did user Y do?"

```
1. hermes_list_events(initiator_name="<username>", sort="time:desc", limit=50)
2. Optionally narrow with time range or target_type
3. Shows all actions taken by that user across all services
```

### "Show me all failures"

```
1. hermes_list_events(outcome="failure", sort="time:desc", limit=50)
2. Optionally narrow by time range or target_type
3. Each event shows what was attempted and on what resource
4. hermes_get_event for details on specific failures
```

### Compliance audit — full resource history

```
1. hermes_list_events(target_id="<resource-uuid>", sort="time:asc", limit=500)
2. This gives chronological lifecycle: create → updates → deletes
3. For each event of interest: hermes_get_event → full request/response
4. Build timeline: who did what, when, and the exact changes made
```

### Discovery — what's tracked?

```
1. hermes_list_attributes(attribute="target_type") → all audited resource types
2. hermes_list_attributes(attribute="action") → all tracked actions
3. hermes_list_attributes(attribute="outcome") → valid outcome values
4. Use results to construct precise queries
```

## Troubleshooting

### No events found

Most common causes (check in order):

1. **Wrong target_type format** — Must be slash format: `compute/server` not `nova/server` or `server`. Call `hermes_list_attributes` to verify.
2. **Time range too narrow** — Expand `time_gte`/`time_lte` range. Events for old resources may be outside default window.
3. **Resource never audited** — Not all internal operations generate events. Read-only operations (list, get) may not be tracked for all services.
4. **Ingestion delay** — If the action just happened, wait 30-60 seconds.
5. **Wrong project scope** — Hermes returns events scoped to the authenticated project. Events in other projects are invisible.

### Too many results / HTTP 500 on large queries

**If you get HTTP 500**: You've likely hit the 10,000 offset ceiling. The fix:
1. Add time range (`time_gte`/`time_lte`) to bound the window below 10k results
2. Use time-based cursoring: query a window, take last event's time as next `time_lte`

**To reduce results generally**:
1. Add `target_type` filter to narrow to specific service
2. Add time range (`time_gte`/`time_lte`) to bound the window
3. Add `action` filter if looking for specific operations (e.g., only `delete`)
4. Add `outcome` filter if only interested in failures
5. Never set `limit` above 10,000 — the API will 500

### Event detail missing attachments

Not all events include request/response attachments. Simple actions (delete, start, stop) may have minimal or no attachments. Update events typically include the changed fields.

## Security

Audit data is sensitive. It reveals:
- **Who** performed actions (usernames, technical accounts)
- **What** they did (including potentially destructive operations)
- **When** they were active (activity patterns)
- **Which resources** they accessed (infrastructure topology)

Only query audit data scoped to the authenticated project. Do not expose audit data containing other users' actions or resource details without confirming the requester has legitimate need. The MCP server enforces project-scoped access, but be judicious in what you surface.

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Server details for compute/server events | Nova | `nova_get_server(<target_id>)` |
| Port details for network/port events | Neutron | `neutron_list_ports` |
| Volume details for volume events | Cinder | `cinder_get_volume(<target_id>)` |
| Who is the initiator (token context) | Keystone | `keystone_token_info` |
| Resource quota impact of actions | Limes | `limes_get_project_quota` |

## Routing

| User need | Action |
|-----------|--------|
| Understanding CADF event structure | Read [cadf-event-format.md](references/cadf-event-format.md) |
