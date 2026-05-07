---
name: sapcc-registry
description: >
  Keppel container registry management for SAP Converged Cloud.
  Triggers: container image, registry, docker image, keppel, repository, manifest, tag, vulnerability scan, image version
version: 1.0.0
metadata:
  service: [keppel]
  task: [scan, inspect, manage]
  persona: [developer, devops]
---

# SAP CC Container Registry (Keppel)

Keppel is SAP CC's multi-tenant container image registry. Not vanilla OpenStack. It provides regionally federated, project-scoped image storage with integrated vulnerability scanning.

## MCP Tools

### Read Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `keppel_list_accounts` | List container image registry accounts | (none) |
| `keppel_get_account` | Get account detail (registry endpoint, replication config) | `account_name` (**required**) |
| `keppel_list_repositories` | List repos within an account | `account_name` (**required**) |
| `keppel_list_manifests` | List image manifests (tags) in a repo | `account_name` (**required**), `repo_name` (**required**) |
| `keppel_get_vulnerability_report` | Get vulnerability scan results for an image | `account_name` (**required**), `repo_name` (**required**), `digest` (**required**) |

> All Keppel tools are read-only. Image push/pull uses standard Docker/OCI registry protocol, not MCP.

### Guardrails

- **Path segment validation**: Account and repository names validated to prevent path traversal
- **Vulnerability data may be large**: Scan reports for images with many layers can be substantial

## Keppel Hierarchy

```
Account (registry namespace)
  └─ Repository (image name, e.g. "nginx")
       └─ Manifest (specific image version)
            ├─ Tags (human-readable: "latest", "v1.2.3")
            └─ Digest (immutable: "sha256:abc123...")
```

**Key distinctions:**
- Account ≈ namespace for image organization. One OpenStack project can own multiple accounts.
- Repository = just the image name. NOT the full registry path (not `registry.example.com/account/repo`).
- Manifest = a specific image build. Identified by digest (immutable) or tag (mutable pointer).

## Gotchas

### 1. Account ≠ OpenStack Project

A Keppel account is a registry namespace, not an OpenStack project. One project can have multiple accounts (e.g., `myproject-base`, `myproject-app`). The account name is an arbitrary string chosen at creation time.

### 2. Untagged manifests still consume storage

Manifests without tags are NOT automatically deleted. They accumulate from CI pipelines pushing new builds that overwrite existing tags. The old manifest loses its tag but persists. Garbage collection policies (if configured) handle cleanup, but this is not instant.

### 3. vulnerability_status values

Manifests report scan status as one of: `Clean`, `Low`, `Medium`, `High`, `Critical`, `Unknown`, `Unsupported`. `Unknown` = scan pending or incomplete. `Unsupported` = scanner cannot analyze this image format (e.g., Windows containers, scratch-based images with no OS packages).

### 4. Repository name is just the image name

When calling `keppel_list_manifests`, pass the bare image name: `nginx`, `my-app`, `tools/build-agent`. NOT the full registry URL. The account parameter already provides namespace context.

### 5. Account name is required to list repositories

You cannot list all repos across all accounts in one call. Flow is always: `keppel_list_accounts` → pick account → `keppel_list_repositories(account)`. No shortcut.

### 6. Cross-region federation

The same account name can exist in multiple regions. Images replicate automatically between regions (eventual consistency). A manifest pushed to `eu-de-1` will appear in `eu-nl-1` after replication completes. Replication is pull-on-demand — the remote region fetches layers when first requested.

### 7. Digests are immutable, tags are not

`sha256:abc123...` always points to the same image content. A tag like `latest` or `v1.0` can be moved to point to a different digest at any time. For reproducible deployments, pin to digest. Tags are convenience labels only.

### 8. Size is compressed layer size

The `size_bytes` field on manifests is the compressed (wire-transfer) size, not the extracted filesystem size. Actual disk usage after pulling can be 2-5x larger depending on compression ratio and layer contents.

## Common Workflows

### "What images do we have?"

```
1. keppel_list_accounts → enumerate namespaces
2. keppel_list_repositories(account) → list image repos per account
3. keppel_list_manifests(account, repository) → list versions per image
```

### "What version is deployed?"

Given a known image tag (from a deployment manifest or Helm chart):

```
1. keppel_list_manifests(account, repository)
2. Find manifest where tags contains the target tag (e.g., "v2.1.0")
3. Report: digest, push time, vulnerability_status
```

The digest confirms exactly which build is running regardless of tag moves.

### "Are there vulnerable images?"

```
1. keppel_list_accounts → get all accounts
2. For each account: keppel_list_repositories(account)
3. For each repo: keppel_list_manifests(account, repo)
4. Filter manifests where vulnerability_status in ("High", "Critical")
5. Report: account/repo:tag, severity, digest
```

Note: only manifests with completed scans will show severity. `Unknown` status means the scan hasn't finished — don't treat as "clean."

### "What's our storage usage?"

```
1. keppel_list_accounts → get all accounts
2. For each account: keppel_list_repositories(account)
3. For each repo: keppel_list_manifests(account, repo)
4. Sum size_bytes across all manifests
5. Report per-account and total (remember: compressed size, not extracted)
```

Layer deduplication means actual backend storage is less than the naive sum — shared layers between manifests are stored once.

## Troubleshooting

### Empty account (no repositories listed)

Causes:
- Account was just created, no images pushed yet
- Images were pushed to a different region and haven't replicated
- Permission issue — token may lack read access to this account
- All repositories were garbage collected (all manifests expired)

### Missing tags (manifest exists but no tag)

- Tag was overwritten by a newer push (CI pushed `latest` again)
- Tag was explicitly deleted via Keppel API
- The manifest is orphaned — it's just layers consuming storage now

### vulnerability_status = "Unknown" persisting

- Scan queue backlog — large images take time to scan
- Scanner service may be degraded — check region health
- Image was just pushed — allow 5-15 minutes for initial scan
- If persistent (>1 hour): scanner cannot reach the image layers (network issue)

### Image pull fails but manifest shows in list

- Replication incomplete — manifest metadata arrived but layers haven't replicated yet
- Storage backend issue — layers corrupted or missing from swift/S3
- Manifest is a multi-arch index and local platform architecture isn't available

## Security

- **Image layers may contain secrets.** Embedded credentials, API keys, and tokens in image layers are permanently baked in. Rebuilding with secrets removed doesn't delete old manifests — the old layers still exist until garbage collected.
- **Vulnerability scanning is passive.** Keppel scans for known CVEs but does NOT block image pulls. A `Critical` vulnerability status is informational only — the image remains pullable.
- **Account access follows OpenStack RBAC.** Token scope determines which accounts are visible. Cross-project image sharing requires explicit account policies.
- **Digest exposure is safe.** Sharing a `sha256:...` digest does not grant pull access — authentication is still enforced. But digests do confirm whether two environments run the same build.

## Routing

| User need | Action |
|-----------|--------|
| Image lifecycle and vulnerability workflow | Read [image-lifecycle.md](references/image-lifecycle.md) |
