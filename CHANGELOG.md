<!--
SPDX-FileCopyrightText: 2026 SAP SE or an SAP affiliate company

SPDX-License-Identifier: Apache-2.0
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2026-05-06

### Added

- Initial release of the SAP Converged Cloud Agent Toolkit
- Plugin structure supporting Claude Code and Codex
- **10 service skills**: compute, networking, storage, identity, quota, audit, metrics, registry, connectivity, credential-setup
- **9 additional service skills**: DNS, load balancer, images, object storage, secrets, autoscaling, shared storage, baremetal, email notifications
- Rules file with baseline agent behavior guidance
- Knowledge base with service reference
- MCP server configuration for openstack-mcp-server
- Validation tooling (`tools/validate.py`)
- GitHub Actions CI for manifest validation
- Contributor infrastructure (CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md)
- Multi-agent marketplace manifests (.claude-plugin, .codex-plugin, .agents)

### Security

- Credential isolation: secrets never reach the LLM context
- Application credential guidance over password authentication
- Keychain-backed secret storage patterns
- Response sanitization in MCP server
- Project-scoped access enforcement

[0.1.0]: https://github.com/notque/openstack-agent-toolkit/releases/tag/v0.1.0
