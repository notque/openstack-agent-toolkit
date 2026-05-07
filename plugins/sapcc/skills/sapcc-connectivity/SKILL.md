---
name: sapcc-connectivity
description: >
  Archer endpoint service management for private network connectivity in SAP Converged Cloud.
  Triggers: endpoint service, private link, archer, private connectivity, service endpoint, internal access, cross-project access
version: 1.0.0
metadata:
  service: [archer]
  task: [discover, connect, debug]
  persona: [developer, platform-engineer]
---

# SAP CC Private Connectivity (Archer)

Archer is SAP CC's endpoint service for private network connectivity between projects. Similar to AWS PrivateLink. Not part of vanilla OpenStack. Enables consumers to access services published by other projects via a local IP address without traversing public networks.

## MCP Tools

### Read Tools
| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `archer_list_services` | List services available for endpoint creation | `status` (optional) |
| `archer_get_service` | Get service detail by UUID | `service_id` |
| `archer_list_endpoints` | List endpoints in current project | `service_id`, `status` (optional) |
| `archer_get_endpoint` | Get endpoint detail by UUID | `endpoint_id` |

## Archer Model

```
Producer (other project)                Consumer (your project)
┌─────────────────────┐                ┌─────────────────────┐
│  Network Resource    │                │  Endpoint            │
│  (DB, API, etc.)     │◄──private──────│  (local IP in YOUR   │
│                      │   connection   │   network)           │
│  Published as        │                │                      │
│  SERVICE             │                │  Created by YOU      │
└─────────────────────┘                └─────────────────────┘
```

**Producer/Consumer pattern:**
- **Service** = a network resource published by another project (the producer). You cannot create services with these tools — you consume them.
- **Endpoint** = your access point. Created in your project, provides a local IP address on your network that routes privately to the service.
- Traffic stays on the internal network fabric. No public IPs, no NAT, no firewall traversal.

## Gotchas

### 1. You create endpoints, not services

Services are published by OTHER projects (producers). Your project is a consumer. You discover available services with `archer_list_services`, then create endpoints to connect to them. If you don't see a service you expect, the producer hasn't published it yet or hasn't made it available to your project.

### 2. Endpoint status transitions matter

```
PENDING_APPROVAL → AVAILABLE    (happy path)
PENDING_APPROVAL → REJECTED     (producer denied access)
```

An endpoint is NOT usable until status is `AVAILABLE`. The local IP won't route traffic until the endpoint is fully active.

### 3. Some services require producer approval

Not all services auto-approve endpoints. The producer can configure their service to require manual approval of each consumer endpoint. If your endpoint is stuck in `PENDING_APPROVAL`, the producer must approve it — this is not something you can resolve yourself.

### 4. The endpoint IP is YOUR access point

The endpoint provides a local IP address in your network. Use that IP (or DNS pointing to it) to reach the remote service. Don't try to reach the service's original IP — the whole point is that you access it through your local endpoint IP.

### 5. List services BEFORE creating endpoints

Always call `archer_list_services` first to discover what's available. Services have UUIDs that you need for endpoint creation. Guessing service IDs will fail.

### 6. Correlate endpoint to service for full picture

An endpoint's `service_id` tells you which service it connects to. Use `archer_get_service` with that UUID to get the service details (what it is, who provides it, what network resource it exposes).

### 7. Endpoints are project-scoped

You only see your own project's endpoints with `archer_list_endpoints`. You cannot see other projects' endpoints. But `archer_list_services` shows services available to you regardless of which project published them.

## Common Workflows

### "What services can I connect to?"

```
1. archer_list_services()
2. Review available services — note name, description, service_id
3. archer_get_service(service_id) for details on a specific service
```

Filter by status to see only active services: `archer_list_services(status="AVAILABLE")`

### "What are my current connections?"

```
1. archer_list_endpoints()
2. Review each endpoint: status, service_id, IP address
3. For any with status != AVAILABLE, investigate
```

### "Get full details about a connection"

```
1. archer_get_endpoint(endpoint_id) → endpoint details including service_id
2. archer_get_service(service_id) → what service it connects to
3. Correlate: you now know your local IP and what remote resource it reaches
```

### Troubleshooting connectivity

```
1. archer_list_endpoints(service_id=<target_service>) → find your endpoint
2. Check endpoint status:
   - AVAILABLE → endpoint is fine, problem is elsewhere (DNS, security groups, application)
   - PENDING_APPROVAL → not active yet, contact producer
   - REJECTED → producer denied, contact them
   - ERROR → platform issue, escalate
3. Verify you're connecting to the endpoint's local IP, not the service's original IP
```

## Troubleshooting

### Endpoint stuck in PENDING_APPROVAL

- The service requires manual approval from the producer project
- You cannot approve it yourself
- Action: contact the team that owns the service and ask them to approve your endpoint
- Check service details with `archer_get_service` to identify the producer

### Endpoint status is REJECTED

- The producer explicitly denied your endpoint request
- Possible reasons: wrong project, policy violation, service decommissioned
- Action: contact the service producer to understand why and resolve

### Service not found in archer_list_services

- The service may not exist yet (producer hasn't published it)
- The service may not be available to your project (producer restricts visibility)
- The service may have been deleted or is in a non-AVAILABLE status
- Try without status filter to see services in all states

### Endpoint shows AVAILABLE but traffic doesn't flow

- Verify you're using the endpoint's local IP, not the service's backend IP
- Check security groups on your port/network — they still apply to endpoint traffic
- Verify the service itself is healthy (the endpoint is just the tunnel — if the backend is down, traffic won't work)

## Security

Private connectivity via Archer reduces attack surface:
- Traffic never touches public networks — no exposure to internet-based threats
- Endpoints are project-scoped — only your project can use your endpoints
- No public IPs required — the service is reachable only via private endpoint IP
- Producer controls access — services can require approval before granting connectivity
- Principle of least exposure — only the specific service is reachable, not the entire producer network
