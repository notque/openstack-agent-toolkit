---
name: sapcc-autoscaling
description: >
  Autoscaling operations via Castellum. Triggers: autoscaling, castellum, resize,
  scaling, threshold, auto-resize, capacity management. NOT for: manual quota
  changes (use sapcc-quota/Limes).
version: 1.0.0
metadata:
  service: [castellum]
  task: [manage, inspect, debug]
  persona: [developer, platform-engineer]
---

# SAP CC Autoscaling (Castellum)

Inspect Castellum autoscaling state: view resource configurations, check pending resize operations, diagnose failed scaling actions.

## MCP Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `castellum_get_project_resources` | Get autoscaling config and resource status | `project_id` (UUID, required) |
| `castellum_list_pending_operations` | List scheduled but incomplete resizes | `project_id` (UUID), `asset_type` (e.g. `project-quota:compute:cores`) |
| `castellum_list_recently_failed_operations` | List recently failed resizes | `project_id` (UUID), `asset_type` |

## Gotchas

1. **project_id must be a valid UUID.** The tool validates UUID format and rejects anything else. You cannot pass a project name — resolve it to UUID first via Keystone if needed.

2. **asset_type uses a colon-separated hierarchy.** Format is `project-quota:<service>:<resource>`, e.g., `project-quota:compute:cores` or `project-quota:network:floating_ips`. Getting this format wrong returns empty results without an error.

3. **Castellum watches Limes, does not replace it.** Castellum monitors usage via Limes and triggers resize operations. The actual quota values live in Limes. To see current quota/usage, use `limes_get_project_quota`. Castellum shows the autoscaling configuration and pending/failed operations.

4. **Pending does not mean stuck.** Pending operations are queued resizes that have not yet been executed. Castellum processes these asynchronously. Only flag operations that have been pending for an unusually long time (hours).

5. **Failed operations include the failure reason.** The `recently-failed` endpoint shows why a resize failed (e.g., parent quota exhausted, constraint violation). This is the primary diagnostic tool for scaling failures.

6. **Not all resources are auto-scalable.** Only resources that have Castellum configuration will appear. If `get_project_resources` returns empty or missing resources, those resources are not configured for autoscaling.

7. **Thresholds define when scaling triggers.** Each configured resource has usage thresholds (high/low) that trigger upscale/downscale. The `get_project_resources` response shows these thresholds alongside current usage.

## Common Workflows

### Check Autoscaling Configuration for a Project

1. `castellum_get_project_resources` with `project_id=<uuid>` — see all configured resources and their thresholds.
2. For each resource, note the high/low thresholds and current usage percentage.
3. Cross-reference with `limes_get_project_quota` to see actual quota values.

### Diagnose Why a Resource Did Not Autoscale

1. `castellum_list_recently_failed_operations` with `project_id=<uuid>` — check for failures.
2. If failures exist, read the error reason (typically quota exhaustion at parent level).
3. If no failures and no pending ops, `castellum_get_project_resources` — check if thresholds are configured and if usage is actually above the high threshold.

### Monitor Pending Resize Operations

1. `castellum_list_pending_operations` — see all queued resizes (optionally filter by project or asset_type).
2. Check timestamps — operations pending for over an hour may indicate a processing backlog.
3. If a specific resource is pending, verify the parent quota has headroom via Limes.

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Current quota and usage values | Limes | `limes_get_project_quota` |
| Project UUID from name | Keystone | `keystone_list_projects` |
| Audit trail of resize actions | Hermes | `hermes_list_events(initiator_name=castellum)` |
| Compute resource details | Nova | `nova_list_servers` |
