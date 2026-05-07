---
name: credential-setup
description: |
  Create and securely store OpenStack application credentials for MCP server authentication.
  Triggers: setup credentials, configure auth, application credential, MCP server setup,
  first time setup, rotate credentials
version: 1.0.0
allowed-tools:
  - Read
  - Write
  - Bash
  - mcp__sapcc__keystone_token_info
  - mcp__sapcc__keystone_create_application_credential
  - mcp__sapcc__keystone_list_application_credentials
  - mcp__sapcc__keystone_delete_application_credential
---

# Credential Setup

Create, store, and configure OpenStack application credentials for MCP server authentication. Handles first-time setup, rotation, and multi-project configurations.

## MCP Tools

| Tool | Purpose |
|------|---------|
| `keystone_token_info` | Check current auth context (project, roles, expiry) |
| `keystone_create_application_credential` | Create app credential (secret shown ONCE) |
| `keystone_list_application_credentials` | List existing credentials for current user/project |
| `keystone_delete_application_credential` | Delete/revoke a credential by ID or name |

## Gotchas

These will save you from the most common failures:

1. **Secret shown ONLY ONCE at creation.** The API returns the secret exactly once in the creation response. If you don't capture it immediately, it's gone forever. You must create a new credential.

2. **Always list existing credentials first.** Call `keystone_list_application_credentials` before creating. Duplicates cause confusion during rotation and waste the 25-credential limit per user.

3. **Roles are frozen at creation time.** The credential inherits whatever roles the user has at the moment of creation. If roles are added/removed later, the credential is unaffected. To pick up new roles, create a new credential.

4. **Naming convention is load-bearing.** Use `mcp-server-{project}-{region}` (e.g., `mcp-server-cc-demo-eu-de-1`). The keychain lookup command embeds this name — inconsistent naming breaks secret retrieval.

5. **Deletion is immediate revocation.** The instant you delete a credential, any process using it loses access. Always verify the replacement works BEFORE deleting the old one.

6. **Set expiration to force rotation.** Recommended: 1 year for development, 90 days for production. Credentials without expiry become forgotten attack surface.

7. **App credentials cannot create other app credentials.** This is an intentional anti-escalation design. The MCP server authenticated via app credential cannot mint new credentials — only a user-scoped token can.

## Workflow

### Phase 1: Assess Current Auth

Call `keystone_token_info` to determine:
- Current project scope (name, ID, domain)
- Active roles
- Auth method in use (password, token, or application_credential)
- Token expiry

If already using app credentials, determine whether this is rotation or new setup.

### Phase 2: Check Existing Credentials

Call `keystone_list_application_credentials` and inspect results:
- Look for credentials matching `mcp-server-*` naming pattern
- Check expiration dates — expired ones can be cleaned up
- Identify if a credential already exists for this project+region

If a valid credential exists and user wants fresh setup, proceed to rotation flow (create new first, then delete old in Phase 7).

### Phase 3: Create Application Credential

Call `keystone_create_application_credential` with:

```
name: mcp-server-{project_name}-{region}
description: "MCP server credential for {project_name} in {region}. Created {YYYY-MM-DD}."
expires_at: {calculated expiry}  # ISO 8601 format
roles: [{minimal required roles}]  # omit to inherit all current roles
```

**IMMEDIATELY capture the `id` and `secret` from the response.** The secret will not be retrievable again.

### Phase 4: Store Secret in System Keychain

**macOS:**
```bash
security add-generic-password -a "mcp-server-{project}-{region}" -s "openstack-appcred" -w "{secret}"
```

**Linux (GNOME Keyring / libsecret):**
```bash
secret-tool store --label="OpenStack App Credential" service openstack-appcred account "mcp-server-{project}-{region}"
```
(Prompts for the secret value via stdin)

**Verify storage immediately:**
```bash
# macOS
security find-generic-password -a "mcp-server-{project}-{region}" -s "openstack-appcred" -w

# Linux
secret-tool lookup service openstack-appcred account "mcp-server-{project}-{region}"
```

### Phase 5: Generate MCP Server Configuration

Output the configuration block for Claude Code settings (`~/.claude/settings.json` or project `.claude/settings.json`):

```json
{
  "mcpServers": {
    "sapcc": {
      "command": "openstack-mcp-server",
      "env": {
        "OS_AUTH_URL": "https://identity-3.{region}.cloud.sap/v3",
        "OS_APPLICATION_CREDENTIAL_ID": "{id}",
        "OS_APPCRED_SECRET_CMD": "security find-generic-password -a mcp-server-{project}-{region} -s openstack-appcred -w",
        "OS_REGION_NAME": "{region}"
      }
    }
  }
}
```

For Linux, replace `OS_APPCRED_SECRET_CMD` value with:
```
secret-tool lookup service openstack-appcred account mcp-server-{project}-{region}
```

### Phase 6: Verify

1. Restart Claude Code (MCP servers reload on restart)
2. Call `keystone_token_info` — confirm it returns valid auth context
3. Verify project scope and roles match expectations

If verification fails, check:
- Credential ID matches (copy-paste errors)
- Secret retrieval command works standalone in terminal
- Auth URL region matches the credential's project region

### Phase 7: Clean Up (Rotation Only)

Only after Phase 6 succeeds:
1. Identify old credential ID from Phase 2 listing
2. Call `keystone_delete_application_credential` with old credential ID
3. Remove old keychain entry:
   ```bash
   # macOS
   security delete-generic-password -a "old-credential-name" -s "openstack-appcred"
   ```

## Best Practices

| Practice | Rationale |
|----------|-----------|
| One credential per purpose | Revoke one without affecting others |
| Descriptive names (`mcp-server-{project}-{region}`) | Keychain lookup depends on exact name |
| Set expiration | Forces rotation, limits blast radius of leaked creds |
| Minimum roles | Don't grant admin for read-only MCP access |
| Keychain storage | Never store in env files, dotfiles, or git |
| Test before delete | Verify new cred works before revoking old |
| Document creation date in description | Know when rotation is overdue |

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| "Authentication required" after setup | Secret retrieval command fails | Run `OS_APPCRED_SECRET_CMD` manually in terminal; check keychain entry name matches exactly |
| "Credential not found" | Credential was deleted or expired | `keystone_list_application_credentials` to confirm; create new if missing |
| Wrong project scope in token | Credential was created under different project | Check `keystone_token_info` project field; recreate credential under correct project scope |
| "Unauthorized" with valid credential | Roles insufficient for requested operation | List credential roles vs. required roles; recreate with correct role set |
| MCP server won't start | Malformed config JSON or missing binary | Validate JSON syntax; confirm `openstack-mcp-server` is in PATH |
| Works in terminal but not in Claude Code | Environment differences (PATH, keychain access) | Ensure Claude Code's process has keychain access; use full path to `security`/`secret-tool` |

## Routing

| User need | Action |
|-----------|--------|
| Authentication methods comparison | Read [auth-methods.md](references/auth-methods.md) |
