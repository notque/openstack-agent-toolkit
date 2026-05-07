---
name: sapcc-object-storage
description: >
  Object storage operations via Swift. Triggers: object storage, swift,
  container, bucket, blob, s3. NOT for: block storage/volumes (use
  sapcc-storage/Cinder).
version: 1.0.0
metadata:
  service: [swift]
  task: [manage, inspect, debug]
  persona: [developer, platform-engineer]
---

# SAP CC Object Storage (Swift)

Inspect Swift containers and objects: list containers, browse object listings, check object metadata.

## MCP Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `swift_list_containers` | List containers in the account | `prefix` (name prefix filter), `limit` (number, default 100) |
| `swift_list_objects` | List objects in a container | `container` (name, required), `prefix`, `delimiter` (e.g. `/` for pseudo-dirs), `limit` (number, default 100) |
| `swift_get_object_metadata` | Get metadata for a specific object | `container` (name, required), `object` (name, required) |

## Gotchas

1. **This tool returns metadata only, never object content.** `swift_get_object_metadata` returns content_type, content_length, etag, and last_modified. It does NOT download or display the object body. You cannot read file contents through MCP tools.

2. **Container names are strings, not UUIDs.** Unlike most OpenStack resources, containers are identified by name, not UUID. Names are case-sensitive and URL-encoded.

3. **Delimiter creates pseudo-directories.** Setting `delimiter=/` causes Swift to group objects by prefix and return `subdir` entries. This simulates directory browsing but Swift is a flat namespace internally.

4. **Default limit is 100, not all objects.** Both list tools default to 100 results. Large containers may have thousands of objects. If you need to verify an object exists, use `prefix` to narrow results rather than paginating.

5. **Etag is MD5, not SHA.** The `etag` (hash) field in object listings and metadata is an MD5 digest. For large objects uploaded via SLO/DLO, the etag is an MD5 of the concatenated segment etags, not of the full content.

6. **Bytes are raw bytes, not human-readable.** Container `bytes` and object `bytes`/`content_length` are in raw bytes. Divide by appropriate power of 1024 for KiB/MiB/GiB.

## Common Workflows

### Browse Container Contents

1. `swift_list_containers` — get an overview of all containers and their sizes.
2. `swift_list_objects` with `container=<name>` and `delimiter=/` — browse top-level pseudo-directories.
3. `swift_list_objects` with `container=<name>` and `prefix=subdir/` and `delimiter=/` — drill into a subdirectory.

### Check if a Specific Object Exists

1. `swift_list_objects` with `container=<name>` and `prefix=<exact-object-name>`.
2. If the object appears in results, it exists. If empty results, it does not.
3. `swift_get_object_metadata` to confirm and get details (size, type, last modified).

### Assess Storage Usage

1. `swift_list_containers` — sum the `bytes` field across all containers for total usage.
2. Compare against quota from `limes_get_project_quota(service=object-store)`.
3. Identify large containers by `bytes` value and investigate with `swift_list_objects`.

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Object storage quota | Limes | `limes_get_project_quota(service=object-store)` |
| Who modified containers/objects | Hermes | `hermes_list_events(target_type=container)` |
| Block storage (volumes) instead | Cinder | `cinder_list_volumes` |
| S3 compatibility endpoint | Keystone | `keystone_list_services` (look for s3 type) |
