---
name: sapcc-dns
description: >
  DNS zone and recordset management via Designate in SAP Converged Cloud.
  Triggers: dns, zone, recordset, designate, domain, A record, CNAME, MX, TXT, nameserver
version: 1.0.0
metadata:
  service: [designate]
  task: [manage, inspect, debug]
  persona: [developer, platform-engineer]
---

# SAP CC DNS (Designate)

Manage DNS zones and recordsets: list zones, inspect zone details, and query recordsets. Designate is OpenStack's multi-tenant DNS-as-a-Service.

## MCP Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `designate_list_zones` | List DNS zones in current project | `name`, `status`, `type` (returns: ID, name, email, TTL, status, type, serial, created_at) |
| `designate_get_zone` | Full detail for a single zone | `zone_id` (UUID) |
| `designate_list_recordsets` | List recordsets in a zone | `zone_id` (required), `name`, `type`, `status`, `data` |

## Gotchas

### 1. Zones are project-scoped — you cannot see other projects' zones

Each project manages its own DNS zones. If you expect to see a zone but don't, verify you're authenticated to the correct project with `keystone_token_info`.

### 2. Zone names MUST end with a dot

DNS convention requires fully qualified domain names (FQDNs) to end with a trailing dot. `example.com.` is correct; `example.com` may not match filters. The API returns names with trailing dots.

### 3. Recordsets require a zone_id — you cannot list all recordsets globally

You must first identify the zone, then list its recordsets. Workflow: `designate_list_zones` → pick zone → `designate_list_recordsets(zone_id=...)`.

### 4. Status transitions: PENDING → ACTIVE

After creation or modification, zones and recordsets go through `PENDING` status before becoming `ACTIVE`. A `PENDING` record is not yet propagated to DNS servers.

### 5. Recordset types matter for filtering

Common types: `A` (IPv4), `AAAA` (IPv6), `CNAME` (alias), `MX` (mail), `TXT` (arbitrary text, SPF, DKIM), `SRV` (service locator), `NS` (nameserver delegation).

### 6. The `data` filter searches record values

Use `data` to find records pointing to a specific IP or target. For example, `data=10.0.1.5` finds all A records pointing to that IP. Useful for "what DNS names point to this server?"

### 7. TTL controls cache duration

TTL (Time To Live) in seconds controls how long resolvers cache the record. Low TTL (60-300s) = faster propagation of changes. High TTL (3600-86400s) = less DNS traffic but slower updates. Zone-level TTL is the default; recordset-level TTL overrides it.

### 8. Zone type PRIMARY vs SECONDARY

`PRIMARY` zones are authoritative — you manage records directly. `SECONDARY` zones are replicas of an external primary — records are read-only copies. Most user zones are PRIMARY.

## Common Workflows

### Discover DNS Zones in Project

```
1. designate_list_zones()
2. Review zones — note name, status, type
3. designate_get_zone(zone_id) for full detail
```

### Find All Records in a Zone

```
1. designate_list_zones() → identify target zone
2. designate_list_recordsets(zone_id=<uuid>)
3. Scan results for A, CNAME, MX, TXT records
```

### "What DNS points to this IP?"

```
1. designate_list_zones() → get all zones
2. For each zone: designate_list_recordsets(zone_id=<id>, data=<ip_address>)
3. Matches show which names resolve to that IP
```

### Verify DNS Configuration for a Service

```
1. designate_list_zones(name=<expected_domain.>) → find the zone
2. designate_list_recordsets(zone_id=<id>, name=<fqdn.>) → find specific record
3. Check: correct type, correct data, status=ACTIVE
```

## Troubleshooting

### Zone not found

- Verify zone name includes trailing dot: `example.com.`
- Check you're in the correct project: `keystone_token_info`
- Zone may be in another project — DNS is project-scoped

### Recordset status is PENDING for > 5 minutes

- May indicate a backend issue — check Hermes audit trail
- `hermes_list_events(target_type=dns/recordset, outcome=failure)`

### DNS not resolving despite ACTIVE status

- Check TTL — old cached value may not have expired at resolver
- Verify the zone's NS records point to correct nameservers
- Ensure the zone itself is ACTIVE (not just the recordset)

## Security Considerations

- DNS records reveal infrastructure topology (server IPs, service names)
- TXT records may contain verification tokens, SPF policies, or DKIM keys
- MX records expose mail server infrastructure
- Treat zone data as internal — it maps your service architecture

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Server at an IP address | Nova | `nova_list_servers(ip=<address>)` |
| Who modified DNS records | Hermes | `hermes_list_events(target_type=dns/recordset)` |
| Load balancer VIP in DNS | Octavia | `octavia_get_loadbalancer` → check VIP address |
| Network for a DNS-referenced IP | Neutron | `neutron_list_ports` |
