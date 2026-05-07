# SAP Converged Cloud Domain-Project Model

## Hierarchy

```
SAP Converged Cloud
├── Region: eu-de-1 (independent OpenStack deployment)
│   ├── Domain: cc-demo
│   │   ├── Project: demo-app-dev
│   │   ├── Project: demo-app-staging
│   │   └── Project: demo-app-prod
│   ├── Domain: cc-platform
│   │   ├── Project: platform-monitoring
│   │   └── Project: platform-shared
│   └── Domain: cc-network
│       └── Project: network-infra
├── Region: eu-de-2 (completely separate)
│   ├── Domain: cc-demo  (same name, different instance)
│   │   └── ...
│   └── ...
└── Region: na-us-1
    └── ...
```

## Concepts

### Region

An independent OpenStack deployment. Each region has:
- Its own Keystone (identity service)
- Its own service catalog
- Its own set of credentials
- No resource sharing across regions

Region naming: `<geo>-<country>-<number>` (e.g., `eu-de-1`, `na-us-1`, `ap-jp-1`)

### Domain

An organizational unit within a region. Typically maps to:
- A team (e.g., `cc-platform`)
- A business unit (e.g., `cc-finance`)
- An environment grouping (e.g., `cc-demo`)

Domain properties:
- Contains one or more projects
- Has domain-level quota (cap on sum of project quotas, via Limes)
- Users can be members of multiple domains
- Domain admins manage projects and role assignments within their domain

Naming convention: `cc-<name>` (the `cc-` prefix is SAP CC convention, not enforced by Keystone)

### Project

The fundamental resource container. All OpenStack resources (servers, networks, volumes) belong to a project.

Project properties:
- Belongs to exactly one domain
- Has its own quota allocation (from domain's quota pool, managed by Limes)
- Role assignments are per-project
- Isolated from other projects (network, compute, storage)

### Roles

Roles determine what actions a user can perform within a project scope.

Common SAP CC roles:
| Role | Typical Permissions |
|------|-------------------|
| `admin` | Full control over project resources |
| `member` | Create/manage own resources |
| `reader` | Read-only access to project resources |
| `network_admin` | Manage networks, subnets, security groups |
| `compute_admin` | Manage servers, flavors (project-scoped) |
| `audit_viewer` | Read audit events (Hermes) |

Key behaviors:
- Roles are additive (a user can have multiple roles)
- Roles are project-scoped (admin in Project A does not mean admin in Project B)
- App credentials inherit the creating user's roles at creation time
- Domain admin is a separate concept from project admin

## Authentication Scoping

When you authenticate to SAP CC, your token is scoped to:
- One user
- One project (and by extension, one domain)
- A set of roles (for that project)

This means:
- All API calls operate in the context of that one project
- You cannot "switch projects" without re-authenticating (or using a different credential)
- For multi-project workflows, you need one app credential per project

## Relationship to MCP Server

The MCP server authenticates with a single set of credentials, which means:
- It operates in one project at a time
- `keystone_token_info` shows the current scope
- `keystone_list_projects` can show other projects you have access to
- To work in a different project, you need a different MCP server instance (or reconfigure)

## Common Patterns

### Multi-Project Access

```
MCP Server Instance 1: OS_PROJECT_NAME=demo-app-dev
MCP Server Instance 2: OS_PROJECT_NAME=demo-app-prod
```

Or use one credential and know you're scoped to one project.

### Cross-Domain Discovery

To list projects in another domain:
```
keystone_list_projects(domain_id="<target-domain-id>")
```

Note: requires the domain ID (UUID), not the domain name. The domain ID can be found in `keystone_token_info` for your own domain.

### Credential Per Environment

Recommended naming:
```
mcp-server-<project>-<region>
```

Examples:
- `mcp-server-demo-app-dev-eu-de-1`
- `mcp-server-platform-monitoring-na-us-1`
