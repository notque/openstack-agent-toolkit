# SAP Converged Cloud Services Reference

## Standard OpenStack Services

| Service | Project | API Version | MCP Tool Prefix |
|---------|---------|-------------|-----------------|
| Compute | Nova | v2.1 | `nova_` |
| Networking | Neutron | v2.0 | `neutron_` |
| Block Storage | Cinder | v3 | `cinder_` |
| Identity | Keystone | v3 | `keystone_` |
| Object Storage | Swift | v1 | - |
| DNS | Designate | v2 | - |
| Load Balancing | Octavia | v2 | - |

## SAP CC-Specific Services

| Service | Project | Catalog Type | MCP Tool Prefix | Purpose |
|---------|---------|--------------|-----------------|---------|
| Audit | Hermes | `audit-data` | `hermes_` | CADF audit events for all service actions |
| Quota/Usage | Limes | `resources` | `limes_` | Project/domain/cluster resource quotas |
| Registry | Keppel | `keppel` | `keppel_` | Multi-tenant container image registry |
| Endpoint Service | Archer | `endpoint-services` | `archer_` | Private network connectivity (like AWS PrivateLink) |
| Metrics | Maia | `metrics` | `maia_` | Multi-tenant Prometheus-compatible metrics |

## Common Operations by Role

### Platform Engineer
- Check quota usage: `limes_get_project_quota`
- Review audit trail: `hermes_list_events`
- Monitor metrics: `maia_query` with PromQL
- Manage endpoints: `archer_list_services`, `archer_list_endpoints`

### Developer
- List servers: `nova_list_servers`
- Check networking: `neutron_list_networks`, `neutron_list_ports`
- View container images: `keppel_list_repositories`
- Check storage: `cinder_list_volumes`

### Security/Compliance
- Audit events: `hermes_list_events` with time/action/outcome filters
- Token info: `keystone_token_info` to see current roles
- Project access: `keystone_list_projects`

## Authentication

### Recommended: Application Credentials
```
OS_AUTH_URL + OS_APPLICATION_CREDENTIAL_ID + OS_APPCRED_SECRET_CMD
```

### Alternative: Password with Keychain
```
OS_AUTH_URL + OS_USERNAME + OS_PW_CMD + OS_USER_DOMAIN_NAME + OS_PROJECT_NAME + OS_PROJECT_DOMAIN_NAME
```

## Regional Architecture

Each SAP CC region is an independent OpenStack deployment:
- Separate Keystone (identity)
- Separate service catalog
- Separate credentials required
- Region naming: `<geo>-<country>-<number>` (e.g., `eu-de-1`, `qa-de-1`, `na-us-1`)
