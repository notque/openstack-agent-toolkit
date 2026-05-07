<!--
SPDX-FileCopyrightText: 2026 SAP SE or an SAP affiliate company

SPDX-License-Identifier: Apache-2.0
-->

# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

### How to Report

Please report security issues via the SAP Trust Center at [https://www.sap.com/about/trust-center/security/incident-management.html](https://www.sap.com/about/trust-center/security/incident-management.html).

Alternatively, you can email [secure@sap.com](mailto:secure@sap.com).

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 5 business days
- **Resolution target**: Varies by severity

## Security Design

This toolkit follows defense-in-depth principles:

1. **Credentials never reach the LLM** — The MCP server holds secrets in process memory; only sanitized responses flow to the agent.
2. **Application credentials over passwords** — Scoped, revocable, auditable.
3. **Keychain storage** — Secrets retrieved via OS commands (`security find-generic-password` on macOS, `pass` on Linux), never stored in plaintext config.
4. **Response sanitization** — The MCP server strips sensitive fields before returning results.
5. **Project-scoped access** — All operations are scoped to the authenticated project.
6. **Audit trail** — All actions are logged to Hermes with the credential identity.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |

## Scope

This policy covers:
- The agent toolkit (skills, rules, knowledge)
- Plugin manifests and configuration
- The validation tooling

For vulnerabilities in the MCP server itself, please report to the [openstack-mcp-server](https://github.com/notque/openstack-mcp-server) repository.
