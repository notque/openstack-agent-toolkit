# Keppel Image Lifecycle & Federation Model

## Image Lifecycle

### Push Flow

```
docker push registry.region.cloud.sap/account/repo:tag
  1. Client authenticates via OpenStack token
  2. Layers uploaded to account's backing storage (Swift/S3)
  3. Manifest created linking layers together
  4. Tag pointer set to new manifest digest
  5. Previous manifest (if tag existed) becomes untagged
  6. Vulnerability scanner queues new manifest for analysis
```

### Pull Flow

```
docker pull registry.region.cloud.sap/account/repo:tag
  1. Client authenticates via OpenStack token
  2. Tag resolved to manifest digest
  3. Manifest fetched → layer list retrieved
  4. Layers downloaded from backing storage
  5. If layer missing locally → triggers replication from primary region
```

### Manifest States

| State | Meaning | Action |
|-------|---------|--------|
| Tagged + Clean | Active image, no vulnerabilities | Normal operation |
| Tagged + Critical | Active image, severe CVEs found | Rebuild with patched base image |
| Tagged + Unknown | Active image, scan incomplete | Wait 5-15 min, check again |
| Untagged + Clean | Orphaned but safe | Candidate for garbage collection |
| Untagged + Critical | Orphaned and vulnerable | Priority cleanup target |

### Garbage Collection

Keppel garbage collection is policy-driven per account:

- **Untagged manifests**: Deleted after configurable retention period (default varies by account policy)
- **Tagged manifests**: Never auto-deleted while tag exists
- **Shared layers**: Only deleted when no manifest references them
- **Soft-delete window**: Deleted manifests may be recoverable briefly (implementation-dependent)

GC does NOT run continuously. It's periodic. Expect latency between a manifest becoming untagged and actual storage reclamation.

## Federation Model

### Architecture

```
Region A (eu-de-1)          Region B (eu-nl-1)          Region C (ap-jp-1)
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│ Keppel Registry  │       │ Keppel Registry  │       │ Keppel Registry  │
│                  │◄─────►│                  │◄─────►│                  │
│ account: myapp   │       │ account: myapp   │       │ account: myapp   │
│ repo: frontend   │       │ repo: frontend   │       │ repo: frontend   │
└──────────────────┘       └──────────────────┘       └──────────────────┘
        │                          │                          │
        ▼                          ▼                          ▼
  Swift/S3 (local)           Swift/S3 (local)          Swift/S3 (local)
```

### Replication Behavior

- **Pull-on-demand**: Layers are NOT eagerly replicated. When a client in Region B pulls an image that was pushed to Region A, Region B fetches the layers from Region A on first request.
- **Manifest sync**: Manifest metadata (tags, digests, vulnerability status) syncs between regions. You can list manifests in any region even if layers aren't local yet.
- **Consistency model**: Eventually consistent. Tag updates propagate within seconds to minutes. Layer availability depends on pull triggers.
- **Primary region**: The region where the image was originally pushed. It's the authoritative source for layers until replication completes.

### Federation Implications

| Scenario | Behavior |
|----------|----------|
| Push to eu-de-1, pull from eu-nl-1 | First pull is slower (cross-region layer fetch). Subsequent pulls are local-speed. |
| Tag update in eu-de-1 | Tag pointer updates in all regions within seconds. |
| Delete in eu-de-1 | Deletion replicates. Other regions lose access after sync. |
| Region outage (eu-de-1 down) | If layers already replicated to eu-nl-1, pulls succeed. If not replicated, pulls fail. |
| Same account name, different content | Not possible — federation ensures consistency. Same account = same content everywhere. |

### Cross-Region Considerations

- **First pull latency**: Budget extra time for first pull in a non-primary region. Layer download crosses region boundaries.
- **Disaster recovery**: Critical images should be pulled at least once in each region to ensure layers are locally cached.
- **Storage costs**: Replicated layers consume storage in each region they're pulled to. More regions pulling = more storage used.
- **Network costs**: Cross-region replication incurs network transfer charges.

## Retention Strategy Recommendations

### For CI/CD pipelines

- Tag releases with semver: `v1.2.3` (never delete)
- Use `latest` or branch tags for development (accept overwrites)
- Set GC policies to clean untagged manifests after 7-14 days

### For production images

- Pin deployments to digest, not tag
- Maintain at least N-2 tagged versions for rollback
- Monitor vulnerability_status on all tagged manifests
- Rebuild and re-push when base image CVEs are published

### For multi-arch images

- Push manifest lists (multi-arch indexes) that reference per-platform manifests
- Each platform manifest has its own vulnerability scan
- A manifest list shows as a single entry with aggregated vulnerability status
