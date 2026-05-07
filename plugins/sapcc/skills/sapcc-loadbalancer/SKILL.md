---
name: sapcc-loadbalancer
description: >
  Load balancer operations via Octavia. Triggers: load balancer, lb, listener,
  pool, vip, octavia, l7. NOT for: network ports or security groups (use
  sapcc-networking).
version: 1.0.0
metadata:
  service: [octavia]
  task: [manage, inspect, debug]
  persona: [developer, platform-engineer]
---

# SAP CC Load Balancer (Octavia)

Manage Octavia load balancers: list/inspect LBs, listeners, and pools. Understand the LB topology and troubleshoot provisioning issues.

## MCP Tools

### Read Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `octavia_list_loadbalancers` | List load balancers | `name`, `provisioning_status`, `vip_address`, `operating_status`, `vip_subnet_id`, `provider` |
| `octavia_get_loadbalancer` | Full LB detail by UUID | `loadbalancer_id` (**required**) |
| `octavia_list_listeners` | List listeners | `name`, `protocol` (TCP/HTTP/HTTPS/TERMINATED_HTTPS/UDP/SCTP), `loadbalancer_id`, `protocol_port` |
| `octavia_list_pools` | List backend pools | `name`, `protocol`, `loadbalancer_id`, `lb_algorithm` (ROUND_ROBIN/LEAST_CONNECTIONS/SOURCE_IP) |
| `octavia_list_members` | List pool members | `pool_id` (**required**), `name`, `address` |
| `octavia_list_healthmonitors` | List health monitors | `pool_id`, `type` (HTTP/HTTPS/PING/TCP/TLS-HELLO/UDP-CONNECT) |
| `octavia_list_l7policies` | List L7 routing policies | `listener_id`, `name` |
| `octavia_list_l7rules` | List rules for L7 policy | `l7policy_id` (**required**) |

### Write Tools (requires MCP_READ_ONLY=false)

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `octavia_create_loadbalancer`* | Create a new load balancer | `name` (**required**), `vip_subnet_id` (**required**), `description`, `confirmed` |
| `octavia_delete_loadbalancer`* | Delete a load balancer | `loadbalancer_id` (**required**), `cascade` (bool, deletes children), `confirmed` |

### Admin Tools (requires MCP_ADMIN_TOOLS=true)

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `octavia_list_amphorae`† | List amphora instances | `loadbalancer_id`, `status` |

### Guardrails

- **UUID validation**: All `*_id` parameters validated
- **Confirmation required**: Write tools return preview unless `confirmed=true`
- **Cascade delete**: `octavia_delete_loadbalancer` with `cascade=true` deletes ALL child resources (listeners, pools, members, monitors)

## Gotchas

1. **Two status fields: provisioning vs operating.** `provisioning_status` tracks the API/control plane state (ACTIVE, PENDING_CREATE, ERROR). `operating_status` tracks the data plane (ONLINE, DEGRADED, ERROR, NO_MONITOR). A LB can be ACTIVE provisioning but DEGRADED operating.

2. **Immutable during PENDING states.** When `provisioning_status` is any PENDING_* value, no mutations are allowed on the LB or its children (listeners, pools). Wait for ACTIVE before making changes.

3. **Listener protocol determines TLS handling.** `TERMINATED_HTTPS` means TLS terminates at the LB (requires certificate). `HTTPS` means passthrough — the LB forwards encrypted traffic without inspecting it. Do not confuse these.

4. **Pool lb_method values are algorithm names.** Common values: `ROUND_ROBIN`, `LEAST_CONNECTIONS`, `SOURCE_IP`. These are not free-text — use the exact enum values.

5. **loadbalancer_id filter on listeners/pools is optional.** Without it, you get all listeners/pools in the project. Always filter by `loadbalancer_id` when investigating a specific LB to avoid confusion.

6. **VIP address is on a subnet.** The `vip_address` is allocated from `vip_subnet_id`. If you need the network context, look up the subnet in Neutron.

7. **Topology: LB -> Listeners -> Pools -> Members.** Members are not exposed via MCP tools. You can see `default_pool_id` on listeners to trace which pool handles traffic.

## Common Workflows

### Map Full LB Topology

1. `octavia_get_loadbalancer` with `loadbalancer_id` — note the VIP, status, and provider.
2. `octavia_list_listeners` with `loadbalancer_id=<uuid>` — see all frontend listeners (protocol + port).
3. `octavia_list_pools` with `loadbalancer_id=<uuid>` — see all backend pools and their algorithms.
4. Match `default_pool_id` from listeners to pool IDs to understand traffic flow.

### Diagnose LB in ERROR State

1. `octavia_get_loadbalancer` — check `provisioning_status` and `operating_status`.
2. If provisioning ERROR: the control plane failed (network issue, quota, amphora boot failure). Check `hermes_list_events`.
3. If operating ERROR/DEGRADED: backend members are unhealthy. Pool health monitors are detecting failures.

### Find LB by VIP Address

1. `octavia_list_loadbalancers` with `vip_address=<ip>` — returns the matching LB.
2. If no results, the IP may be a floating IP mapped to the VIP — check `neutron_list_floating_ips`.

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Subnet details for VIP | Neutron | `neutron_list_subnets(<vip_subnet_id>)` |
| Who created/modified the LB | Hermes | `hermes_list_events(target_type=loadbalancer)` |
| LB quota for the project | Limes | `limes_get_project_quota(service=network)` |
| Server behind a pool member | Nova | `nova_get_server(<member_server_id>)` |
| Floating IP pointing to VIP | Neutron | `neutron_list_floating_ips` |
