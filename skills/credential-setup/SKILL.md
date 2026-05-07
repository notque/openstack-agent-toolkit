# Credential Setup

Guided workflow for creating and securely storing OpenStack application credentials for use with the MCP server.

## What It Does

1. Creates an application credential scoped to the user's current project and roles
2. Stores the secret securely in the system keychain (macOS Keychain / Linux secret-tool)
3. Outputs the exact MCP server configuration to use

## When to Use

- First-time MCP server setup (replaces password-based auth)
- Rotating credentials (create new, update config, delete old)
- Setting up credentials for a new project scope

## Workflow

### Phase 1: Assess Current Auth

Check what authentication method is currently configured:
- If already using application credentials → offer rotation
- If using password → recommend migration to app credentials

### Phase 2: Create Application Credential

Use the `keystone_create_application_credential` MCP tool with:
- **name**: `mcp-server-<project>-<region>` naming convention
- **description**: Include purpose, creation date, and scope
- **expires_at**: Recommend 1 year for development, 90 days for production
- **roles**: Use minimum required roles (avoid admin unless needed)

### Phase 3: Store Secret Securely

Save the secret to the system keychain:

**macOS:**
```bash
security add-generic-password -a "<credential-name>" -s "openstack-appcred" -w "<secret>"
```

**Linux (GNOME Keyring):**
```bash
secret-tool store --label="OpenStack App Credential" service openstack-appcred account "<credential-name>"
```

### Phase 4: Update MCP Server Configuration

Generate the Claude Code settings configuration:

```json
{
  "mcpServers": {
    "openstack": {
      "command": "/path/to/openstack-mcp-server",
      "env": {
        "OS_AUTH_URL": "https://identity-3.<region>.cloud.sap/v3",
        "OS_APPLICATION_CREDENTIAL_ID": "<credential-id>",
        "OS_APPCRED_SECRET_CMD": "security find-generic-password -a <credential-name> -s openstack-appcred -w",
        "OS_REGION_NAME": "<region>"
      }
    }
  }
}
```

### Phase 5: Verify

1. Restart Claude Code (to reload MCP server)
2. Test with `keystone_token_info` to confirm authentication works
3. If rotating: delete the old credential with `keystone_delete_application_credential`

## Best Practices

| Practice | Rationale |
|----------|-----------|
| One credential per purpose | Easy to revoke without affecting other services |
| Descriptive names | `mcp-server-cc-demo-qa-de-1` not `my-cred` |
| Set expiration | Force periodic rotation, limit blast radius |
| Minimum roles | Don't use admin roles for read-only MCP server access |
| Keychain storage | Never store secrets in plain text files |
| Test before deleting old | Verify new credential works before revoking old one |

## Naming Convention

```
mcp-server-<project_name>-<region>
```

Examples:
- `mcp-server-cc-demo-qa-de-1`
- `mcp-server-platform-eu-de-2`
- `mcp-server-network-na-us-1`
