---
name: sapcc-quota
description: >
  Limes quota and usage management for SAP Converged Cloud.
  Triggers: quota, usage, capacity, resource limit, how much, running out, limes, burst
version: 1.0.0
---

# SAP CC Quota & Usage (Limes)

Limes is SAP CC's central quota management service. Not part of vanilla OpenStack. It enforces hierarchical resource quotas across cluster, domain, and project levels.

## MCP Tools

| Tool | Purpose | Required Params |
|------|---------|-----------------|
| `limes_get_project_quota` | Quota + usage for a single project | `domain_id`, `project_id` (optional: `service`, `resource`) |
| `limes_get_domain_quota` | Aggregated quota for all projects in a domain | `domain_id` (optional: `service`, `resource`) |
| `limes_get_cluster_quota` | Cluster-wide capacity and usage | (optional: `service`, `resource`) |

## Quota Model

```
Cluster Capacity
  └─ Domain Quota (sum of project quotas ≤ domain quota)
       └─ Project Quota (what a project is allowed to consume)
            └─ Usage (what's actually consumed)
```

**Constraints:**
- Project quota ≤ Domain quota ≤ Cluster capacity
- Each service (compute, network, object-store, etc.) has multiple resources
- Quota is pre-allocated — not on-demand. Unused quota still "counts" against the domain.

## Gotchas

This is the highest-gotcha-density skill. Read all of these before interpreting Limes data.

### 1. RAM is in MiB, not GB

RAM quota and usage are reported in **MiB**. A quota of `51200` = 50 GiB. A quota of `131072` = 128 GiB. Always convert: `value / 1024 = GiB`.

### 2. physical_usage can exceed usage — this is NORMAL

`physical_usage` includes backend overhead: snapshots, replicas, metadata, copy-on-write reserves. A volume with `usage=100 GiB` might have `physical_usage=150 GiB`. This is not a bug.

### 3. quota=0 with usage=0 means DISABLED, not unlimited

Zero quota = resource is not available to this project. It's explicitly disabled. If you see `quota: 0, usage: 0`, the project cannot use that resource at all.

### 4. quota=-1 means unlimited

Rare. Usually only at domain level for internal/platform domains. Means no hard cap enforced. Do not confuse with "no quota set."

### 5. burst_usage is borrowed capacity

Burst allows temporary over-quota usage. It's a loan from unused cluster capacity. Limes can reclaim it. If `burst_usage > 0`, the project is currently exceeding its base quota and relying on burst — this is fragile and should be resolved.

### 6. domain_id is REQUIRED for project quota

`limes_get_project_quota` needs both `domain_id` AND `project_id`. Get them from `keystone_token_info` first. The token response includes `project.domain.id` and `project.id`.

### 7. project_id is REQUIRED — not project name

Limes uses UUIDs, not names. Always resolve via `keystone_token_info` or `keystone_list_projects`.

### 8. Service filter narrows the response

`service=compute` only returns compute resources. Omit the filter to see ALL services. Don't filter unless you know exactly what you want — you'll miss relevant data.

### 9. "Running out?" = usage/quota ratio

There's no Limes alert. You calculate it: `usage / quota * 100`. Alert thresholds: >80% = warning, >90% = critical, 100% = exhausted (new resource creation blocked).

### 10. Cluster quota ≠ what's available to you

Cluster capacity shows total platform resources. Your project gets a fraction. Don't confuse "cluster has 10TB" with "I can use 10TB."

### 11. Quota does not auto-adjust

If a project needs more quota, someone must request a raise. This is often a manual approval process. Limes just enforces limits — it doesn't grow them.

### 12. Volume types have separate quotas

`volumes_vmware`, `volumes_ceph`, `capacity_vmware`, `capacity_ceph` — each volume backend has its own quota line. A project might have plenty of ceph quota but zero vmware quota.

### 13. Quota exhaustion blocks creation, not operation

Running resources continue to run even if quota is 100% used. But you cannot create NEW resources. Existing VMs keep running, existing volumes stay mounted.

## Common Workflows

### "Am I running out of resources?"

```
1. keystone_token_info → get domain_id, project_id
2. limes_get_project_quota(domain_id, project_id)
3. For each resource: calculate usage/quota percentage
4. Flag anything > 80%
```

### "Can I create a server with flavor X?"

Check three resources simultaneously:
- `compute/cores` — flavor vCPUs ≤ (quota - usage)
- `compute/ram` — flavor RAM (in MiB!) ≤ (quota - usage)
- `compute/instances` — at least 1 instance slot available

If any is insufficient, the server creation will fail with a quota error.

### Full resource inventory for a project

```
1. keystone_token_info → domain_id, project_id
2. limes_get_project_quota(domain_id, project_id)  [no service filter]
3. List all services and resources with quota, usage, percentage
```

### Domain capacity planning

```
1. limes_get_domain_quota(domain_id)
2. Compare projects_quota (sum allocated to projects) vs domain_quota
3. If projects_quota ≈ domain_quota → no room to grow any project
```

### Cluster-wide capacity check

```
1. limes_get_cluster_quota(service="compute")
2. Shows total cluster capacity, domains_quota, usage
3. capacity - domains_quota = unallocated headroom
```

## Interpreting the Response

| Field | Meaning |
|-------|---------|
| `quota` | Maximum allowed for this resource in this project/domain |
| `usage` | Currently consumed (logical — what the user sees) |
| `physical_usage` | Actually consumed on backend (includes overhead, replicas, snapshots) |
| `burst_usage` | Amount currently over-quota via burst allowance |
| `backend_quota` | What's actually configured in the backend service (should match `quota`) |
| `projects_quota` | (Domain/cluster level) Sum of all child project quotas |
| `capacity` | (Cluster level) Total physical capacity of the platform |

### Reading a typical response

```json
{
  "service": "compute",
  "resources": [
    {
      "name": "cores",
      "quota": 64,
      "usage": 48,
      "burst_usage": 0
    },
    {
      "name": "ram",
      "quota": 131072,
      "usage": 98304,
      "burst_usage": 0
    }
  ]
}
```

Translation: Project has 64 cores quota, using 48 (75%). RAM quota is 128 GiB (131072 MiB), using 96 GiB (98304 MiB, 75%).

## Troubleshooting

### "Quota exhausted" but I can't see why

1. Check `usage` vs `quota` — is it really at 100%?
2. Check if burst is active (`burst_usage > 0`) — burst may have been reclaimed
3. Check specific resource — error might say "compute" but actual limit is `instances`, not `cores`
4. Check volume type quotas separately — generic "storage" quota might be fine but specific backend is exhausted

### physical_usage > usage

Normal. Causes:
- Volume snapshots count toward physical but not logical usage
- Replication factor (3x for ceph)
- Copy-on-write overhead
- Deleted resources still being garbage collected

Not a problem unless physical_usage is growing unboundedly.

### Burst usage appearing unexpectedly

1. Project exceeded its base quota at some point
2. Limes granted burst from available cluster headroom
3. This is temporary — Limes can reclaim burst at any time
4. Action: request a quota raise to cover actual usage, or reduce usage below base quota

### backend_quota != quota

Limes periodically syncs to backend services. Temporary mismatch during sync is normal. Persistent mismatch (>1 hour) indicates a Limes issue — escalate.

## Security

Quota data reveals project sizing, resource allocation strategy, and capacity headroom. Treat as internal/confidential:
- Project quota = how big the project is
- Domain quota = how big the business unit's allocation is
- Cluster capacity = total platform size

Only query at the scope you have legitimate access to. The MCP server enforces token-based access, but be aware that quota data you return to users should be scope-appropriate.
