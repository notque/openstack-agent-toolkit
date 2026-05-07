---
name: sapcc-shared-storage
description: >
  Shared file system operations via Manila. Triggers: shared file, manila, nfs,
  cifs, file share, share network. NOT for: block storage (use sapcc-storage)
  or object storage (use sapcc-object-storage).
version: 1.0.0
metadata:
  service: [manila]
  task: [manage, inspect, debug]
  persona: [developer, platform-engineer]
---

# SAP CC Shared Storage (Manila)

Manage shared file systems: list shares, inspect share details, understand protocol and availability zone placement.

## MCP Tools

### Read Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `manila_list_shares` | List file shares in project | `name`, `status` (available/error/creating/deleting/error_deleting), `share_proto` (NFS/CIFS/GlusterFS/HDFS/CephFS) |
| `manila_get_share` | Full share detail by UUID | `share_id` (**required**) |
| `manila_list_access_rules` | List access rules for a share | `share_id` (**required**) |
| `manila_list_share_networks` | List share networks (Neutron connectivity) | `name` |
| `manila_list_snapshots` | List share snapshots | `share_id`, `status` (available/error/creating/deleting) |
| `manila_list_security_services` | List LDAP/Kerberos/AD services | `type` (ldap/kerberos/active_directory), `name` |
| `manila_list_share_types` | List available share types with specs | (none) |

### Security: Credential Isolation

- **Security service passwords excluded**: Manila security services may reference LDAP/AD credentials — password fields are never returned
- No write or admin tiers exist for Manila — all 7 tools are read-only

### Guardrails

- **UUID validation**: `share_id` validated before API call
- **share_proto filter**: Applied client-side (Manila API doesn't support it as query param)

## Gotchas

1. **share_proto filter is applied client-side.** The Manila API does not support `share_proto` as a query parameter. The MCP tool fetches all shares and filters locally. For large projects this may return more data than expected before filtering.

2. **Size is in GiB.** The `size` field is in gibibytes, consistent with Cinder. Do not confuse with bytes or GB.

3. **Status "available" = usable.** Only shares in `available` status can be mounted and accessed. Shares in `creating` are still being provisioned; shares in `error` need investigation.

4. **Share type determines backend capabilities.** The `share_type_name` field indicates the storage backend and capabilities (e.g., replication, snapshots). Different types have different performance characteristics.

5. **Availability zone matters for access.** A share in one AZ may not be directly accessible from compute instances in another AZ. Always check the `availability_zone` matches your server placement.

6. **Export location not shown in list.** To get the mount path (export location), you need `manila_get_share` for the full detail. The list view shows metadata only.

7. **Host field reveals backend placement.** The `host` field (e.g., `manila-host@backend#pool`) shows which storage backend serves the share. Useful for diagnosing backend-specific issues.

## Common Workflows

### List All NFS Shares and Their Status

1. `manila_list_shares` with `share_proto=NFS` — get all NFS shares.
2. Group by `status`: `available` (healthy), `error` (needs attention), `creating` (in progress).
3. Note `size` and `availability_zone` for capacity planning.

### Diagnose a Share in Error State

1. `manila_get_share` with `share_id=<uuid>` — get full details including error messages.
2. Check `status` and any error-related fields in the response.
3. `hermes_list_events` with `target_id=<share_id>` — find the action that caused the error.
4. Verify quota was not exhausted at the time of creation.

### Check Shared Storage Quota

1. `limes_get_project_quota` with service `sharev2` — see share quota and usage.
2. Key resources: `shares` (count), `share_gigabytes` (total GiB), `share_snapshots`.
3. Compare usage against quota to determine headroom.

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Share quota and usage | Limes | `limes_get_project_quota(service=sharev2)` |
| Who created/modified a share | Hermes | `hermes_list_events(target_type=share)` |
| Server that mounts this share | Nova | `nova_get_server` (check mounted filesystems) |
| Block storage (per-server volumes) | Cinder | `cinder_list_volumes` |
| Network access for share | Neutron | `neutron_list_networks` |
