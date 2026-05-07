# Authentication Methods for OpenStack MCP Server

Comparison of authentication methods available for the openstack-mcp-server, with recommendations for each use case.

## Method Comparison

| Method | Security | Rotation | MCP Suitability | Scope Control |
|--------|----------|----------|-----------------|---------------|
| Application Credential | High | Manual (with expiry) | **Recommended** | Per-project, frozen roles |
| Password | Low | Shared lifecycle | Not recommended | Full user access |
| Token | Medium | Auto-expires (hours) | Impractical | Inherits current scope |

## Application Credential (Recommended)

**How it works:** A project-scoped credential with its own ID and secret, tied to a specific user and project. Authenticates directly with Keystone without exposing the user's password.

**Pros:**
- Secret is independent of user password (password change doesn't break MCP)
- Scoped to single project (limits blast radius)
- Roles frozen at creation (predictable permissions)
- Can set expiration date
- Revocable without affecting other credentials
- Cannot create other app credentials (anti-escalation)

**Cons:**
- Secret shown only once at creation
- Cannot exceed the creating user's roles
- Must recreate to pick up new role assignments
- 25-credential limit per user

**MCP server config pattern:**
```
OS_APPLICATION_CREDENTIAL_ID + OS_APPCRED_SECRET_CMD (keychain retrieval)
```

## Password Auth

**How it works:** User's OpenStack password passed directly to the MCP server process, which exchanges it for tokens as needed.

**Pros:**
- Simple setup (no credential creation step)
- Always has current roles
- No expiration management

**Cons:**
- Password exposed to MCP server process
- Password rotation breaks all MCP instances
- Full user access (all projects, all roles) unless manually scoped
- Cannot revoke without changing password (affects everything)
- Violates principle of least privilege
- Password may be subject to external rotation policies (LDAP, SSO)

**MCP server config pattern:**
```
OS_USERNAME + OS_PASSWORD + OS_PROJECT_NAME + OS_USER_DOMAIN_NAME + OS_PROJECT_DOMAIN_NAME
```

## Token Auth

**How it works:** A pre-obtained Keystone token passed to the MCP server. Token is already scoped and has limited lifetime (typically 1-4 hours).

**Pros:**
- No long-lived secrets stored
- Already scoped to project
- Revocable via Keystone

**Cons:**
- Expires in hours — MCP server stops working until manually refreshed
- Requires external process to obtain and refresh tokens
- Impractical for always-on MCP server use
- Adds operational complexity with no security benefit over app credentials

**MCP server config pattern:**
```
OS_TOKEN (must be refreshed externally)
```

## Decision Matrix

| Scenario | Recommended Method | Reason |
|----------|-------------------|--------|
| Developer local setup | Application Credential (1yr expiry) | Set-and-forget, secure, revocable |
| Production/shared CI | Application Credential (90d expiry) | Forced rotation, minimal permissions |
| Quick one-off testing | Token | No credential cleanup needed |
| Legacy migration | Password → App Credential | Migrate away from password ASAP |
| Multi-project access | Multiple App Credentials | One per project, independent lifecycle |

## Migration Path: Password to Application Credential

1. Authenticate with password (current state)
2. Create app credential scoped to needed project
3. Store secret in keychain
4. Update MCP config to use app credential
5. Verify MCP server works with new auth
6. Remove password from any config files
7. Confirm no other processes depend on stored password

## Security Considerations

- **Keychain storage is mandatory.** Secrets in environment variables, dotfiles, or config files are readable by any process with file access.
- **One credential per MCP instance.** Sharing credentials across instances means you cannot revoke one without breaking all.
- **Monitor credential age.** Credentials without expiration should be audited quarterly.
- **App credentials survive password changes.** This is a feature (MCP doesn't break) and a risk (compromised cred persists). Set expiration as mitigation.
