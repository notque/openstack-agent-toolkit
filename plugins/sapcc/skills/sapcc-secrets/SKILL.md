---
name: sapcc-secrets
description: >
  Secret metadata management via Barbican (Key Manager) in SAP Converged Cloud.
  Triggers: secret, key, certificate, barbican, key manager, encryption, passphrase, credential store
version: 1.0.0
metadata:
  service: [barbican]
  task: [inspect, audit, manage]
  persona: [developer, security, platform-engineer]
---

# SAP CC Secrets (Barbican)

Inspect secret metadata stored in Barbican (OpenStack Key Manager). The MCP server provides metadata-only access — **secret payloads are never returned** for security.

## MCP Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `barbican_list_secrets` | List secrets (metadata only) | `name`, `secret_type` (returns: secret_ref, name, status, secret_type, algorithm, bit_length, created, expiration) |
| `barbican_get_secret` | Get metadata for a single secret | `secret_id` (UUID) (returns: name, status, secret_type, algorithm, bit_length, mode, created, updated, expiration, content_types) |

## Critical Security Note

**The secret payload (the actual key/certificate/password value) is NEVER returned by these tools.** This is an intentional security boundary. The MCP server only exposes metadata — enough to inventory and audit secrets, but never enough to extract sensitive material.

If a user asks to "show me the secret value" or "get the password from Barbican" — explain that this is not possible through these tools and is by design.

## Gotchas

### 1. Payload is never returned — metadata only

You will see name, type, algorithm, bit_length, expiration — but never the actual secret value. This is a security feature, not a limitation.

### 2. Secret types determine usage context

| Type | Typical Use |
|------|-------------|
| `symmetric` | Encryption keys (AES, etc.) |
| `public` | Public keys (RSA, EC) |
| `private` | Private keys (RSA, EC) |
| `passphrase` | Passwords, tokens |
| `certificate` | X.509 certificates |
| `opaque` | Arbitrary binary data |

### 3. Status "ACTIVE" means ready for use

Secrets go through: `PENDING` → `ACTIVE`. Only `ACTIVE` secrets can be consumed.

### 4. Expiration is informational — Barbican does not auto-delete

A secret past its `expiration` date is still retrievable. The expiration field is advisory — it tells you the secret SHOULD have been rotated, but Barbican does not enforce it.

### 5. secret_ref contains the UUID

The `secret_ref` field is a full URL. Extract the UUID from the end for use with `barbican_get_secret`.

### 6. Secrets are project-scoped

You only see secrets belonging to your current project. Cross-project secret sharing requires explicit ACLs.

### 7. algorithm + bit_length describe cryptographic strength

For symmetric keys: `AES` + `256` = AES-256. For asymmetric: `RSA` + `4096` = RSA-4096. Use this to audit security standards compliance.

## Common Workflows

### Inventory All Secrets

```
1. barbican_list_secrets()
2. Review: name, type, status, expiration
3. Flag any with expired dates or weak algorithms
```

### Find Certificates Nearing Expiration

```
1. barbican_list_secrets(secret_type=certificate)
2. Check expiration field for each
3. Certificates past or near expiration need rotation
```

### Audit Secret Usage for Compliance

```
1. barbican_list_secrets() → full inventory
2. barbican_get_secret(secret_id) for each → detailed metadata
3. Cross-reference with Hermes: hermes_list_events(target_type=key-manager/secret)
```

## Troubleshooting

### No secrets found

- Project may not use Barbican
- Check project scope: `keystone_token_info`
- Secrets may be stored under different names than expected

### Secret status is not ACTIVE

- `PENDING`: Store operation may have failed
- Check Hermes: `hermes_list_events(target_type=key-manager/secret, outcome=failure)`

## Security Considerations

- Even metadata reveals security posture: weak algorithms, expired certs, naming patterns
- Secret names may reveal infrastructure details (service names, environments)
- Report expired secrets and weak algorithms (< AES-128, < RSA-2048) as findings
- Never suggest workarounds to extract secret payloads

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Who accessed/created secrets | Hermes | `hermes_list_events(target_type=key-manager/secret)` |
| Secret quota usage | Limes | `limes_get_project_quota(service=key-manager)` |
| TLS certificates for LBs | Octavia | `octavia_list_listeners` (TERMINATED_HTTPS uses Barbican) |
| Project identity context | Keystone | `keystone_token_info` |
