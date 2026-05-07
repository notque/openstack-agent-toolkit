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

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `ironic_list_nodes` | List baremetal nodes with filters | `provision_state` (active, available, deploying, error), `maintenance` ("true" for maintenance-only), `driver` (ipmi, redfish), `resource_class` |
| `ironic_get_node` | Full detail for a single node | `node_id` (UUID or name, required) |

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
