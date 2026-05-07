---
name: sapcc-images
description: >
  Image management via Glance in SAP Converged Cloud.
  Triggers: image, glance, VM image, OS image, snapshot, AMI, disk image, boot image
version: 1.0.0
metadata:
  service: [glance]
  task: [inspect, manage, debug]
  persona: [developer, platform-engineer]
---

# SAP CC Images (Glance)

Inspect Glance images: list available images, check details, and understand image properties. Glance stores disk images used to boot Nova servers.

## MCP Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `glance_list_images` | List images available to current project | `name`, `status`, `visibility`, `owner` (returns: ID, name, status, visibility, disk/container format, size) |
| `glance_get_image` | Full detail for a single image | `image_id` (UUID) |

## Gotchas

### 1. Visibility controls who can see and use an image

| Visibility | Who can see | Who can use |
|------------|-------------|-------------|
| `public` | Everyone | Everyone |
| `private` | Owner project only | Owner project only |
| `shared` | Owner + explicitly shared projects | Owner + shared projects |
| `community` | Everyone | Everyone (but not in default listings) |

Most production images are `public` (provided by platform team) or `private` (project-specific snapshots).

### 2. Status "active" = ready to use

Only `active` images can be used to boot servers. Other statuses:
- `queued`: Metadata created, no data uploaded yet
- `saving`: Data currently being uploaded
- `deactivated`: Administratively disabled (cannot boot, but data exists)
- `killed`: Upload failed

### 3. Size is in bytes — can be very large

Image sizes are raw bytes. A typical Linux image is 2-10 GB. Convert: `size / 1024 / 1024 / 1024` for GiB.

### 4. disk_format and container_format matter for compatibility

| disk_format | Description |
|-------------|-------------|
| `vmdk` | VMware (most common in SAP CC) |
| `raw` | Uncompressed disk |
| `qcow2` | QEMU/KVM compressed |
| `vhd` | Hyper-V |

Container format is almost always `bare` in practice.

### 5. Public images are platform-provided — don't delete them

Images with `visibility=public` are maintained by the SAP CC platform team. Your project uses them but doesn't own them. You can only modify/delete `private` images you own.

### 6. Image properties contain OS metadata

`glance_get_image` returns properties like `os_type`, `os_distro`, `os_version`, `hw_vif_model`, `hypervisor_type`. Use these to identify the operating system and compatibility requirements.

### 7. Snapshots are private images created from servers

When you snapshot a server, it creates a private Glance image. These consume image quota and storage. Old snapshots should be cleaned up.

### 8. owner field is a project UUID

The `owner` filter accepts a project UUID. Use `keystone_list_projects` to find project UUIDs if needed.

## Common Workflows

### Find Available Boot Images

```
1. glance_list_images(visibility=public, status=active)
2. Review: name, size, disk_format
3. Look for naming patterns: "Ubuntu 22.04", "SLES 15 SP5", "Windows 2022"
```

### Find Project Snapshots

```
1. glance_list_images(visibility=private, owner=<project_id>)
2. These are your project's server snapshots
3. Check sizes and dates for cleanup candidates
```

### Inspect Image Before Booting

```
1. glance_get_image(image_id=<uuid>)
2. Check: status=active, disk_format compatible with your hypervisor
3. Note: min_disk, min_ram requirements
4. Review os_distro, os_version for the OS
```

### Find Image Used by a Server

```
1. nova_get_server(server_id) → note image reference
2. glance_get_image(image_id) → full image details
```

## Troubleshooting

### Image not found

- Image may be private to another project
- Image may have been deleted — check Hermes audit trail
- Try without filters to see all accessible images

### Cannot boot server from image

- Check image status is `active` (not `deactivated` or `queued`)
- Check `min_disk` and `min_ram` — flavor must meet minimums
- Verify disk_format is compatible with the target hypervisor

### Image in "queued" status for a long time

- Upload may have failed silently
- Check Hermes: `hermes_list_events(target_type=image, target_id=<uuid>)`
- May need to delete and re-upload

## Security Considerations

- Private images may contain sensitive configurations or credentials baked in
- Image names and properties reveal infrastructure stack (OS versions, patch levels)
- Old, unpatched images are a security risk — check os_version against known CVEs
- Snapshots may capture ephemeral credentials or session data from running servers

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Servers using an image | Nova | `nova_list_servers(image=<image_id>)` |
| Who created/deleted images | Hermes | `hermes_list_events(target_type=image)` |
| Image quota usage | Limes | `limes_get_project_quota(service=image)` |
| Flavors meeting min_disk/min_ram | Nova | `nova_list_flavors` |
