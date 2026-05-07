# SAP Converged Cloud Architecture

## Regional Model

Each SAP CC region is an independent OpenStack deployment:

| Property | Scope | Implication |
|----------|-------|-------------|
| Keystone (identity) | Per-region | Separate credentials per region |
| Service catalog | Per-region | Available services may differ |
| Resources | Per-region | VMs, volumes, networks don't cross regions |
| Credentials | Per-region | App credentials valid only in creating region |
| Quota (Limes) | Per-region | Capacity tracked independently |

## Region Naming

Format: `<geo>-<country>-<number>`

| Region | Location | Notes |
|--------|----------|-------|
| `eu-de-1` | Germany | Primary EU region |
| `eu-de-2` | Germany | Secondary EU region |
| `eu-nl-1` | Netherlands | EU expansion |
| `na-us-1` | US East | North America |
| `na-us-2` | US West | North America |
| `na-us-3` | US Central | North America |
| `ap-jp-1` | Japan | Asia-Pacific |
| `ap-au-1` | Australia | Asia-Pacific |
| `qa-de-1` | Germany | QA/staging environment |

## Domain → Project Hierarchy

```
Region (eu-de-1)
├── Domain: cc-demo
│   ├── Project: demo-platform
│   ├── Project: demo-app-team
│   └── Project: demo-monitoring
├── Domain: cc-production
│   ├── Project: prod-frontend
│   ├── Project: prod-backend
│   └── Project: prod-data
└── Domain: cc-network
    ├── Project: network-mgmt
    └── Project: network-shared
```

- **Domain** = organizational unit (team, department, environment)
- **Project** = resource container (where VMs, volumes, networks live)
- **Roles** = assigned at project level (member, admin, reader)

## Service Architecture

All services authenticate through Keystone and are scoped to the current project:

```
User → Keystone (auth) → Token (project-scoped)
                           ↓
          ┌────────────────┼────────────────┐
          │                │                │
        Nova           Neutron          Cinder
      (compute)      (network)        (storage)
          │                │                │
          └────────────────┼────────────────┘
                           ↓
              SAP CC Platform Services
          ┌────────────────┼────────────────┐
          │        │       │       │        │
        Limes   Hermes   Maia   Keppel   Archer
       (quota)  (audit) (metrics)(registry)(endpoints)
```

## Multi-Tenancy Model

| Layer | Isolation |
|-------|-----------|
| Region | Complete (separate deployments) |
| Domain | Administrative (quota boundaries) |
| Project | Resource (VMs, networks, volumes) |

Cross-project visibility:
- Hermes audit events: project-scoped (you see only your actions)
- Maia metrics: project-scoped (you see only your metrics)
- Limes quota: project/domain/cluster views (different detail levels)
- Archer services: services visible cross-project (endpoints are project-scoped)
- Keppel accounts: project-scoped (but federation shares images across regions)
