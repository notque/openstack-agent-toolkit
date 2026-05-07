---
name: sapcc-autoscaling
description: >
  Autoscaling operations via Castellum in SAP Converged Cloud.
  Triggers: autoscaling, castellum, auto-resize, quota scaling, capacity management, resize operation
version: 1.0.0
metadata:
  service: [castellum]
  task: [inspect, monitor, debug]
  persona: [platform-engineer, devops]
---

# SAP CC Autoscaling (Castellum)

Inspect Castellum autoscaling: check resource configurations, view pending operations, and diagnose failed resize attempts. Castellum automatically adjusts project quotas and resource sizes based on configured thresholds.

## MCP Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `castellum_get_project_resources` | Get autoscaling config and status for a project | `project_id` (UUID, required) |
| `castellum_list_pending_operations` | List scheduled but incomplete resize operations | `project_id`, `asset_type` |
| `castellum_list_recently_failed_operations` | List recent resize failures | `project_id`, `asset_type`, `max_age` (default: 1d) |

## What Castellum Does

Castellum watches resource usage and automatically resizes when thresholds are hit:

```
Usage crosses HIGH threshold → Castellum schedules UPSIZE
Usage drops below LOW threshold → Castellum schedules DOWNSIZE
```

Assets it manages:
- `project-quota:compute:cores` — vCPU quota
- `project-quota:compute:ram` — RAM quota
- `project-quota:compute:instances` — instance count quota
- `project-quota:block-storage:capacity` — volume storage
- NFS share sizes, server root disks, etc.

## Gotchas

### 1. Castellum manages QUOTA, not individual resources

Castellum doesn't scale your application. It adjusts quotas and resource sizes. For example, it can increase your project's compute cores quota when usage exceeds 80%, but it doesn't create new servers.

### 2. project_id is required — you must know which project

Unlike other tools, Castellum requires an explicit project_id. Get it from `keystone_token_info` or `keystone_list_projects`.

### 3. Operations can be PENDING without issues

A pending operation means a resize is scheduled. This is normal — Castellum batches operations and may wait for cooldown periods between resizes.

### 4. Failed operations have a reason

`castellum_list_recently_failed_operations` shows WHY a resize failed. Common reasons:
- Quota exceeded at the domain level (project can't grow)
- Backend capacity exhausted
- Conflicting resize already in progress

### 5. max_age controls the failure lookback window

Default is `1d` (24 hours). Use `7d` for broader investigation, `12h` for recent issues only. Accepts Go duration format: `s`, `m`, `h`, `d`.

### 6. asset_type filters are specific strings

Format: `project-quota:<service>:<resource>`. Examples:
- `project-quota:compute:cores`
- `project-quota:compute:ram`
- `project-quota:block-storage:capacity`

### 7. Castellum only acts on configured resources

Not all resources have autoscaling configured. `castellum_get_project_resources` shows which resources ARE configured and their thresholds. No configuration = no autoscaling.

### 8. Cooldown prevents thrashing

After a resize, Castellum waits before acting again. If you see a resource at threshold but no pending operation, it may be in cooldown.

## Common Workflows

### Check Autoscaling Configuration

```
1. keystone_token_info → get current project_id
2. castellum_get_project_resources(project_id=<uuid>)
3. Review: which resources are configured, thresholds, current status
```

### Are There Pending Resizes?

```
1. castellum_list_pending_operations(project_id=<uuid>)
2. If empty: no scheduled resizes (normal)
3. If populated: review what's being resized and when
```

### Diagnose Autoscaling Failures

```
1. castellum_list_recently_failed_operations(project_id=<uuid>, max_age=7d)
2. Review failure reasons
3. Common: domain quota ceiling hit, backend capacity
4. Cross-reference with Limes: limes_get_project_quota → is project at domain cap?
```

### "Why didn't my quota grow?"

```
1. castellum_get_project_resources(project_id) → is the resource configured?
2. If not configured: autoscaling won't act
3. If configured: check thresholds — is usage actually above HIGH?
4. castellum_list_recently_failed_operations → did it try and fail?
5. Check cooldown — did it resize recently and is waiting?
```

### Correlate with Quota

```
1. castellum_get_project_resources(project_id) → autoscaling config
2. limes_get_project_quota → current quota and usage
3. Compare: is usage near threshold? Has quota been growing?
```

## Troubleshooting

### No autoscaling configured for a resource

- Castellum configuration is per-resource, per-project
- Not all projects have autoscaling enabled
- Configuration requires admin or project-admin access (not via MCP tools)

### Operations keep failing

- Check `castellum_list_recently_failed_operations(max_age=7d)` for patterns
- If "domain quota exceeded": the project has hit its domain-level cap. Need domain admin to increase domain quota.
- If "backend capacity": physical capacity exhausted in the region/AZ
- If "conflicting operation": wait for the existing operation to complete

### Autoscaling seems too slow

- Castellum has deliberate cooldown periods (typically 5-15 minutes)
- It batches multiple threshold crossings
- For urgent needs: manual quota adjustment via Limes is faster

### Resource at threshold but no pending operation

- Cooldown period active (recent resize within last N minutes)
- Castellum may not have polled yet (typical interval: 5 minutes)
- Resource may not be configured for autoscaling

## Security Considerations

- Autoscaling configuration reveals capacity management strategy
- Failed operations reveal infrastructure limits and bottlenecks
- project_id in URLs is validated (UUID format) to prevent injection
- Autoscaling policies are read-only via MCP — no configuration changes possible

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Current quota and usage | Limes | `limes_get_project_quota(project_id=<uuid>)` |
| Domain-level quota cap | Limes | `limes_get_domain_quota(domain_id=<uuid>)` |
| Project identity | Keystone | `keystone_token_info`, `keystone_list_projects` |
| Who changed autoscaling config | Hermes | `hermes_list_events(target_type=castellum)` |
| Compute resources being scaled | Nova | `nova_list_servers` (to see actual usage) |
