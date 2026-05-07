---
name: sapcc-images
description: >
  Image operations via Glance. Triggers: image, glance, ami, snapshot,
  visibility, boot image. NOT for: container images (use sapcc-registry/Keppel).
version: 1.0.0
metadata:
  service: [glance]
  task: [manage, inspect, debug]
  persona: [developer, platform-engineer]
---

# SAP CC Images (Glance)

Inspect and list VM images: find available boot images, check image status, understand visibility and format.

## MCP Tools

### Read Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `glance_list_images` | List available images | `name`, `status` (queued/saving/active/killed/deleted/deactivated), `visibility` (public/private/shared/community), `owner` |
| `glance_get_image` | Full image detail by UUID | `image_id` (**required**) |
| `glance_list_image_members` | List projects an image is shared with | `image_id` (**required**) |

### Admin Tools (requires MCP_ADMIN_TOOLS=true)

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `glance_list_tasks`† | List image import tasks | `status` (pending/processing/success/failure), `type` |

### Guardrails

- **UUID validation**: `image_id` validated before API call
- **No write tools**: Image upload/delete not available via MCP (use OpenStack CLI)
- **Visibility meanings**: `public` = all projects see it; `shared` = explicitly shared via members; `community` = discoverable by all but not in default list

## Gotchas

1. **Public images are shared across all projects.** When listing images without an `owner` filter, you will see both project-owned (private) and platform-provided (public) images. Use `visibility=private` to see only your project's images.

2. **Size is in bytes, not GiB.** The `size` field is raw bytes. Divide by 1073741824 to get GiB. A null/zero size means the image data has not been uploaded yet (status will be `queued`).

3. **min_disk and min_ram are constraints.** These values (GiB and MiB respectively) define the minimum flavor requirements to boot a server from this image. Nova will reject a boot request if the flavor does not meet these minimums.

4. **Status "active" is the only bootable state.** Only images with `status=active` can be used to create servers. Images in `queued`, `saving`, or `deactivated` cannot be booted from.

5. **Container image vs VM image confusion.** Glance manages VM/bare-metal boot images (qcow2, raw, vmdk). For OCI container images, use Keppel (`sapcc-registry`). Users frequently confuse these.

6. **Deactivated images exist but cannot be used.** An admin can deactivate an image (e.g., due to CVE). It remains visible but cannot boot new servers. Existing servers using it are unaffected.

7. **disk_format determines hypervisor compatibility.** Common formats: `qcow2` (KVM), `vmdk` (VMware), `raw`. In SAP CC, most images are `vmdk` for vSphere-based regions.

## Common Workflows

### Find Available Boot Images

1. `glance_list_images` with `status=active` and `visibility=public` — see platform-provided images.
2. Note `min_disk` and `min_ram` to determine flavor requirements.
3. Check `disk_format` matches the target hypervisor in your availability zone.

### Check Why a Server Boot Failed Due to Image

1. `glance_get_image` with the image UUID from the failed server request.
2. Verify `status=active` — if not, the image is unusable.
3. Check `min_disk` and `min_ram` against the chosen flavor — insufficient resources cause boot failure.
4. Confirm `disk_format` is compatible with the target region's hypervisor.

### List Project-Owned Snapshots

1. `glance_list_images` with `visibility=private` and `owner=<project_id>`.
2. These are typically server snapshots or custom-uploaded images.
3. Check `size` to understand storage consumption (counts toward image quota).

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Server using this image | Nova | `nova_list_servers` (image field in response) |
| Image quota for the project | Limes | `limes_get_project_quota(service=image)` |
| Who uploaded/deleted an image | Hermes | `hermes_list_events(target_type=image)` |
| Container images (OCI) | Keppel | `keppel_list_repositories` |
