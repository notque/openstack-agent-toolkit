---
name: sapcc-dns
description: >
  DNS zone and recordset operations via Designate. Triggers: dns, zone,
  recordset, domain, designate. NOT for: network ports, floating IPs (use
  sapcc-networking).
version: 1.0.0
metadata:
  service: [designate]
  task: [manage, inspect, debug]
  persona: [developer, platform-engineer]
---

# SAP CC DNS (Designate)

Manage DNS zones and recordsets: list zones, inspect zone details, query recordsets by type.

## MCP Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `designate_list_zones` | List DNS zones with optional filters | `name`, `status` (ACTIVE, PENDING, ERROR), `type` (PRIMARY, SECONDARY) |
| `designate_get_zone` | Full detail for a single zone | `zone_id` (UUID, required) |
| `designate_list_recordsets` | List recordsets within a zone | `zone_id` (UUID, required), `name`, `type` (A, AAAA, CNAME, MX, TXT, etc.), `status` |

## Gotchas

1. **Zone names are FQDN with trailing dot.** Designate stores zone names like `example.com.` (note the trailing dot). When filtering by `name`, include the trailing dot or you will get zero results.

2. **zone_id is required for recordsets.** You cannot list recordsets globally — you must first identify the zone UUID, then query recordsets within it. Always call `designate_list_zones` first if you only know the domain name.

3. **Status PENDING means propagation in progress.** A zone or recordset in PENDING status has been accepted but is not yet live on nameservers. Do not treat PENDING as an error — wait and re-check.

4. **Recordset type must be uppercase.** The `type` filter expects uppercase values like `A`, `CNAME`, `MX`. Lowercase values will return no results without an error.

5. **Multiple records per recordset.** A single recordset (e.g., type A) can contain multiple IP addresses in the `records` array. This is normal for round-robin DNS.

6. **SOA and NS recordsets are auto-managed.** Every zone has system-created SOA and NS recordsets. These cannot be modified and should be ignored when auditing user-created records.

7. **Serial number increments on every change.** The zone `serial` field is useful for verifying whether a recent change has been applied — compare before and after values.

## Common Workflows

### Find All Records for a Domain

1. `designate_list_zones` with `name=example.com.` — get the zone UUID.
2. `designate_list_recordsets` with `zone_id=<uuid>` — retrieve all recordsets.
3. Filter results by `type` if you only need specific record types (A, CNAME, etc.).

### Diagnose DNS Resolution Failure

1. `designate_list_zones` with `name=<domain.>` — confirm the zone exists and status is ACTIVE.
2. `designate_list_recordsets` with `zone_id=<uuid>` and `name=<fqdn.>` — check if the expected recordset exists.
3. If status is ERROR or PENDING, the issue is on the Designate side. If ACTIVE but resolution fails, the issue is downstream (caching, client config).

### Audit Zone Health

1. `designate_list_zones` with `status=ERROR` — find zones in error state.
2. For each error zone, `designate_get_zone` to inspect details and timestamps.
3. Cross-reference with `hermes_list_events` for the triggering action.

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Who modified a zone/recordset | Hermes | `hermes_list_events(target_type=zone)` |
| DNS quota for the project | Limes | `limes_get_project_quota(service=dns)` |
| Floating IP that should have a DNS record | Neutron | `neutron_list_floating_ips` |
| Server associated with an A record IP | Nova | `nova_list_servers` + filter by IP |
