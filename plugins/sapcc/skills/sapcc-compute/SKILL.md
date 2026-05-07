---
name: sapcc-compute
description: >-
  Manage compute instances on SAP Converged Cloud. Covers server lifecycle,
  flavor selection, status transitions, and cross-service correlation with
  networking and storage. Use when: listing VMs, checking server status,
  debugging instance issues, performing server actions (start/stop/reboot),
  selecting flavors, or investigating why a server won't start.
  NOT for container workloads (use sapcc-registry) or bare metal.
version: 1.0.0
metadata:
  service: [nova]
  task: [list, inspect, debug, lifecycle]
  persona: [developer, platform-engineer]
---

# SAP CC Compute (Nova)

## MCP Tools

| Tool | Purpose |
|------|---------|
| \`nova_list_servers\` | List instances. Filters: \`status\`, \`name\` (regex), \`limit\`. Returns ID, name, status, addresses. |
| \`nova_get_server\` | Full detail by UUID: addresses, flavor, image, host_id, metadata, created/updated timestamps. |
| \`nova_list_flavors\` | Available instance types with vCPUs, RAM (MiB), disk (GiB). Use for sizing decisions. |
| \`nova_server_action\` | Lifecycle actions: \`start\`, \`stop\`, \`reboot\` (type: SOFT/HARD), \`pause\`, \`unpause\`, \`suspend\`, \`resume\`. |

## Gotchas

1. **Check quota before creating.** Nova returns generic 403 or 409 when quota is exhausted — no helpful message. Always call \`limes_get_project_quota\` for \`compute\` resources (instances, cores, ram) before any create/resize operation. The error "Quota exceeded" is often not in the Nova response at all.

2. **SHUTOFF still consumes quota.** A stopped server (\`SHUTOFF\` status) continues to consume \`instances\` and \`cores\` quota. Only \`DELETED\` servers release quota. Users who "stopped" servers expecting freed capacity will be confused — clarify this distinction.

3. **Ports are not in the Nova response.** The \`addresses\` field on a server shows IP addresses grouped by network name, but does NOT include port UUIDs, MAC addresses, or security group assignments. To get port details, call \`neutron_list_ports\` with \`device_id=<server-uuid>\`. This is the only way to find which security groups apply to a server.

4. **SAP CC flavor naming conventions.** Flavors follow the pattern \`<family><generation>_<size>\` (e.g., \`m2_xlarge\`). Families: \`m\` = general purpose, \`r\` = memory-optimized, \`c\` = compute-optimized. Generations increment (1, 2, 3...). See \`references/flavor-families.md\` for the full matrix. Do not guess flavor names — always call \`nova_list_flavors\` to confirm availability in the current region.

5. **Server actions are asynchronous.** Calling \`nova_server_action\` returns 202 immediately. The server transitions through intermediate states (e.g., \`REBOOT\` → \`ACTIVE\`). You must poll with \`nova_get_server\` to confirm the action completed. Typical transitions take 5-30 seconds but can take minutes for large instances.

6. **HARD reboot is destructive.** A \`HARD\` reboot is equivalent to pulling the power cord — in-flight I/O is lost, filesystems may corrupt. Always attempt \`SOFT\` reboot first (sends ACPI shutdown signal). Only escalate to \`HARD\` if the guest OS is unresponsive. Confirm with the user before issuing HARD reboot.

7. **ERROR state requires admin intervention.** Servers in \`ERROR\` status cannot be recovered via \`nova_server_action\`. Common causes: host failure, scheduler error, failed live-migration. The user must contact their cloud admin or file a support ticket. Do not attempt repeated actions on ERROR servers.

8. **Addresses field structure varies by network.** The \`addresses\` response is keyed by network name, with each entry containing \`addr\` (IP), \`version\` (4/6), and \`OS-EXT-IPS:type\` (\`fixed\` or \`floating\`). Multiple networks produce multiple keys. Do not assume a single-network structure.

9. **Server metadata is not automatically populated.** Nova metadata is user-supplied key-value pairs. Do not expect metadata to contain project info, cost center, or ownership unless the user's automation sets it. The \`host_id\` is an opaque hash — it identifies co-location but is not a hostname.

10. **Name filter is not exact match.** \`nova_list_servers\` with a \`name\` filter uses regex-style matching. Searching for \`name=web\` returns \`web-1\`, \`web-prod\`, \`my-web-server\`, etc. For exact matches, filter results client-side after retrieval.

## Common Workflows

### List and Inspect Servers

```
1. nova_list_servers (optionally filter by status or name)
2. For each server needing detail: nova_get_server with its UUID
3. For network info: neutron_list_ports with device_id=<server-uuid>
```

### Get Full Server + Network Picture

```
1. nova_get_server → note addresses (IPs) and server UUID
2. neutron_list_ports with device_id=<server-uuid> → port UUIDs, MAC, security groups
3. For each security group ID: neutron_list_security_groups for rules
```

This gives the complete picture: server → IPs → ports → security groups → rules.

### Debug: Server Won't Start

```
1. nova_get_server → check current status
   - SHUTOFF: try nova_server_action start
   - ERROR: inform user, admin required
   - BUILD: still provisioning, wait
   - PAUSED/SUSPENDED: unpause/resume first
