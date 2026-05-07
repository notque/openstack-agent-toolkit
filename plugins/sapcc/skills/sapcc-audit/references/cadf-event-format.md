# CADF Event Format Reference

CADF (Cloud Auditing Data Federation) is the DMTF standard used by Hermes to structure audit events. Every action in SAP Converged Cloud generates a CADF event.

## Event Structure

```json
{
  "id": "event-uuid",
  "eventType": "activity",
  "eventTime": "2024-03-15T14:22:01.234Z",
  "action": "update",
  "outcome": "success",
  "initiator": {
    "id": "user-uuid",
    "name": "D012345",
    "typeURI": "service/security/account/user",
    "domain_id": "domain-uuid",
    "project_id": "project-uuid"
  },
  "target": {
    "id": "resource-uuid",
    "typeURI": "compute/server",
    "name": "my-server-01",
    "project_id": "project-uuid"
  },
  "observer": {
    "id": "observer-uuid",
    "typeURI": "service/compute",
    "name": "nova"
  },
  "attachments": [
    {
      "name": "payload",
      "typeURI": "mime:application/json",
      "content": "{\"server\": {\"name\": \"new-name\"}}"
    }
  ],
  "requestPath": "/v2.1/servers/resource-uuid"
}
```

## Field Definitions

### Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique event identifier. Use with `hermes_get_event`. |
| `eventType` | string | Always `activity` for API actions. |
| `eventTime` | ISO 8601 | UTC timestamp of when the action occurred. |
| `action` | string | The operation: `create`, `update`, `delete`, `read`, `authenticate`, etc. |
| `outcome` | string | `success`, `failure`, or `pending`. |
| `requestPath` | string | The API endpoint path that was called. |

### Initiator (Who)

| Field | Description |
|-------|-------------|
| `initiator.id` | Keystone user UUID |
| `initiator.name` | Human-readable username (this is what you filter on) |
| `initiator.typeURI` | Always `service/security/account/user` for human users |
| `initiator.domain_id` | Domain the user belongs to |
| `initiator.project_id` | Project scope of the action |

### Target (What Was Acted On)

| Field | Description |
|-------|-------------|
| `target.id` | UUID of the resource (server, port, volume, etc.) |
| `target.typeURI` | Resource type in slash format (see table below) |
| `target.name` | Human-readable resource name (if available) |
| `target.project_id` | Project that owns the resource |

### Observer (Which Service Recorded It)

| Field | Description |
|-------|-------------|
| `observer.id` | Service instance UUID |
| `observer.typeURI` | Service type (e.g., `service/compute`) |
| `observer.name` | Service name (e.g., `nova`, `neutron`) |

### Attachments (Request/Response Details)

| Field | Description |
|-------|-------------|
| `attachments[].name` | Typically `payload` or `request`/`response` |
| `attachments[].typeURI` | MIME type, usually `mime:application/json` |
| `attachments[].content` | JSON string of the request body or response |

Attachments are the key to answering "what exactly changed?" — they contain the API request payload showing which fields were modified and to what values.

## Common target_type Values

### Compute (Nova)

| target_type | Resource |
|-------------|----------|
| `compute/server` | Virtual machine instance |
| `compute/keypair` | SSH keypair |
| `compute/server-group` | Server anti-affinity group |
| `compute/flavor` | Instance type definition |

### Networking (Neutron)

| target_type | Resource |
|-------------|----------|
| `network/port` | Virtual network interface |
| `network/network` | Virtual network |
| `network/subnet` | IP subnet |
| `network/router` | Virtual router |
| `network/security-group` | Security group |
| `network/security-group-rule` | Individual firewall rule |
| `network/floatingip` | Floating IP address |

### Identity (Keystone)

| target_type | Resource |
|-------------|----------|
| `identity/project` | Project/tenant |
| `identity/user` | User account |
| `identity/role-assignment` | Role grant/revoke |
| `identity/application-credential` | App credential |
| `identity/OS-TRUST/trust` | Trust delegation |

### Block Storage (Cinder)

| target_type | Resource |
|-------------|----------|
| `storage/volume` | Block volume |
| `storage/snapshot` | Volume snapshot |
| `storage/backup` | Volume backup |

### DNS (Designate)

| target_type | Resource |
|-------------|----------|
| `dns/zone` | DNS zone |
| `dns/recordset` | DNS record set |

### Load Balancing (Octavia)

| target_type | Resource |
|-------------|----------|
| `load-balancer/loadbalancer` | Load balancer |
| `load-balancer/listener` | LB listener |
| `load-balancer/pool` | LB backend pool |
| `load-balancer/member` | Pool member |

### Object Storage (Swift)

| target_type | Resource |
|-------------|----------|
| `object-store/container` | Swift container |
| `object-store/object` | Stored object |

## Common action Values

| Action | Meaning |
|--------|---------|
| `create` | New resource created |
| `update` | Existing resource modified |
| `delete` | Resource removed |
| `read` | Resource details retrieved (not always tracked) |
| `authenticate` | Login/token creation |
| `start` | Server/service started |
| `stop` | Server/service stopped |
| `reboot` | Server rebooted |
| `attach` | Volume/port attached |
| `detach` | Volume/port detached |
| `resize` | Server flavor changed |
| `migrate` | Server moved to different host |

## Querying Tips

**By resource lifecycle:**
```
target_id=<uuid>, sort=time:asc → full creation-to-deletion history
```

**By user activity:**
```
initiator_name=<username>, time_gte=<start> → all actions by user in window
```

**By failure investigation:**
```
outcome=failure, target_type=compute/server → all failed compute operations
```

**By security review:**
```
action=authenticate, outcome=failure → failed login attempts
action=delete, target_type=identity/role-assignment → permission removals
```
