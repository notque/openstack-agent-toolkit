---
name: sapcc-storage
description: >
  Block storage operations via Cinder. Triggers: volume, disk, storage,
  block storage, attachment, cinder.
version: 1.0.0
metadata:
  service: [cinder]
  task: [manage, inspect, debug]
  persona: [developer, platform-engineer]
---

# SAP CC Block Storage (Cinder)

Manage Cinder volumes: list, inspect, understand attachment state, and troubleshoot failures.

## MCP Tools

### Read Tools
| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `cinder_list_volumes` | List volumes with optional filters | `status`, `name` |
| `cinder_get_volume` | Full detail for a single volume | `volume_id` |
| `cinder_list_snapshots` | List volume snapshots | `volume_id`, `status` |
| `cinder_get_snapshot` | Detail for a single snapshot | `snapshot_id` |
| `cinder_list_volume_types` | Available volume types and their properties | — |
| `cinder_get_quotas` | Block storage quota usage and limits | `project_id` (optional) |
| `cinder_list_backups` | List volume backups | `volume_id`, `status` |
| `cinder_list_transfers` | List pending volume transfers | — |

### Write Tools (requires MCP_READ_ONLY=false)
| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `cinder_create_volume` | Create a new volume | `size`, `name`, `volume_type` |
| `cinder_delete_volume` | Delete a volume (must be in available state) | `volume_id` |

### Admin Tools (requires MCP_ADMIN_TOOLS=true)
| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `cinder_list_services` | List Cinder services (scheduler, volume) and state | — |

## Gotchas

1. **Status "in-use" blocks deletion.** A volume with status `in-use` is attached to a server. You must detach it (via Nova) before deletion. Attempting to delete returns 400.

2. **Status "available" = safe to operate.** Only volumes in `available` state can be deleted, extended, or retyped. This is the idle/detached state.

3. **Size is GiB, not GB.** Cinder reports size in gibibytes (1 GiB = 1.074 GB). Limes quota is also in GiB. Do not confuse with decimal gigabytes when calculating capacity.

4. **volume_type determines performance tier.** Each volume type (e.g., `vmware`, `vmware_hdd`) maps to a backend with different IOPS/throughput characteristics. Quota in Limes is tracked per volume_type, not just total capacity.

5. **attachments array reveals server linkage.** Each entry contains `server_id` and `device` (e.g., `/dev/sdb`). A volume can have multiple attachments if multiattach is enabled (rare in SAP CC).

6. **Status "error" = backend failure.** Usually indicates a storage backend issue (e.g., failed provisioning, snapshot failure). Check Hermes audit trail (`hermes_list_events` with `target.id=<volume_id>`) for the originating action and error detail.

7. **Quota is per volume_type in Limes.** Use `limes_get_project_quota` and inspect `block-storage` service resources. You will see separate `capacity` and `volumes` quotas for each type. Running out of quota for one type does not mean all storage is exhausted.

## Common Workflows

### List Volumes and Attachment Status

```
cinder_list_volumes
```

Scan the response for:
- `status: in-use` — attached (check `attachments[].server_id`)
- `status: available` — detached, idle
- `status: error` — needs investigation

### Find Volumes Attached to a Specific Server

```
cinder_list_volumes
```

Filter results client-side: iterate `attachments` array and match `server_id` against the target server UUID. There is no server-side filter for attachment target.

### Check Available Storage Quota Before Creating

```
limes_get_project_quota  (service: block-storage)
```

Compare `usage` vs `quota` for the target `volume_type`. Key resources:
- `capacity_<type>` — total GiB allocated for that type
- `volumes_<type>` — count of volumes of that type

### Investigate Volume in Error State

1. `cinder_get_volume` with the volume UUID — note the `status`, `migration_status`, and any `error` fields.
2. `hermes_list_events` filtered to `target.id=<volume_id>` — find the action that triggered the error (create, extend, snapshot, migrate).
3. Check if quota was exceeded at the time of the action.
4. If the volume was being created from a snapshot, verify the source snapshot still exists.

## Troubleshooting

### Volume Stuck in "in-use" After Server Deletion

The volume's attachment record was not cleaned up. This happens when a server is force-deleted or the detach call fails mid-operation.

**Diagnosis:**
1. `cinder_get_volume` — check `attachments[].server_id`
2. `nova_get_server` with that server_id — if 404, the server no longer exists
3. The attachment is orphaned

**Resolution:** Requires admin intervention or a `os-force_detach` action (not available via MCP tools). Escalate to platform team with volume_id and orphaned server_id.

### Volume in Error State

**Diagnosis:**
1. `cinder_get_volume` — capture full status fields
2. `hermes_list_events` with `target.id=<volume_id>` and `outcome=failure`
3. Common causes: backend capacity exhausted, snapshot source deleted, network timeout to storage backend

**Resolution:** If the volume was never successfully provisioned (size shows 0 or status is `error` from creation), it can be deleted. If it held data, escalate — the backend may recover.

### Quota Exhausted

**Diagnosis:**
1. `limes_get_project_quota` — check `block-storage` service
2. Identify which volume_type hit the limit (capacity or count)

**Resolution:**
- Delete unused `available` volumes of that type
- Request quota increase via Limes (requires approval workflow)
- Consider using a different volume_type if another has available capacity

## Security Considerations

- **Volumes may contain sensitive data.** Always confirm with the user before deleting a volume. There is no soft-delete or recycle bin — deletion is permanent and unrecoverable.
- **Snapshot inheritance.** Deleting a volume does not delete its snapshots, but orphaned snapshots still consume quota and may contain sensitive data.
- **Cross-project visibility.** Volumes are project-scoped. You cannot see or operate on volumes in other projects without re-scoping credentials.
- **Audit trail.** All volume operations (create, delete, attach, detach, extend) are logged in Hermes. Use this to verify who performed destructive actions.

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Server a volume is attached to | Nova | `nova_get_server(<attachments[].server_id>)` |
| Who created/deleted/modified a volume | Hermes | `hermes_list_events(target_type=volume, target_id=<uuid>)` |
| Block storage quota remaining | Limes | `limes_get_project_quota(service=block-storage)` |
| Server's other volumes | Nova + Cinder | Get server → list volumes → filter by server_id |
