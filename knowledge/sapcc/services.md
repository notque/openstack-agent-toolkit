# SAP Converged Cloud Services Reference

## Standard OpenStack Services

| Service | Project | API Version | MCP Tool Prefix |
|---------|---------|-------------|-----------------|
| Compute | Nova | v2.1 | `nova_` |
| Networking | Neutron | v2.0 | `neutron_` |
| Block Storage | Cinder | v3 | `cinder_` |
| Identity | Keystone | v3 | `keystone_` |
| Object Storage | Swift | v1 | `swift_` |
| DNS | Designate | v2 | `designate_` |
| Load Balancing | Octavia | v2 | `octavia_` |
| Image | Glance | v2 | `glance_` |
| Key Manager | Barbican | v1 | `barbican_` |
| Shared File Systems | Manila | v2 | `manila_` |
| Bare Metal | Ironic | v1 | `ironic_` |

## SAP CC-Specific Services

| Service | Project | Catalog Type | MCP Tool Prefix | Purpose |
|---------|---------|--------------|-----------------|---------|
| Audit | Hermes | `audit-data` | `hermes_` | CADF audit events for all service actions |
| Quota/Usage | Limes | `resources` | `limes_` | Project/domain/cluster resource quotas |
| Registry | Keppel | `keppel` | `keppel_` | Multi-tenant container image registry |
| Endpoint Service | Archer | `endpoint-services` | `archer_` | Private network connectivity (like AWS PrivateLink) |
| Metrics | Maia | `metrics` | `maia_` | Multi-tenant Prometheus-compatible metrics |
| Autoscaling | Castellum | `castellum` | `castellum_` | Resource autoscaling policies |
| Email | Cronus | `email-aws` | `cronus_` | Email notification service |

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

## Related CLI Tools

| Service | CLI | Repository |
|---------|-----|------------|
| Hermes (Audit) | hermescli | [sapcc/hermescli](https://github.com/sapcc/hermescli) |
| Limes (Quota) | limesctl | [sapcc/limesctl](https://github.com/sapcc/limesctl) |
| All OpenStack | openstackclient | [openstack/python-openstackclient](https://github.com/openstack/python-openstackclient) |

## API Type Declarations

Canonical Go structs for SAP CC APIs: [sapcc/go-api-declarations](https://github.com/sapcc/go-api-declarations)

| Package | Covers |
|---------|--------|
| `cadf` | CADF audit event format (Hermes) |
| `limes` | Quota/usage resource models |
| `castellum` | Autoscaling resource declarations |
| `liquid` | Resource capacity protocol |

## OpenStack API References

| Service | API Docs |
|---------|----------|
| Nova | https://docs.openstack.org/api-ref/compute/ |
| Neutron | https://docs.openstack.org/api-ref/network/ |
| Cinder | https://docs.openstack.org/api-ref/block-storage/ |
| Keystone | https://docs.openstack.org/api-ref/identity/ |
| Glance | https://docs.openstack.org/api-ref/image/ |
| Designate | https://docs.openstack.org/api-ref/dns/ |
| Octavia | https://docs.openstack.org/api-ref/load-balancer/ |
| Barbican | https://docs.openstack.org/api-ref/key-manager/ |
| Manila | https://docs.openstack.org/api-ref/shared-file-system/ |
| Ironic | https://docs.openstack.org/api-ref/baremetal/ |
| Swift | https://docs.openstack.org/api-ref/object-store/ |
