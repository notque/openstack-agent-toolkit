# CADF Event Format Reference

Source: [sapcc/go-api-declarations/cadf/event.go](https://github.com/sapcc/go-api-declarations/blob/main/cadf/event.go)

## Event Structure

```json
{
  "typeURI": "http://schemas.dmtf.org/cloud/audit/1.0/event",
  "id": "event-uuid",
  "eventTime": "2024-03-15T14:22:01.000000+00:00",
  "eventType": "activity",
  "action": "update",
  "outcome": "success",
  "reason": {
    "reasonType": "HTTP",
    "reasonCode": "200"
  },
  "initiator": {
    "typeURI": "service/security/account/user",
    "id": "user-keystone-uuid",
    "name": "D012345",
    "domain": "cc-demo",
    "host": {
      "address": "10.0.0.1",
      "agent": "python-openstackclient/6.0.0"
    },
    "project_id": "project-uuid",
    "domain_id": "domain-uuid"
  },
  "target": {
    "typeURI": "compute/server",
    "id": "resource-uuid",
    "name": "my-server",
    "project_id": "project-uuid",
    "domain_id": "domain-uuid"
  },
  "observer": {
    "typeURI": "service/compute",
    "id": "nova-service-uuid",
    "name": "nova"
  },
  "requestPath": "/v2.1/servers/resource-uuid",
  "attachments": [
    {
      "name": "payload",
      "typeURI": "mime:application/json",
      "content": "{\"server\": {\"name\": \"new-name\"}}"
    }
  ]
}
```

## Field Reference

### Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `typeURI` | string | Always `http://schemas.dmtf.org/cloud/audit/1.0/event` |
| `id` | string | Unique event UUID |
| `eventTime` | string | ISO 8601 timestamp (UTC) when the event occurred |
| `eventType` | string | Usually `activity` |
| `action` | Action | The operation: `create`, `update`, `delete`, `read`, `authenticate`, `start`, `stop` |
| `outcome` | Outcome | Result: `success`, `failure`, `pending` |
| `reason` | Reason | HTTP-level result (reasonType + reasonCode) |
| `initiator` | Resource | Who performed the action |
| `target` | Resource | What was acted upon |
| `observer` | Resource | Which service recorded it |
| `requestPath` | string | Original HTTP request path |
| `attachments` | []Attachment | Request/response payloads (may be empty) |

### Resource Fields (initiator, target, observer)

| Field | Type | Description |
|-------|------|-------------|
| `typeURI` | string | Resource type in slash format (e.g., `compute/server`) |
| `id` | string | UUID of the resource |
| `name` | string | Human-readable name |
| `domain` | string | Domain name (for initiator) |
| `host` | Host | Client host info (for initiator) |
| `project_id` | string | OpenStack project UUID (SAP CC extension) |
| `domain_id` | string | OpenStack domain UUID (SAP CC extension) |
| `project_name` | string | Project name (SAP CC extension) |
| `domain_name` | string | Domain name (SAP CC extension) |
| `app_credential_id` | string | If authenticated via app credential |

### Host Fields (initiator.host)

| Field | Type | Description |
|-------|------|-------------|
| `address` | string | Client IP address |
| `agent` | string | User agent string (e.g., `python-openstackclient/6.0.0`) |

### Attachment Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Attachment label (e.g., `payload`, `request`, `response`) |
| `typeURI` | string | MIME type (e.g., `mime:application/json`) |
| `content` | any | Serialized content (usually JSON string) |

## Common target_type Values

Obtained via `hermes_list_attributes(attribute="target_type")`:

| target_type | Service | Resource |
|-------------|---------|----------|
| `compute/server` | Nova | Virtual machine |
| `network/port` | Neutron | Network port |
| `network/security-group` | Neutron | Security group |
| `network/floatingip` | Neutron | Floating IP |
| `network/router` | Neutron | Router |
| `volume/volume` | Cinder | Block storage volume |
| `identity/project` | Keystone | Project |
| `identity/user` | Keystone | User account |
| `identity/credential` | Keystone | Application credential |
| `dns/zone` | Designate | DNS zone |
| `dns/recordset` | Designate | DNS record |
| `image/image` | Glance | VM image |
| `key-manager/secret` | Barbican | Secret/certificate |
| `loadbalancer/loadbalancer` | Octavia | Load balancer |
| `share/share` | Manila | File share |

## CLI Reference

For command-line audit access outside of agents: [hermescli](https://github.com/sapcc/hermescli)

```bash
# List recent events
hermescli event list --time '>=2024-03-15T00:00:00Z'

# Filter by target type
hermescli event list --target-type compute/server

# Get event detail
hermescli event show <event-uuid>
```
