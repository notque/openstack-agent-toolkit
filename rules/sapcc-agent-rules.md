# SAP Converged Cloud Agent Rules

## Core Principles

- Use the SAP CC MCP Server for all OpenStack/SAP CC interactions — it provides
  authenticated API access with credential isolation (secrets never reach the LLM).
- Before starting a task, check whether a relevant sapcc-* skill is available.
  Load the skill and prefer its guidance over general knowledge.
- SAP CC uses a Domain → Project hierarchy. Always be aware of the current
  project scope (check with `keystone_token_info` if uncertain).
- SAP CC regions are independent deployments. Credentials and resources do not
  cross region boundaries. Region naming: `<geo>-<country>-<number>` (e.g., `eu-de-1`).

## Tool Visibility Tiers

The MCP server exposes tools in three tiers based on environment configuration:

| Tier | Env Variable | Tools Available | Use Case |
|------|-------------|-----------------|----------|
| **Read-only** (default) | `MCP_READ_ONLY=true` | 91 read tools | Safe exploration, investigation, monitoring |
| **Write-enabled** | `MCP_READ_ONLY=false` | +16 write tools (107 total) | Resource creation, modification, deletion |
| **Admin** | `MCP_ADMIN_TOOLS=true` | +12 admin tools (119 total) | Cloud admin operations (hypervisors, agents, services) |

### If a tool doesn't appear

- The tool may be gated behind a tier not currently enabled
- Write tools (marked with \* in skill docs) require `MCP_READ_ONLY=false`
- Admin tools (marked with † in skill docs) require `MCP_ADMIN_TOOLS=true` AND cloud_admin role
- Do NOT tell the user the tool doesn't exist — explain which tier enables it

### Write tool safety protocol

All write tools enforce a **confirmed two-call pattern**:
1. Read the resource first (verify state, confirm identity)
2. Only then perform the write operation
3. Verify the result after the write

The `destructive-action-gate` hook blocks destructive writes until the user explicitly approves.

### Admin tool awareness

Admin tools require `cloud_admin` role. If the user's token doesn't have this role:
- The MCP server will return 403 even if the tool is visible
- Check `keystone_token_info` to see current roles before attempting admin operations
- Don't waste API calls on predictably-forbidden operations

## Pre-Action Checks

- **Check quota before creating resources.** Call `limes_get_project_quota` before
  any Nova create, Cinder create, or Neutron resource creation. Quota errors are
  confusing (generic 403/409) and avoidable.
- **Verify current state before mutating.** Call `nova_get_server`, `cinder_get_volume`,
  etc. to confirm current status before performing actions. Stale assumptions cause
  invalid state transitions.
- **Use audit trail for debugging.** Check `hermes_list_events` and metrics
  (`maia_query`) before guessing at root causes. Evidence-based diagnosis > hypothesis.

## Credential Safety

- **Never expose credentials to the LLM.** Do not ask users to paste passwords,
  tokens, or secrets into the conversation. The MCP server handles auth.
- **Prefer application credentials over passwords.** They are scoped, revocable,
  and auditable. Guide users to `credential-setup` skill for initial auth.
- **Keychain storage is mandatory.** Secrets must be stored via OS keychain
  (macOS Keychain, Linux `pass` or `secret-tool`). Never store in plaintext files.
- **Do not log or echo tokens.** If a tool response contains a token or password
  field, do not repeat it in your response to the user.

## Error Handling

- **401 Unauthorized**: Credentials expired or invalid. Guide user to re-authenticate.
  Do not retry — the token is dead. Run `credential-setup` skill.
- **403 Forbidden**: Insufficient permissions for this operation in the current project.
  Check if the user has the correct role. Do not retry with same credentials.
- **404 Not Found**: Resource does not exist or is in a different project. Verify
  the UUID and project scope before concluding it's deleted.
- **409 Conflict**: Resource is in a state that prevents the operation (e.g., volume
  already attached, server in ERROR). Check current state and report why.
- **429 Too Many Requests**: Rate limited. Wait 10-30 seconds and retry once.
  If still failing, reduce request frequency. Never tight-loop retry.
- **500/503 Server Error**: Infrastructure issue. Wait 30 seconds, retry once.
  If persistent, inform user the service may be degraded.

## Rate Limiting & Pagination

- **Respect pagination.** Most list operations return limited results. If you need
  comprehensive data (all servers, all ports), check for pagination markers and
  make subsequent calls. Do not assume the first page is everything.
- **Avoid tight loops.** Space repeated API calls by at least 1-2 seconds.
  Do not hammer endpoints with rapid sequential requests.
- **Use filters to reduce scope.** Prefer filtered queries (by status, name, ID)
  over listing everything and filtering client-side. Less data = faster = fewer API calls.
- **Limit and sort.** Use `limit` parameters when you only need recent items
  (e.g., `hermes_list_events(limit=20)` for recent audit events, not unlimited).

## Destructive Operations

- **Require user confirmation** before any operation that destroys data or interrupts
  service: `delete`, `stop`, `HARD reboot`, `detach volume`, `remove security group`.
- **State what will happen** in the confirmation prompt: "This will permanently delete
  server 'web-prod-1' (UUID: abc-123). All local disk data will be lost. Proceed?"
- **Never auto-chain destructive operations.** Do not delete-then-recreate without
  explicit user approval of each step.
- **Inform about irreversibility.** Some operations cannot be undone: volume deletion
  (data gone), security group removal (connectivity lost), project deletion.

## Shared Resources & Multi-Tenancy

- **Shared security groups affect multiple servers.** Before modifying a security group,
  check which ports/servers reference it. A rule change can break other workloads.
- **Networks may be shared across projects.** The user may see networks owned by
  other projects. Do not modify shared networks — those require network-admin role.
- **Floating IPs are a finite pool.** Do not allocate floating IPs speculatively.
  Allocate only when the user has a clear external connectivity need.
- **RBAC visibility ≠ ownership.** Being able to see a resource does not mean you can
  modify it. Check the resource's `project_id` against the current token scope.

## Stop Conditions

Stop and inform the user if:

- **3 consecutive API errors** on the same operation — something is systemically wrong
- **Resource is in ERROR/irrecoverable state** — admin intervention required
- **Operation would exceed quota** — user needs to free resources or request increase
- **No audit events after 60 seconds** — event ingestion may be delayed, not missing
- **Operation requires admin role** — user credentials likely insufficient
- **You are unsure about a destructive action** — always ask, never assume

## Maximum Depth Directives

- **List operations**: Do not paginate more than 5 pages without asking the user
  if they need the full list. Offer to filter instead.
- **Debugging workflows**: If you've checked 5+ potential causes without finding
  the root cause, summarize findings and ask the user for additional context.
- **Retry loops**: Maximum 3 retries on any operation. After that, report the
  persistent failure and suggest next steps.
- **Cross-service hops**: Maximum 3 levels of cross-service correlation without
  surfacing findings. (e.g., server → ports → security groups: stop and report).

## Role Awareness

| Operation Category | Minimum Role | Note |
|-------------------|--------------|------|
| List/read operations | `member` | Most users have this |
| Create resources | `member` | But quota must allow it |
| Delete own resources | `member` | Only resources in current project |
| Modify shared resources | `network_admin` | Shared networks, RBAC policies |
| Cross-project operations | `admin` or `domain_admin` | Domain-level quota, user management |
| Image publishing | `cloud_image_admin` | Public image visibility |
| Audit log access | `audit_viewer` | May be restricted in some regions |

If an operation requires a role the user likely doesn't have, inform them before
attempting it. Don't waste API calls on predictably-forbidden operations.
