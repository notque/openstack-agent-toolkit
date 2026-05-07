---
name: sapcc-object-storage
description: >
  Object storage operations via Swift in SAP Converged Cloud.
  Triggers: object storage, swift, container, blob, S3, bucket, object, file upload
version: 1.0.0
metadata:
  service: [swift]
  task: [inspect, manage, debug]
  persona: [developer, platform-engineer]
---

# SAP CC Object Storage (Swift)

Inspect Swift object storage: list containers, browse objects, and retrieve object metadata. Swift provides S3-compatible, project-scoped object/blob storage.

## MCP Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `swift_list_containers` | List containers in current account | `prefix`, `limit` (returns: name, object count, total bytes) |
| `swift_list_objects` | List objects in a container | `container` (required), `prefix`, `delimiter`, `limit` (returns: name, bytes, content_type, last_modified, hash) |
| `swift_get_object_metadata` | Get metadata for a specific object | `container` (required), `object` (required) (returns: content_type, content_length, etag, last_modified) |

## Gotchas

### 1. These tools provide metadata only — no object content retrieval

You can list containers, list objects, and get object metadata. You CANNOT download or read object content through these tools. This prevents accidentally dumping large binary files into the LLM context.

### 2. Containers are flat namespaces with pseudo-directories

Swift does not have real directories. Use `delimiter=/` to create pseudo-directory listings. Objects named `logs/2024/01/data.json` appear as directory `logs/` when using `delimiter=/`.

### 3. Object count and bytes are at container level

`swift_list_containers` shows aggregate stats per container. Use for quick capacity assessment.

### 4. The `prefix` filter enables efficient browsing

Use `prefix` to navigate pseudo-directories:
- `prefix=logs/` → all objects starting with "logs/"
- `prefix=logs/2024/` → narrow to a year
- Combined with `delimiter=/` → see only immediate "children"

### 5. `limit` defaults to 100

Swift containers can hold millions of objects. Default returns first 100. Use prefix+delimiter for efficient navigation.

### 6. `hash` is the MD5 of the object content (etag)

Use it to verify object integrity or detect changes without downloading content.

### 7. Container names are URL-safe strings, not UUIDs

Unlike most OpenStack resources, containers are identified by name (not UUID). Case-sensitive.

### 8. Object storage is eventually consistent for overwrites

Read-after-write is consistent for new objects. Overwrites/deletes may take seconds to propagate.

## Common Workflows

### Inventory Storage Containers

```
1. swift_list_containers()
2. Review: container names, object counts, total bytes
3. Identify large containers or unusual names
```

### Browse Container Contents

```
1. swift_list_containers() → identify target
2. swift_list_objects(container=<name>, delimiter="/") → top-level
3. swift_list_objects(container=<name>, prefix=<dir/>, delimiter="/") → drill down
```

### Check Object Details

```
1. swift_list_objects(container=<name>, prefix=<path>) → find object
2. swift_get_object_metadata(container=<name>, object=<full_name>)
3. Review: size, content_type, last_modified
```

### Assess Storage Usage

```
1. swift_list_containers() → total bytes per container
2. Sum across containers for project total
3. Compare with quota: limes_get_project_quota(service=object-store)
```

## Troubleshooting

### Container not found

- Container names are case-sensitive — verify exact casing
- Check project scope: `keystone_token_info`

### Object listing returns empty

- Container may genuinely be empty
- `prefix` filter may be too restrictive — try without prefix

### Large container — cannot see all objects

- Use `prefix` + `delimiter` to navigate instead of listing all

## Security Considerations

- Object names and container names may reveal data classification
- `last_modified` timestamps reveal activity patterns
- Container listings expose data inventory — treat as confidential
- Never attempt to retrieve object content that might contain secrets

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Object storage quota | Limes | `limes_get_project_quota(service=object-store)` |
| Who uploaded/deleted objects | Hermes | `hermes_list_events(target_type=object-store/object)` |
| Container used by Keppel | Keppel | `keppel_list_accounts` (registry backing storage) |
| Project context | Keystone | `keystone_token_info` |
