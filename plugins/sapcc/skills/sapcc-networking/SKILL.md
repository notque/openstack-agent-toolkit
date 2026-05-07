---
name: sapcc-networking
description: >
  Neutron networking operations: network topology, port inspection, security group debugging,
  connectivity troubleshooting. Triggers: network, subnet, port, security group, firewall,
  connectivity, "can't reach", interface, IP address, CIDR.
version: 1.0.0
metadata:
  service:
    - neutron
---

# SAP CC Networking (Neutron)

Investigate and debug network topology, port state, and security group rules in SAP Converged Cloud.

## MCP Tools

| Tool | Purpose | Key Filters |
|------|---------|-------------|
| `neutron_list_networks` | List networks | `name`, `status` |
| `neutron_list_subnets` | List subnets (CIDR, gateway, DHCP) | `network_id` |
| `neutron_list_ports` | List ports (MAC, fixed IPs, device_owner) | `network_id`, `device_id`, `status` |
| `neutron_list_security_groups` | List security groups with rules | — |

## Gotchas

These are the most common mistakes. Follow them exactly.

1. **Default security group blocks ALL inbound traffic.** Users assume "default" means permissive. It is not. The default group allows all egress but zero ingress. Always check security group rules when debugging connectivity.

2. **`device_owner` tells you what owns a port.** Key values:
   - `compute:nova` — VM network interface
   - `network:dhcp` — DHCP agent port
   - `network:router_interface` — Router attachment
   - `network:floatingip` — Floating IP anchor
   - Empty string — Unattached/orphaned port

3. **To find a server's ports, use `neutron_list_ports` with `device_id=<server_uuid>`.** Do not look for port information in Nova responses. Neutron is the source of truth for network interfaces.

4. **Security group rules are additive (whitelist-only).** There is no explicit deny. If traffic is not allowed by any rule, it is denied. You cannot "block port 22" — you can only not allow it.

5. **Ports in DOWN status may be detached OR the VM is shut off.** A DOWN port does not mean a problem — cross-reference with `nova_show_server` to check server power state. ACTIVE port + SHUTOFF server = normal (port state lags).

6. **`network_id` is required to correlate subnets to networks.** Subnets do not carry the network name. To map the full topology: list networks first, then list subnets filtered by each `network_id`.

7. **Fixed IPs in port response contain both `subnet_id` and `ip_address`.** To determine the CIDR range for a port's IP, use the `subnet_id` from the port's `fixed_ips` array to look up the subnet.

8. **SAP CC networks are provider networks (not self-service).** Users cannot create or delete networks. Network infrastructure is managed by platform operators. Users can only create ports, security groups, and floating IP associations.

9. **Security group is applied per-port, not per-server.** A server with multiple interfaces can have different security groups on each port. Always check the `security_groups` field on the specific port, not at the server level.

10. **Remote group rules create circular dependencies.** A security group rule referencing another group (remote_group_id) means "allow traffic from any port that has that group applied." This is how you allow intra-project communication without specifying IPs.

## Common Workflows

### "Why can't I reach my server?"

This is the most common networking question. Follow this sequence:

```
Step 1: Find the server's ports
  → neutron_list_ports(device_id=<server_uuid>)
  → Note the port status, fixed_ips, and security_groups

Step 2: Check security groups on those ports
  → neutron_list_security_groups()
  → Find the groups listed on the port
  → Verify inbound rules allow the protocol/port/source you need

Step 3: Verify subnet configuration
  → Use subnet_id from port's fixed_ips
  → neutron_list_subnets(network_id=<network_id>)
  → Check gateway_ip is set, DHCP is enabled if expected

Step 4: Verify network status
  → neutron_list_networks(name=<network_name>)
  → Confirm status is ACTIVE, admin_state_up is true
```