2. If start fails with 409: limes_get_project_quota → check compute quota
3. If quota ok: hermes_list_events with target.id=<server-uuid> → recent errors
4. If no audit clues: maia_query for host-level issues
```

### Perform Server Action Safely

```
1. nova_get_server → confirm current status allows the action
   Valid transitions:
   - start: SHUTOFF → ACTIVE
   - stop: ACTIVE → SHUTOFF
   - reboot (SOFT): ACTIVE → ACTIVE (via REBOOT)
   - reboot (HARD): any running state → ACTIVE (destructive)
   - pause: ACTIVE → PAUSED
   - unpause: PAUSED → ACTIVE
   - suspend: ACTIVE → SUSPENDED
   - resume: SUSPENDED → ACTIVE
2. For destructive actions (stop, HARD reboot): confirm with user
3. nova_server_action with action and server_id
4. Poll nova_get_server until status reaches target (or timeout after 2 min)
```

### Select a Flavor

```
1. nova_list_flavors → get available flavors in region
2. Match requirements to flavor family:
   - Balanced workload → m-series (general purpose)
   - Database/cache → r-series (memory-optimized)
   - Batch/CI → c-series (compute-optimized)
3. Check limes_get_project_quota to ensure cores/ram headroom
4. If flavor not found: may not be available in this region or project
```

## Troubleshooting

### Stuck in BUILD

Server has been in \`BUILD\` status for >10 minutes.

- **Typical cause**: Scheduler couldn't place it (no host with capacity), or image download is slow.
- **Diagnostic**: \`hermes_list_events\` filtered to \`target.id=<server-uuid>\` — look for \`compute/server/create\` with outcome \`pending\` or \`failure\`.
- **Resolution**: If no events after 15 min, likely a scheduler issue — admin intervention required. Do not delete-and-retry without checking quota first.

### ERROR After Resize

Server entered ERROR after a resize or migrate operation.

- **Typical cause**: Target host ran out of disk during resize, or live-migration timed out.
- **Diagnostic**: \`hermes_list_events\` for recent \`compute/server/resize\` or \`compute/server/migrate\` events. Check outcome field.
- **Resolution**: Admin must reset the server state. User cannot self-service from ERROR.

### Can't Reach Server via Network

Server is ACTIVE but unreachable.

- **Diagnostic steps**:
  1. \`nova_get_server\` → confirm status is ACTIVE (not PAUSED/SUSPENDED)
  2. Check addresses: does it have a floating IP? Fixed IPs are only reachable from within the VPC/network.
  3. \`neutron_list_ports\` with \`device_id\` → check port \`status\` (should be \`ACTIVE\`, not \`DOWN\` or \`BUILD\`)
  4. Check security groups on the port → ensure ingress rules allow the traffic (SSH=22, ICMP, etc.)
  5. If port is DOWN: may be a binding failure — check \`hermes_list_events\` for port-related events

## Security Considerations

- **Confirm destructive actions**: Always ask user confirmation before \`stop\`, \`HARD reboot\`, or any action that interrupts service. State what will happen: "This will immediately power off the instance, dropping all connections."
- **Metadata visibility**: Server metadata is visible to anyone with \`compute:server:show\` permission in the project. Do not store secrets, credentials, or PII in metadata.
- **Host ID is semi-sensitive**: While opaque, \`host_id\` reveals co-location (same hash = same hypervisor). Avoid exposing it in shared contexts without need.
- **Audit trail**: All server actions generate Hermes events. Inform users that actions are logged with their credential identity.
- **Cross-project access**: Nova operations are scoped to the authenticated project. You cannot see or act on servers in other projects without re-scoping credentials.

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Network interfaces for a server | Neutron | `neutron_list_ports(device_id=<server_uuid>)` |
| Attached volumes | Cinder | `cinder_list_volumes` → filter by attachments[].server_id |
| Quota before creating | Limes | `limes_get_project_quota(service=compute)` |
| Who modified this server | Hermes | `hermes_list_events(target_type=compute/server, target_id=<uuid>)` |
| CPU/memory metrics | Maia | `maia_query` with `vm_cpu_seconds_total`, `vm_memory_usage_bytes` |
| Security groups on ports | Neutron | `neutron_list_ports` → then `neutron_list_security_groups` |

## Routing

| User need | Action |
|-----------|--------|
| Flavor naming and selection | Read [flavor-families.md](references/flavor-families.md) |
