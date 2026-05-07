# Cross-Service Troubleshooting Flows

## "Why can't I reach my server?"

```
Step 1: nova_get_server → Is status ACTIVE?
  ├── No (SHUTOFF/ERROR) → Server isn't running. Start it or check ERROR cause.
  └── Yes → Continue

Step 2: neutron_list_ports (device_id=server_id) → Port status?
  ├── No ports → Server has no network interface. Problem is at creation level.
  ├── DOWN → VM is off or port is not bound.
  └── ACTIVE → Continue

Step 3: Check port's security_groups → neutron_list_security_groups
  ├── No rules allowing your traffic → Add ingress rule for your port/protocol
  └── Rules exist → Continue

Step 4: Check if IP is correct
  └── Port fixed_ips[].ip_address matches what you're connecting to?
      ├── No → Wrong IP. Use the one from the port.
      └── Yes → Issue is outside OpenStack (DNS, routing, client firewall)
```

## "Who changed this resource?"

```
Step 1: Identify the resource
  └── Get target_type + target_id
      Examples: compute/server + UUID, network/port + UUID

Step 2: hermes_list_events (target_type, target_id, sort=time:desc)
  ├── Events found → Read initiator_name, action, outcome, time
  └── No events → Widen time range or check target_type format (uses slashes)

Step 3: For full detail → hermes_get_event (event_id)
  └── Shows request/response attachments — what exactly was sent
```

## "Am I running out of resources?"

```
Step 1: keystone_token_info → Get project_id and domain_id

Step 2: limes_get_project_quota (domain_id, project_id)
  └── For each service/resource:
      Calculate: usage / quota × 100 = utilization %

Step 3: Alert thresholds
  ├── > 90% → Critical: will hit limit soon
  ├── > 80% → Warning: plan capacity increase
  └── < 80% → Healthy

Step 4: If physical_usage > usage → Normal (snapshots/replicas)
         If burst_usage > 0 → Temporary over-quota (will need to reduce)
```

## "What's happening with my server?"

```
Step 1: nova_get_server → Status, task_state, host_id

Step 2: hermes_list_events (target_type=compute/server, target_id=UUID, sort=time:desc)
  └── Recent actions and their outcomes

Step 3: maia_query → Performance metrics
  └── CPU: rate(vm_cpu_seconds_total[5m])
  └── Memory: vm_memory_usage_bytes

Step 4: neutron_list_ports (device_id=server_id) → Network state

Step 5: cinder_list_volumes (filter by server in attachments) → Storage state
```

## "Debug a failed operation"

```
Step 1: hermes_list_events (outcome=failure, time_gte=<when it happened>)
  └── Find the failed event

Step 2: hermes_get_event (event_id)
  └── Read the response attachment for error details

Step 3: Common failure reasons:
  ├── 403 → Wrong project scope or insufficient roles
  ├── 409 → Conflict (resource in wrong state, quota exceeded)
  ├── 404 → Resource doesn't exist in this project
  └── 500 → Backend error (retry or escalate)
```

## Cross-Service Correlation Table

| Starting Point | Need to Know | Use |
|---------------|--------------|-----|
| Server UUID | Network interfaces | `neutron_list_ports(device_id=UUID)` |
| Server UUID | Attached volumes | `cinder_list_volumes` → filter attachments |
| Server UUID | What happened to it | `hermes_list_events(target_type=compute/server, target_id=UUID)` |
| Server UUID | Performance metrics | `maia_query` with instance label |
| Port UUID | Which server | Port's `device_id` field → `nova_get_server` |
| Network UUID | Subnets in it | `neutron_list_subnets(network_id=UUID)` |
| Network UUID | All ports | `neutron_list_ports(network_id=UUID)` |
| Volume UUID | Which server | Volume's `attachments[].server_id` |
| Any resource | Quota impact | `limes_get_project_quota(service=<svc>)` |
| Any resource | Audit trail | `hermes_list_events(target_type=<type>, target_id=UUID)` |
