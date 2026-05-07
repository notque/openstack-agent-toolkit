# Limes Services and Resources Mapping

Which Limes services map to which resources. Use this to understand what you're looking at in quota responses.

## compute

| Resource | Unit | Notes |
|----------|------|-------|
| `cores` | count | vCPU cores across all instances |
| `ram` | MiB | **Not GB!** Divide by 1024 for GiB |
| `instances` | count | Total number of VMs |
| `server_groups` | count | Anti-affinity / affinity groups |
| `server_group_members` | count | Max members per server group |

## network

| Resource | Unit | Notes |
|----------|------|-------|
| `floating_ips` | count | Public IPv4 addresses |
| `networks` | count | Neutron networks |
| `subnets` | count | Subnets across all networks |
| `ports` | count | Virtual switch ports |
| `routers` | count | Neutron routers |
| `security_groups` | count | Firewall rule groups |
| `security_group_rules` | count | Individual firewall rules |
| `rbac_policies` | count | Cross-project sharing policies |

## object-store

| Resource | Unit | Notes |
|----------|------|-------|
| `capacity` | bytes | Total Swift storage capacity |

## sharev2 (Manila - Shared File Systems)

| Resource | Unit | Notes |
|----------|------|-------|
| `share_capacity` | GiB | Total shared filesystem capacity |
| `shares` | count | Number of file shares |
| `share_networks` | count | Share network objects |
| `share_snapshots` | count | Snapshots of shares |
| `snapshot_capacity` | GiB | Capacity used by snapshots |

## volumev2 (Cinder - Block Storage)

| Resource | Unit | Notes |
|----------|------|-------|
| `capacity` | GiB | Total block storage (all types combined) |
| `volumes` | count | Number of volumes (all types) |
| `snapshots` | count | Volume snapshots |
| `capacity_<type>` | GiB | Per-backend: `capacity_vmware`, `capacity_ceph` |
| `volumes_<type>` | count | Per-backend: `volumes_vmware`, `volumes_ceph` |
| `snapshots_<type>` | count | Per-backend: `snapshots_vmware`, `snapshots_ceph` |

**Volume type gotcha:** Generic `capacity` is the sum of all types. But each type has its own sub-quota. A project can have `capacity=500 GiB` total but only `capacity_vmware=200` and `capacity_ceph=300`. You must check the specific type.

## dns (Designate)

| Resource | Unit | Notes |
|----------|------|-------|
| `zones` | count | DNS zones managed |
| `recordsets` | count | DNS record sets across all zones |

## loadbalancing (Octavia)

| Resource | Unit | Notes |
|----------|------|-------|
| `loadbalancers` | count | Load balancer instances |
| `listeners` | count | LB listeners (frontends) |
| `pools` | count | LB backend pools |
| `pool_members` | count | Members across all pools |
| `healthmonitors` | count | Health check configurations |
| `l7policies` | count | Layer 7 routing policies |

## keppel (Container Registry)

| Resource | Unit | Notes |
|----------|------|-------|
| `images` | count | Container images stored |

## Common Service Filters

When using `service` parameter with Limes tools:

```
service=compute         → cores, ram, instances
service=network         → floating_ips, networks, ports, etc.
service=volumev2        → capacity, volumes, snapshots (all types)
service=object-store    → capacity (Swift)
service=sharev2         → shares, share_capacity
service=dns             → zones, recordsets
service=loadbalancing   → loadbalancers, listeners, pools
service=keppel          → images
```

When using `resource` parameter (must combine with `service`):

```
service=compute&resource=ram        → just RAM quota/usage
service=volumev2&resource=capacity  → just total volume capacity
```
