---
name: sapcc-baremetal
description: >
  Bare metal node operations via Ironic. Triggers: baremetal, bare metal, ironic,
  node, provision state, hardware, physical server. NOT for: virtual servers
  (use sapcc-compute/Nova).
version: 1.0.0
metadata:
  service: [ironic]
  task: [manage, inspect, debug]
  persona: [platform-engineer, operator]
---

# SAP CC Bare Metal (Ironic)

Inspect baremetal nodes: list nodes, check provision/power states, understand maintenance status and driver configuration.

## MCP Tools

### Read Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `ironic_list_nodes` | List baremetal nodes | `provision_state`, `maintenance` (true/false), `driver`, `resource_class`, `instance_uuid`, `fault`, `owner` |
| `ironic_get_node` | Full node detail (sensitive fields excluded) | `node_id` (**required**, UUID or name) |
| `ironic_list_node_ports` | List NICs for a node | `node_id` (**required**) |
| `ironic_list_allocations` | List node allocations | `node_id`, `resource_class` |
| `ironic_list_portgroups` | List port groups (bonded NICs) | `node_id` |

### Admin Tools (requires MCP_ADMIN_TOOLS=true)

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `ironic_list_chassis`† | List baremetal chassis | (none) |
| `ironic_node_power_state`†* | Change node power state | `node_id` (**required**), `target` (**required**: `power on`/`power off`/`rebooting`), `confirmed` |

### Security: Credential Isolation

- **DriverInfo excluded**: Node detail NEVER exposes BMC credentials (IPMI passwords, Redfish creds, iDRAC secrets)
- **DriverInternalInfo excluded**: Internal provisioning state with potential secrets omitted
- **InstanceInfo excluded**: Nova instance provisioning details omitted
- **Properties excluded**: Hardware properties that may contain sensitive deployment info

### Guardrails

- **Path segment validation**: `node_id` accepts both UUID and human-readable names safely
- **Power state allowlist**: Only `power on`, `power off`, `rebooting` accepted as targets
- **Confirmation required**: Power state changes return preview unless `confirmed=true`
- **Destructive action gate**: The `destructive-action-gate` hook blocks `ironic_node_power_state` until user approves

## Gotchas

1. **Sensitive fields are redacted.** The MCP tool intentionally omits `driver_info`, `driver_internal_info`, `instance_info`, and `properties` from `ironic_get_node` responses. These may contain BMC credentials (IPMI passwords, Redfish secrets). Do not tell users these fields are accessible.

2. **maintenance filter is a string "true", not a boolean.** Pass `maintenance="true"` as a string value. There is no `"false"` filter — omit the parameter to see all nodes regardless of maintenance status.

3. **provision_state vs power_state.** `provision_state` is the lifecycle state (available, deploying, active, error). `power_state` is the physical state (power on, power off). A node can be `active` provision but `power off` if manually shut down.

4. **"available" means ready for deployment.** In Ironic, `available` does not mean "has capacity" — it means the node is enrolled, inspected, cleaned, and ready to receive a workload. `active` means already deployed.

5. **instance_uuid links to Nova.** When a node is in `active` state, `instance_uuid` shows which Nova server is running on it. Use this to cross-reference with `nova_get_server`.

6. **node_id accepts UUID or name.** Unlike most OpenStack tools that require UUIDs, `ironic_get_node` accepts either the node UUID or its human-readable name.

7. **last_error contains deployment failure details.** When `provision_state=error`, the `last_error` field in the get response describes what went wrong (e.g., timeout during deploy, cleaning failure, network boot failure).

## Common Workflows

### List Nodes Available for Deployment

1. `ironic_list_nodes` with `provision_state=available` — show nodes ready for workloads.
2. Filter by `resource_class` if you need a specific hardware profile.
3. Verify `maintenance=false` in results — maintenance nodes cannot be deployed to.

### Diagnose a Node in Error State

1. `ironic_list_nodes` with `provision_state=error` — find all error nodes.
2. `ironic_get_node` with `node_id=<uuid>` — check `last_error` for the failure reason.
3. Check `maintenance` and `maintenance_reason` — the node may have been put in maintenance due to the error.
4. Check `fault` field for categorized fault information.

### Find the Physical Node Running a VM

1. Start with the Nova server UUID.
2. `ironic_list_nodes` — scan results for `instance_uuid` matching your server UUID.
3. Or if you know the node: `ironic_get_node` and check `instance_uuid`.

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| VM running on this node | Nova | `nova_get_server(<instance_uuid>)` |
| Who modified node state | Hermes | `hermes_list_events(target_type=node)` |
| Compute quota (includes baremetal flavors) | Limes | `limes_get_project_quota(service=compute)` |
| Network ports attached to node | Neutron | `neutron_list_ports` |
