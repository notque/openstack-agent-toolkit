---
name: sapcc-filesystems
description: >
  Shared file system management via Manila in SAP Converged Cloud.
  Triggers: shared filesystem, manila, NFS, CIFS, file share, network storage, mount
version: 1.0.0
metadata:
  service: [manila]
  task: [inspect, manage, debug]
  persona: [developer, platform-engineer]
---

# SAP CC Shared Filesystems (Manila)

Manage Manila shared file systems: list shares, inspect details, and understand access states. Manila provides network-attached storage (NFS, CIFS) that can be mounted by multiple servers simultaneously.

## MCP Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `manila_list_shares` | List file shares in current project | `name`, `status`, `share_proto` (returns: ID, name, status, protocol, size, availability zone) |
| `manila_get_share` | Full detail for a single share | `share_id` (UUID) |

## Gotchas

### 1. Shares are network-mounted — different from block storage

Unlike Cinder volumes (attached to one server via iSCSI/FC), Manila shares are network file systems (NFS/CIFS) accessible by multiple servers simultaneously. Use Manila for shared data, Cinder for dedicated block devices.

### 2. Protocol determines mount method

| Protocol | Mount Style | Typical Use |
|----------|-------------|-------------|
| NFS | `mount -t nfs <export_path> /mnt` | Linux servers, most common |
| CIFS | `mount -t cifs //<path> /mnt` | Windows or mixed environments |
| GlusterFS | Gluster mount | Distributed storage |
| CephFS | Ceph FUSE/kernel mount | Ceph-backed storage |

### 3. Status "available" = ready to mount

Only shares in `available` status can be mounted.

### 4. Size is in GiB

Same as Cinder — all capacity reported in gibibytes.

### 5. Shares need access rules to be mountable

A share in `available` status still requires access rules (IP-based or user-based) before any server can mount it.

### 6. Availability zone affects which servers can mount

Cross-AZ mounting may not be supported. Ensure the share's AZ matches the servers that need it.

### 7. Share network provides the connection path

Shares are associated with a share network (a Neutron network/subnet). Servers must have connectivity to that network.

## Common Workflows

### List All File Shares

```
1. manila_list_shares()
2. Review: name, protocol, status, size, AZ
```

### Inspect a Specific Share

```
1. manila_list_shares(name=<search>) → find the share
2. manila_get_share(share_id=<uuid>) → full details
3. Note: export_location shows the mount path
```

### Find NFS Shares Available for Mounting

```
1. manila_list_shares(share_proto=NFS, status=available)
2. Note export_location for mount commands
3. Verify AZ matches your server's AZ
```

### Troubleshoot a Share in Error State

```
1. manila_get_share(share_id=<uuid>) → check status
2. hermes_list_events(target_type=manila/share, target_id=<uuid>)
3. Common causes: backend capacity, network issue, quota exceeded
```

## Troubleshooting

### Share stuck in "creating"

- Backend provisioning may be slow for large shares
- If > 10 minutes, likely a backend issue
- Check Hermes: `hermes_list_events(target_type=manila/share, outcome=failure)`

### Cannot mount despite "available" status

- Check access rules (not visible via MCP tools)
- Verify network connectivity between server and share network
- Check security groups allow NFS traffic (port 2049) or CIFS (port 445)
- Verify server is in the same AZ

### Quota exhausted

- `limes_get_project_quota(service=sharev2)` → check usage vs quota

## Security Considerations

- Share export locations reveal network topology and storage paths
- NFS shares may have permissive access rules (entire subnet)
- Shared access means data accessible to multiple servers — ensure restrictive access rules
- Audit share creation/deletion via Hermes for compliance

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Servers that can mount a share | Nova | `nova_list_servers` (filter by AZ) |
| Network for share connectivity | Neutron | `neutron_list_networks`, `neutron_list_subnets` |
| Who created/modified shares | Hermes | `hermes_list_events(target_type=manila/share)` |
| Share quota remaining | Limes | `limes_get_project_quota(service=sharev2)` |
