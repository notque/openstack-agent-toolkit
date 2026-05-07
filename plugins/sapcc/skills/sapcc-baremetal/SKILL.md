---
name: sapcc-baremetal
description: >
  Bare metal node management via Ironic in SAP Converged Cloud.
  Triggers: bare metal, ironic, physical server, baremetal, BMC, IPMI, redfish, hardware
version: 1.0.0
metadata:
  service: [ironic]
  task: [inspect, manage, debug]
  persona: [platform-engineer]
---

# SAP CC Bare Metal (Ironic)

Inspect Ironic bare metal nodes: list nodes, check provision/power states, and understand maintenance status. Ironic manages physical servers in the cloud, enabling bare metal provisioning alongside VMs.

## MCP Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `ironic_list_nodes` | List baremetal nodes | `provision_state`, `maintenance`, `driver`, `resource_class`, `instance_uuid`, `fault`, `owner` |
| `ironic_get_node` | Full detail for a single node | `node_id` (UUID or name) |

## Security Note

**BMC credentials (IPMI/Redfish passwords) are intentionally excluded from responses.** The MCP server strips `driver_info` and `properties` fields that may contain hardware management credentials. This is a security boundary.

## Gotchas

### 1. Provision state is the lifecycle — not power state

| provision_state | Meaning |
|----------------|---------|
| `available` | Ready to be provisioned (no instance) |
| `active` | Running an instance |
| `deploying` | Instance being deployed onto the node |
| `cleaning` | Being wiped between tenants |
| `error` | Failed operation — needs investigation |
| `manageable` | Enrolled but not yet made available |

### 2. Power state is separate from provision state

A node can be `provision_state=active` but `power_state=power off` (unexpected shutdown). Power states: `power on`, `power off`, `None` (unknown).

### 3. Maintenance mode = node excluded from scheduling

When `maintenance=true`, Nova will not schedule new instances to this node. Existing instances may still be running. Maintenance is set manually by operators or automatically on repeated failures.

### 4. instance_uuid links to Nova

When a node has an instance deployed, `instance_uuid` contains the Nova server UUID. Use `nova_get_server(instance_uuid)` to see the VM running on this hardware.

### 5. resource_class determines scheduling

Nodes declare their resource class (e.g., `baremetal`, `baremetal.large`). Nova flavors reference these classes to match workloads to appropriate hardware.

### 6. driver indicates management protocol

Common drivers: `ipmi` (legacy BMC), `redfish` (modern REST-based BMC). The driver determines how the node is powered on/off and booted.

### 7. fault indicates why a node is broken

When a node enters error/maintenance, the `fault` field explains why: `power failure`, `clean failure`, `deploy failure`, etc. This is the first thing to check for broken nodes.

### 8. Nodes are owned by projects

The `owner` field shows which project can provision instances on this node. Filter by owner to see nodes allocated to your project.

## Common Workflows

### Inventory Bare Metal Nodes

```
1. ironic_list_nodes()
2. Review: name/UUID, provision_state, power_state, maintenance
3. Flag any in error state or maintenance
```

### Find Available Nodes

```
1. ironic_list_nodes(provision_state=available, maintenance=false)
2. These nodes are ready for instance deployment
3. Check resource_class to match with desired flavor
```

### Check What Instance Runs on a Node

```
1. ironic_get_node(node_id=<uuid>) → note instance_uuid
2. nova_get_server(server_id=<instance_uuid>) → instance details
```

### Troubleshoot a Node in Error

```
1. ironic_get_node(node_id=<uuid>) → check fault field
2. Check maintenance flag — was it set automatically?
3. Check provision_state for last failed transition
4. hermes_list_events(target_type=baremetal/node, target_id=<uuid>)
```

### Find Nodes by Owner Project

```
1. ironic_list_nodes(owner=<project_uuid>)
2. Shows all nodes allocated to that project
3. Combine with provision_state filter for specific views
```

## Troubleshooting

### Node in error state

- Check `fault` field first — it describes the failure
- Common faults: `power failure` (BMC unreachable), `clean failure` (disk wipe failed), `deploy failure` (image deployment failed)
- Check Hermes for the triggering event

### Node stuck in "deploying"

- Deployment may have timed out
- Check if the node lost network connectivity during deploy
- BMC may be unresponsive — the node can't be power-cycled

### Node in maintenance unexpectedly

- May have been set automatically after repeated failures
- Check `maintenance_reason` in node details
- Requires operator intervention to clear maintenance flag

### Power state is "None"

- BMC is unreachable — can't determine actual power state
- Check network connectivity to the BMC/management network
- Driver may need reconfiguration

## Security Considerations

- Node listings reveal physical infrastructure topology
- resource_class and driver info reveal hardware types and management protocols
- instance_uuid mapping reveals which workloads run on which physical hardware
- Physical access to BMC = full control of hardware — BMC credential exposure is critical
- Maintenance patterns reveal infrastructure health/reliability

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Instance on a node | Nova | `nova_get_server(<instance_uuid>)` |
| Who modified node state | Hermes | `hermes_list_events(target_type=baremetal/node)` |
| Node network ports | Neutron | `neutron_list_ports(device_id=<node_uuid>)` |
| Compute quota for baremetal | Limes | `limes_get_project_quota(service=compute)` |