**Common findings:**
- Missing ingress rule (most common — see Gotcha #1)
- Wrong security group attached to port
- Port is DOWN because VM is SHUTOFF
- Subnet has no gateway (isolated network)

### Find All Network Interfaces for a Server

```
neutron_list_ports(device_id=<server_uuid>)
```

Each result is one NIC. For each port, extract:
- `mac_address` — correlates to OS-visible interface
- `fixed_ips[].ip_address` — assigned IPs
- `fixed_ips[].subnet_id` — which subnet it belongs to
- `network_id` — which network it connects to
- `security_groups` — applied firewall rules
- `status` — ACTIVE, DOWN, BUILD

### Audit Security Group Rules for a Project

```
Step 1: List all security groups
  → neutron_list_security_groups()

Step 2: For each group, examine rules
  → Look at security_group_rules array in response
  → Flag overly permissive rules (see Security Considerations)

Step 3: Cross-reference with ports
  → neutron_list_ports() to see which groups are actually in use
  → Groups not referenced by any port may be stale
```

### Map Network Topology

Build the full picture: network → subnets → ports → servers.

```
Step 1: List all networks
  → neutron_list_networks()

Step 2: For each network, list subnets
  → neutron_list_subnets(network_id=<id>)
  → Record CIDR, gateway, allocation_pools

Step 3: For each network, list ports
  → neutron_list_ports(network_id=<id>)
  → Group by device_owner to separate VMs from infrastructure

Step 4: Correlate ports to servers
  → Ports with device_owner="compute:nova" have device_id=server_uuid
  → Use nova_show_server(<device_id>) to get server name/status
```

## Troubleshooting

### Port ACTIVE but No Connectivity

1. Security group missing required ingress rule (check Gotcha #1)
2. Source IP not in allowed CIDR of the security group rule
3. Subnet has no gateway — network is intentionally isolated
4. MTU mismatch (rare, but check subnet MTU if large packets fail)
5. Anti-spoofing: traffic from IP not in port's `allowed_address_pairs` or `fixed_ips` is dropped

### Security Group Not Taking Effect

1. Wrong group attached — compare port's `security_groups` list to the group you edited
2. Rule direction wrong — `ingress` is traffic TO the port, `egress` is FROM the port
3. Ethertype mismatch — IPv4 rule won't match IPv6 traffic and vice versa
4. Protocol/port mismatch — rule says TCP but traffic is UDP, or port range excludes your port
5. Remote IP prefix too restrictive — source CIDR doesn't include the connecting client

### IP Conflict / Duplicate Address

1. Check if multiple ports have the same `fixed_ips[].ip_address` on the same subnet
2. Look for ports with `device_owner=""` (orphaned) holding the IP
3. Check `allowed_address_pairs` — another port may legitimately share the IP (VRRP/HA)

## Security Considerations

### Overly Permissive Rules (Flag These)

| Pattern | Risk | Recommendation |
|---------|------|----------------|
| `remote_ip_prefix: 0.0.0.0/0` on SSH (22) | Internet-exposed SSH | Restrict to bastion/VPN CIDR |
| `remote_ip_prefix: 0.0.0.0/0` on all ports | Fully open | Almost never correct — audit immediately |
| `protocol: null` (all protocols allowed) | No protocol restriction | Specify TCP/UDP/ICMP explicitly |
| Egress `0.0.0.0/0` to all ports | Unrestricted outbound | Acceptable for most workloads, flag for PCI |

### Before Modifying Security Groups

1. Identify all ports using the group: `neutron_list_ports()` and filter by security_groups containing the group ID
2. Understand the blast radius — one group change affects all attached ports
3. Check if it's the "default" group — almost every port uses it
4. Prefer adding a new group over modifying a shared one

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Server name/status for a port's device_id | Nova | `nova_show_server` |
| Who modified a security group? | Hermes | `hermes_list_events(target_type=security_group)` |
| Network quota remaining | Limes | `limes_get_project_quota` (service: networking) |
| DNS records for an IP | Designate | Not yet in MCP server |

## Reference Files

- `references/security-group-patterns.md` — Common SAP CC security group configurations and templates
