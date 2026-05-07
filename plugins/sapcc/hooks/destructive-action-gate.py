#!/usr/bin/env python3
"""PreToolUse hook: Block destructive MCP tool calls unless user approves.

This hook fires before any MCP tool invocation. If the tool is classified
as destructive (deletes data, stops services, modifies security), it blocks
the call and requires explicit user approval.

The LLM's behavioral rules say "ask before destructive actions" — this hook
ENFORCES it. The LLM cannot rationalize past a hook.

Exit codes:
  0 = allow (tool is safe or already approved)
  2 = block with message (destructive, needs approval)
"""
from __future__ import annotations

import json
import os
import sys

# --- Destructive tool patterns ---
# Format: tool_name → human-readable consequence
DESTRUCTIVE_TOOLS: dict[str, str] = {
    # Nova - compute
    "nova_server_action": None,  # Special: only some actions are destructive
    # Cinder - storage
    "cinder_delete_volume": "Permanently deletes the volume and all data on it. Cannot be undone.",
    "cinder_delete_snapshot": "Permanently deletes the volume snapshot. Cannot be undone.",
    # Neutron - networking
    "neutron_delete_port": "Removes the network port. Connected instances lose network connectivity.",
    "neutron_delete_network": "Deletes the network and all associated subnets/ports.",
    "neutron_delete_subnet": "Removes the subnet. Ports using this subnet lose IP assignments.",
    "neutron_delete_security_group": "Removes the security group. Ports referencing it lose those rules.",
    "neutron_delete_security_group_rule": "Removes a security group rule. May block traffic that was previously allowed.",
    "neutron_delete_router": "Deletes the router. Connected subnets lose external connectivity.",
    # Keystone - identity
    "keystone_delete_application_credential": "Revokes the application credential. Services using it will fail to authenticate.",
    "keystone_delete_project": "Deletes the project and schedules all resources for cleanup.",
    # Designate - DNS
    "designate_delete_zone": "Deletes the DNS zone and ALL recordsets within it.",
    "designate_delete_recordset": "Removes the DNS record. Services depending on this name will fail to resolve.",
    # Octavia - load balancer
    "octavia_delete_loadbalancer": "Deletes the load balancer. All traffic routing through it stops.",
    "octavia_delete_pool": "Removes the backend pool. Load balancer has no targets.",
    "octavia_delete_listener": "Removes the listener. Traffic on that port/protocol is no longer accepted.",
    # Barbican - secrets
    "barbican_delete_secret": "Permanently deletes the secret/certificate. Services referencing it will fail.",
    # Manila - shared storage
    "manila_delete_share": "Deletes the shared file system. All mount points become unavailable.",
    # Swift - object storage
    "swift_delete_container": "Deletes the container and all objects within it.",
    "swift_delete_object": "Permanently deletes the object. Cannot be undone.",
    # Glance - images
    "glance_delete_image": "Permanently deletes the image. VMs using it as a base are unaffected, but no new VMs can boot from it.",
    # Neutron - floating IPs (PR #13)
    "neutron_delete_floating_ip": "Releases the floating IP back to the pool. External access via this IP is lost immediately.",
    # Nova - create (not destructive but resource-consuming)
    # Cinder - create (not destructive but resource-consuming)
    # Ironic - admin power state changes
    "ironic_node_power_state": "Changes physical server power state. May disrupt running workloads on bare metal.",
}

# Nova server actions that are destructive (not all actions are)
DESTRUCTIVE_SERVER_ACTIONS = {
    "stop": "Powers off the instance. All active connections are dropped.",
    "reboot": None,  # Special: only HARD reboot is destructive
    "delete": "Permanently destroys the instance and its ephemeral disk.",
    "force_delete": "Force-destroys the instance bypassing normal cleanup.",
    "shelve": "Shelves the instance, releasing compute resources. May take time to unshelve.",
}


def get_tool_input() -> tuple[str, dict]:
    """Read hook input from stdin (JSON with tool_name and tool_input)."""
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        return "", {}

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    return tool_name, tool_input


def check_nova_server_action(tool_input: dict) -> str | None:
    """Check if a nova_server_action call is destructive."""
    action = tool_input.get("action", "").lower()

    if action in DESTRUCTIVE_SERVER_ACTIONS:
        consequence = DESTRUCTIVE_SERVER_ACTIONS[action]

        # Special case: soft reboot is safe, hard reboot is destructive
        if action == "reboot":
            reboot_type = tool_input.get("type", "SOFT").upper()
            if reboot_type == "HARD":
                return "HARD reboot is equivalent to pulling the power cord. In-flight I/O is lost, filesystems may corrupt."
            return None  # SOFT reboot is safe

        return consequence

    return None


def main() -> None:
    tool_name, tool_input = get_tool_input()

    if not tool_name:
        # Can't determine tool — allow (don't break non-MCP tools)
        sys.exit(0)

    # Check if it's a destructive tool
    if tool_name == "nova_server_action":
        consequence = check_nova_server_action(tool_input)
        if consequence is None:
            sys.exit(0)  # Safe action
    elif tool_name in DESTRUCTIVE_TOOLS:
        consequence = DESTRUCTIVE_TOOLS[tool_name]
    else:
        sys.exit(0)  # Not a destructive tool — allow

    # Build the block message
    # Extract target identifier from any common ID field
    target_id = "unknown"
    for key in ("server_id", "id", "volume_id", "floatingip_id", "node_id",
                "zone_id", "event_id", "secret_id", "share_id", "loadbalancer_id",
                "container", "object", "name"):
        if key in tool_input and tool_input[key]:
            target_id = str(tool_input[key])
            break
    action_desc = tool_input.get("action", tool_name.split("_", 1)[-1] if "_" in tool_name else tool_name)

    msg = f"BLOCKED: Destructive action requires approval.\n"
    msg += f"  Tool: {tool_name}\n"
    msg += f"  Target: {target_id}\n"
    if consequence:
        msg += f"  Impact: {consequence}\n"
    msg += f"\nThe user must approve this action before it can proceed."

    print(msg, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
