---
name: sapcc-identity
description: >-
  SAP Converged Cloud identity and access management via Keystone. Domain/project
  hierarchy, authentication context, application credentials, role assignments,
  and service catalog interpretation. Use when: project, domain, authentication,
  roles, token, application credential, keystone, who am I, service catalog.
version: 1.0.0
metadata:
  service: [keystone]
  task: [auth, debug, manage, discover]
  persona: [developer, platform-engineer, security]
allowed-tools: [Read]
---

# SAP CC Identity (Keystone)

## MCP Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `keystone_token_info` | Current auth context: user, project, domain, roles, catalog | None |
| `keystone_list_projects` | List accessible projects | `domain_id`, `name` (optional filters) |
| `keystone_create_application_credential` | Create app credential (secret shown once) | `name`, `description`, `expires_at`, `roles` |
| `keystone_list_application_credentials` | List app creds for current user | None |
| `keystone_delete_application_credential` | Delete/revoke an app credential | `id` or `name` |

## SAP CC Domain Model

```
Region (eu-de-1)
└── Domain (organizational unit, e.g. "cc-demo")
    ├── Project A (resource container)
    │   └── Role assignments (member, admin, network_admin...)
    ├── Project B
    └── Project C
```

**Key facts:**
- A domain is an organizational boundary (typically maps to a team or cost center)
- Each project belongs to exactly one domain
- Roles are assigned per-project (a user can be admin in Project A, member in Project B)
- Regions are fully independent — credentials, projects, and catalogs don't cross regions
- Domain names follow convention: `cc-<name>` (e.g., `cc-demo`, `cc-platform`)

For deeper explanation, see `references/domain-project-model.md`.

## Gotchas

1. **token_info never exposes the actual token value** — only metadata (user, project, roles, catalog). This is security by design in the MCP server. Don't tell users you can show them their token.

2. **App credential secret is shown ONLY at creation time** — if the user loses it, the only recovery is delete + recreate. Always instruct users to store the secret immediately (keychain).

3. **App credentials inherit roles at creation time** — role changes to the user after creation do NOT affect existing app credentials. To pick up new roles: delete old credential, create new one.

4. **Always list existing app credentials before creating** — avoids duplicates. Use `keystone_list_application_credentials` first, check if one with the intended name already exists.

5. **App credential names are unique per user, not globally** — two different users can have an app credential named `mcp-server`. But the same user cannot have two with the same name.

6. **Deleting an app credential immediately revokes access** — any service (including the MCP server itself) using that credential will fail on the next API call. Always create the replacement first.

7. **domain_id is required for cross-domain project listing** — without it, `keystone_list_projects` only returns projects in your token's current domain scope.

8. **Service catalog in token_info is region-specific** — it shows only services available in the current region. Different regions may have different service availability.

9. **App credentials cannot create other app credentials** — unless created with `unrestricted: true` (which most deployments disallow). This prevents credential escalation chains.

10. **Project scope determines what you see** — your token is scoped to one project. All API calls operate within that project's context. To work across projects, you need separate credentials per project.

## Common Workflows

### Check Current Auth Context

"Who am I? What project? What can I do?"

```
1. keystone_token_info
   → Returns: user name, user domain, project name, project domain,
     role assignments, service catalog, token expiry
2. Interpret roles to determine access level
3. Review service catalog to see available services
```

### Create Application Credential for MCP Server

```
1. keystone_list_application_credentials
   → Check if one already exists with intended name
2. keystone_create_application_credential
   name: "mcp-server-<project>-<region>"  (e.g., mcp-server-cc-demo-qa-de-1)
   description: "MCP server credential for <project> in <region>"
   expires_at: "2027-05-06T00:00:00Z"  (recommend 1 year dev, 90 days prod)
3. IMMEDIATELY store the secret in keychain:
   macOS:  security add-generic-password -a "<name>" -s "openstack-appcred" -w "<secret>"
   Linux:  secret-tool store --label="<name>" service openstack-appcred account "<name>"
4. Configure MCP server with credential ID + secret retrieval command
5. Verify with keystone_token_info after restart
```

### Rotate Credentials

Order matters — create new BEFORE deleting old:

```
1. keystone_list_application_credentials → identify the old credential
2. keystone_create_application_credential → new credential with new name/suffix
3. Store new secret in keychain
4. Update MCP server config to use new credential
5. Restart MCP server
6. keystone_token_info → verify new credential works
7. keystone_delete_application_credential → remove old credential ONLY after verification
8. Remove old secret from keychain
```

### List Accessible Projects

```
1. keystone_list_projects
   → Shows projects in current domain
2. For cross-domain: keystone_list_projects with domain_id filter
   → Need to know the target domain_id (not name)
3. Cross-reference with keystone_token_info to see current project scope
```

### Discover Available Services

```
1. keystone_token_info → service_catalog section
2. Each catalog entry contains:
   - type (e.g., "compute", "resources", "audit-data")
   - name (e.g., "nova", "limes", "hermes")
   - endpoints with region and URL
3. Use catalog to determine which MCP tools are usable in current region
```

## Troubleshooting

### "Authentication failed" or 401 errors

| Cause | Diagnostic | Fix |
|-------|-----------|-----|
| App credential deleted/expired | `keystone_list_application_credentials` — is it still there? | Create new credential |
| Wrong project scope | `keystone_token_info` — check project name | Update `OS_PROJECT_NAME` or recreate credential |
| User account disabled | Login to dashboard — is account active? | Contact domain admin |
| Wrong region | Check `OS_AUTH_URL` matches `OS_REGION_NAME` | Fix auth URL |

### "Insufficient permissions" or 403 errors

| Cause | Diagnostic | Fix |
|-------|-----------|-----|
| Missing role | `keystone_token_info` → check roles list | Request role from project admin |
| App credential has subset of roles | List app cred → check roles field | Delete and recreate with needed roles |
| Wrong project | `keystone_token_info` → check project | Switch to correct project |

### "Project not found"

- Verify domain scope — cross-domain listing requires `domain_id`
- Check spelling: project names are case-sensitive
- Confirm the project exists in this region (regions are independent)

### "App credential name already exists"

- Names are unique per user — list existing creds to find the conflict
- Delete the old one (if no longer needed) or choose a different name

## Security

| Principle | Implementation |
|-----------|---------------|
| Never expose tokens | MCP server sanitizes all responses — token values never reach the LLM |
| App creds over passwords | Scoped, revocable, no password exposure — always prefer |
| Keychain storage | Use `OS_APPCRED_SECRET_CMD` pattern — never plaintext in config files |
| Set expiration | Forces periodic rotation, limits blast radius of compromised creds |
| Minimum roles | Create app credentials with only the roles needed for the task |
| One credential per purpose | Easy to revoke without disrupting other services |
| Verify before deleting | Always confirm new credential works before revoking the old one |

## Cross-Service References

- **credential-setup skill** — detailed guided workflow for first-time credential creation
- **sapcc-quota** — check `limes_get_project_quota` to see what resources your project can use
- **sapcc-audit** — use `hermes_list_events` with `initiator_name` to see who did what in a project
- **Service catalog** — determines which other MCP tools (nova_, neutron_, limes_, etc.) are available
