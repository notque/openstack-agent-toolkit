# Security Checklist for Application Credentials

## Before Creating

- [ ] Identify minimum required roles for the MCP server's use case
- [ ] Choose appropriate expiration (90 days production, 1 year development)
- [ ] Verify you're in the correct project scope
- [ ] Confirm system keychain is accessible

## During Creation

- [ ] Use descriptive name: `mcp-server-<project>-<region>`
- [ ] Include description with purpose and date
- [ ] Specify roles explicitly (don't inherit all roles unless needed)
- [ ] Save the secret IMMEDIATELY (only shown once)

## After Creation

- [ ] Store secret in system keychain (never in plain text)
- [ ] Update MCP server config to use OS_APPLICATION_CREDENTIAL_ID
- [ ] Use OS_APPCRED_SECRET_CMD to retrieve from keychain
- [ ] Test authentication works with new credential
- [ ] Delete any old/unused credentials
- [ ] Verify old credential is revoked (test should fail)

## Ongoing

- [ ] Monitor expiration dates
- [ ] Rotate before expiry (create new → verify → delete old)
- [ ] Audit unused credentials periodically (`keystone_list_application_credentials`)
- [ ] Review roles — remove any no longer needed

## Red Flags

| Situation | Action |
|-----------|--------|
| Secret stored in config file | Migrate to keychain immediately |
| Credential with no expiration in production | Set expiration, schedule rotation |
| Credential with `unrestricted: true` | Delete and recreate without unrestricted |
| Multiple credentials with same roles | Consolidate to one per purpose |
| Credential still active after user leaves | Delete immediately |
