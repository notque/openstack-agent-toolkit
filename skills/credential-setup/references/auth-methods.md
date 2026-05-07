# OpenStack Authentication Methods

## Comparison for MCP Server Use

| Method | Security | Convenience | Recommended |
|--------|----------|-------------|-------------|
| Application Credential | High (scoped, revocable, no password) | High (set once, forget) | **Yes** |
| Password + OS_PW_CMD | Medium (password in keychain) | Medium (keychain access prompts) | Acceptable |
| Password in env/config | Low (plaintext in files) | High | **Never** |
| Token (manual) | Low (expires, not auto-refreshed) | Low | Never |

## Application Credentials

Application credentials are the recommended authentication method for MCP servers:

- **Scoped**: Automatically scoped to the project they were created in
- **Revocable**: Delete without changing your password
- **Role-limited**: Can have a subset of your roles
- **Password-free**: Your main password is never stored anywhere
- **Expirable**: Set expiration for automatic rotation enforcement

### Limitations

- Cannot create other application credentials (unless `unrestricted: true`)
- Cannot change your password
- Scoped to exactly one project (create multiple for multi-project access)
- If your user account is disabled, all app credentials stop working

## OS_PW_CMD Pattern

For password-based auth, use the command pattern to avoid storing passwords:

```bash
# macOS Keychain
OS_PW_CMD="security find-generic-password -a <username> -s openstack -w"

# Linux (pass)
OS_PW_CMD="pass show openstack/<username>"

# Linux (GNOME Keyring)  
OS_PW_CMD="secret-tool lookup service openstack account <username>"

# 1Password CLI
OS_PW_CMD="op item get 'OpenStack' --fields password"
```

## Migration Path

1. Start with password + OS_PW_CMD (quickest to set up)
2. Create an application credential using the MCP server itself
3. Switch configuration to use the app credential
4. Verify everything works
5. Done — your password is no longer needed in the MCP config
