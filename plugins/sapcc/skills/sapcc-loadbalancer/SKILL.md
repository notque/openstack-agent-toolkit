---
name: sapcc-loadbalancer
description: >
  Load balancer management via Octavia in SAP Converged Cloud.
  Triggers: load balancer, octavia, listener, pool, VIP, health monitor, L7, reverse proxy, LB
version: 1.0.0
metadata:
  service: [octavia]
  task: [inspect, manage, debug]
  persona: [developer, platform-engineer]
---

# SAP CC Load Balancers (Octavia)

Inspect Octavia load balancers: list LBs, view listeners and pools, and troubleshoot connectivity. Octavia provides L4/L7 load balancing as a service.

## MCP Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `octavia_list_loadbalancers` | List LBs in current project | `name`, `provisioning_status`, `operating_status`, `vip_address`, `vip_subnet_id`, `provider` |
| `octavia_get_loadbalancer` | Full detail for a single LB | `loadbalancer_id` (UUID) |
| `octavia_list_listeners` | List listeners | `loadbalancer_id`, `name`, `protocol`, `protocol_port` |
| `octavia_list_pools` | List backend pools | `loadbalancer_id`, `name`, `protocol`, `lb_algorithm` |

## Octavia Object Model

```
Load Balancer (VIP address)
├── Listener (protocol:port — e.g., HTTPS:443)
│   └── Pool (backend group)
│       ├── Member (backend server:port)
│       ├── Member
│       └── Health Monitor (checks member health)
└── Listener (HTTP:80)
    └── Pool
        └── Members...
```

## Gotchas

### 1. Two status fields — provisioning vs operating

| Field | Meaning |
|-------|---------|
| `provisioning_status` | Infrastructure state: ACTIVE, PENDING_CREATE, PENDING_UPDATE, ERROR |
| `operating_status` | Traffic state: ONLINE, OFFLINE, DEGRADED, ERROR, NO_MONITOR |

A LB can be `provisioning_status=ACTIVE` but `operating_status=DEGRADED` if some members are down.

### 2. VIP address is the entry point

The Virtual IP (VIP) is what clients connect to. It's on a specific subnet. DNS should point to this address. The VIP does NOT change when backend members are added/removed.

### 3. Listeners define what traffic to accept

Each listener binds protocol+port. You cannot have two listeners on the same port. Common patterns:
- HTTPS:443 (with TLS termination via Barbican cert)
- HTTP:80 (redirect to HTTPS or direct)
- TCP:3306 (database passthrough)

### 4. Pools define where traffic goes

A pool groups backend members (servers). Key attributes:
- `lb_algorithm`: ROUND_ROBIN, LEAST_CONNECTIONS, SOURCE_IP
- Members are server IP:port pairs
- Health monitor checks member availability

### 5. TERMINATED_HTTPS means TLS terminates at the LB

The LB decrypts HTTPS, forwards plain HTTP to backends. Requires a Barbican certificate reference. Backends only need to handle HTTP.

### 6. Operating status NO_MONITOR = no health checks configured

Without a health monitor, the LB cannot detect down members. Traffic goes to all members regardless of health. Always configure health monitors in production.

### 7. Providers: amphora vs ovn

- `amphora`: Full-featured (L7 rules, TLS termination, health monitors). Uses dedicated VMs.
- `ovn`: Lightweight L4 only. Lower overhead but fewer features.

### 8. Filter listeners/pools by loadbalancer_id

Without `loadbalancer_id` filter, you get ALL listeners/pools across all LBs in the project. Always filter by LB for a specific investigation.

## Common Workflows

### Inventory Load Balancers

```
1. octavia_list_loadbalancers()
2. Review: name, VIP address, provisioning/operating status
3. Flag any with operating_status != ONLINE
```

### Full LB Topology

```
1. octavia_get_loadbalancer(loadbalancer_id=<uuid>) → VIP, status
2. octavia_list_listeners(loadbalancer_id=<uuid>) → what ports are open
3. octavia_list_pools(loadbalancer_id=<uuid>) → backend groups + members
```

### Find LB by VIP Address

```
1. octavia_list_loadbalancers(vip_address=<ip>)
2. Or: neutron_list_ports() and match fixed_ips to the VIP
```

### Troubleshoot Degraded LB

```
1. octavia_get_loadbalancer(loadbalancer_id) → check operating_status
2. octavia_list_pools(loadbalancer_id) → check pool operating_status
3. If DEGRADED: some members are failing health checks
4. Verify backend servers are running: nova_list_servers
5. Check security groups allow health check traffic: neutron_list_security_groups
```

## Troubleshooting

### LB provisioning_status is ERROR

- Check Hermes: `hermes_list_events(target_type=loadbalancer)` for failure details
- Common causes: subnet full (no IP for VIP), quota exhausted, backend unavailable
- May need to delete and recreate

### LB operating_status is OFFLINE

- All members are failing health checks
- Check backend servers are running and healthy
- Verify security groups allow traffic from the LB subnet to member ports

### operating_status is DEGRADED

- Some but not all members are unhealthy
- Identify failing members via pool status
- Common: one server crashed or is overloaded

### Listener on port 443 but no HTTPS

- Check if listener protocol is `TERMINATED_HTTPS` (needs Barbican cert)
- Or `TCP` (passthrough — TLS handled by backend)
- `HTTP` on 443 works but is plain HTTP on a non-standard port

## Security Considerations

- VIP addresses reveal public-facing services
- Listener protocols reveal what services are exposed
- Pool members reveal backend server topology
- Health monitor endpoints may be unauthenticated — check they don't expose sensitive data
- TERMINATED_HTTPS references Barbican certificates — cert rotation matters

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| VIP subnet details | Neutron | `neutron_list_subnets` |
| Backend server status | Nova | `nova_get_server(<member_server_id>)` |
| TLS certificates | Barbican | `barbican_get_secret` (cert referenced by listener) |
| Who modified the LB | Hermes | `hermes_list_events(target_type=loadbalancer)` |
| DNS pointing to VIP | Designate | `designate_list_recordsets(data=<vip_address>)` |
| LB quota | Limes | `limes_get_project_quota(service=network)` |
