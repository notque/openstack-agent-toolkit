---
name: sapcc-secrets
description: >
  Secret management operations via Barbican. Triggers: secret, key, certificate,
  barbican, key manager, encryption, tls cert. NOT for: application credentials
  (use sapcc-identity/Keystone).
version: 1.0.0
metadata:
  service: [barbican]
  task: [manage, inspect, debug]
  persona: [developer, platform-engineer]
---

# SAP CC Secrets (Barbican)

Inspect secrets stored in the key manager: list secrets, check metadata, verify expiration. Payload is never exposed.

## MCP Tools

### Read Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `barbican_list_secrets` | List secret metadata (payload never returned) | `name`, `secret_type` (symmetric/public/private/passphrase/certificate/opaque) |
| `barbican_get_secret` | Get single secret metadata | `secret_id` (**required**) |
| `barbican_list_containers` | List secret containers (cert bundles, RSA pairs) | `name`, `type` (generic/rsa/certificate) |
| `barbican_get_container` | Get container detail with secret refs | `container_id` (**required**) |
| `barbican_list_orders` | List secret generation orders | (none) |

### Security: Credential Isolation

- **Secret payloads are NEVER returned** by any Barbican MCP tool
- Only metadata is exposed: name, type, status, algorithm, bit_length, expiration
- To retrieve actual secret values, use the OpenStack CLI with appropriate RBAC
- No write or admin tiers exist for Barbican — all 5 tools are read-only

### Guardrails

- **UUID validation**: `secret_id` and `container_id` validated before API call
- **No payload access**: By design, the MCP server never fetches or returns secret payload content

## Gotchas

1. **Payload is NEVER returned.** For security, the MCP tools only return secret metadata (name, type, algorithm, status, expiration). The actual secret value/payload is never exposed through these tools. Do not tell users you can retrieve secret contents.

2. **secret_id is a UUID, not the secret_ref URL.** Barbican internally uses `secret_ref` (a full URL like `https://keymanager.example.com/v1/secrets/<uuid>`). The MCP tool expects only the UUID portion, not the full URL.

3. **Expiration can be null.** Not all secrets have an expiration date. A null `expiration` means the secret never expires. Do not assume all secrets rotate automatically.

4. **secret_type determines usage context.** `certificate` = TLS certs (used by Octavia for TERMINATED_HTTPS). `symmetric` = encryption keys. `passphrase` = passwords. `opaque` = arbitrary data. Understanding the type helps identify what service consumes it.

5. **Status "ACTIVE" means usable.** Secrets in non-ACTIVE states may have failed creation or been soft-deleted. Only ACTIVE secrets can be consumed by other services.

6. **Certificates used by load balancers.** Octavia's TERMINATED_HTTPS listeners reference Barbican secrets of type `certificate`. To find which cert a listener uses, get the listener details and look for the certificate reference.

7. **Algorithm and bit_length may be empty.** These fields are informational and only populated if the creator set them. They are not enforced by Barbican.

## Common Workflows

### List All Certificates Approaching Expiration

1. `barbican_list_secrets` with `secret_type=certificate` — get all certificate secrets.
2. Check `expiration` field on each result.
3. Flag any certificates expiring within 30 days for renewal.

### Find the Certificate Used by a Load Balancer

1. `octavia_list_listeners` with `loadbalancer_id=<uuid>` — find TERMINATED_HTTPS listeners.
2. Note the certificate container reference from the listener details.
3. `barbican_get_secret` with the secret UUID — verify certificate metadata and expiration.

### Audit Project Secrets

1. `barbican_list_secrets` — enumerate all secrets in the project.
2. Group by `secret_type` to understand the distribution (certs vs keys vs passphrases).
3. Check `expiration` for any expired secrets that should be cleaned up.

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Which LB listener uses a certificate | Octavia | `octavia_list_listeners(loadbalancer_id=<uuid>)` |
| Who created/accessed a secret | Hermes | `hermes_list_events(target_type=secret)` |
| Key manager quota | Limes | `limes_get_project_quota(service=key-manager)` |
| Application credentials (not secrets) | Keystone | `keystone_list_application_credentials` |
