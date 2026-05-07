# SAP CC Flavor Families

## Naming Convention

```
<family><generation>_<size>
```

Examples: `m2_xlarge`, `r1_large`, `c3_2xlarge`

## Families

| Prefix | Family | Optimized For | Use Case |
|--------|--------|---------------|----------|
| `m` | General Purpose | Balanced CPU:RAM ratio | Web servers, application servers, dev/test |
| `r` | Memory-Optimized | High RAM per vCPU | Databases, in-memory caches, SAP HANA sidecars |
| `c` | Compute-Optimized | High vCPU per RAM | Batch processing, CI/CD workers, HPC |

## Generations

Higher generation = newer hardware and potentially better price/performance.
Not all generations are available in all regions.

| Generation | Typical Hardware | Notes |
|------------|-----------------|-------|
| 1 | Legacy (may be deprecated) | Check availability before recommending |
| 2 | Current default | Safe choice for most workloads |
| 3 | Latest | Best performance, may have limited availability |

## Sizes

Sizes scale within a family/generation. Exact vCPU/RAM values vary by family — always confirm with `nova_list_flavors`.

| Size | Relative Scale |
|------|---------------|
| `small` | Minimum viable |
| `medium` | 2x small |
| `large` | 2x medium |
| `xlarge` | 2x large |
| `2xlarge` | 2x xlarge |
| `4xlarge` | 2x 2xlarge |
| `8xlarge` | 2x 4xlarge (where available) |

## Selection Guidance

| Workload | Recommended Family | Why |
|----------|--------------------|-----|
| Generic web app | `m2_large` or `m2_xlarge` | Balanced, cost-effective |
| PostgreSQL / MySQL | `r2_large` or larger | Databases need RAM for buffer pools |
| Redis / Memcached | `r2_xlarge` or larger | In-memory stores are RAM-bound |
| CI runners | `c2_large` | Build jobs are CPU-bound, transient |
| Kubernetes nodes | `m2_2xlarge` or larger | Need headroom for pod scheduling |
| Batch ETL | `c2_xlarge` | CPU-bound, short-lived |

## Important Notes

- **Always verify with `nova_list_flavors`** — flavor availability varies by region and project.
- **Flavor IDs are UUIDs**, not the human-readable names. The API accepts both, but responses use UUIDs.
- **Some flavors are project-scoped** — your project may have access to custom flavors not visible globally.
- **Deprecated flavors** may still appear in listings but cannot be used for new instances. Check if existing servers use deprecated flavors before recommending resize.
- **RAM is in MiB** in flavor definitions. A flavor showing `ram: 8192` means 8 GiB.
