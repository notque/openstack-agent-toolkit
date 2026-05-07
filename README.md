# OpenStack Agent Toolkit

Skills, knowledge, and prompts for AI agents working with OpenStack and SAP Converged Cloud. Designed for use with [openstack-mcp-server](https://github.com/notque/openstack-mcp-server).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  AI Agent (Claude, etc.)                                         │
├─────────────────────────────────────────────────────────────────┤
│  Agent Toolkit (this repo)          │  MCP Server                │
│  • Skills (workflows)               │  • Tool implementations    │
│  • Knowledge (context)              │  • Auth management          │
│  • Best practices                   │  • API proxying             │
└─────────────────────────────────────────────────────────────────┘
```

**MCP Server** = runtime that provides typed tools (API calls)  
**Agent Toolkit** = intelligence layer that teaches LLMs how to use those tools effectively

## Skills

| Skill | Description |
|-------|-------------|
| [credential-setup](skills/credential-setup/) | Guided workflow for creating and storing OpenStack application credentials securely |

## Knowledge

| Topic | Description |
|-------|-------------|
| [SAP CC Services](knowledge/sapcc/services.md) | Reference guide to SAP Converged Cloud services, their APIs, and common operations |

## Usage with Claude Code

Skills from this toolkit can be loaded as context when working with OpenStack:

```bash
# The MCP server provides the tools
# This toolkit provides the knowledge and workflows
```

## Security Philosophy

- **Credentials never reach the LLM** — the MCP server holds secrets in process memory
- **Application credentials over passwords** — scoped, revocable, no password exposure
- **Keychain storage** — secrets retrieved via system keychain commands, never stored in config files
- **Defense in depth** — response sanitization catches accidental leakage

## Related

- [openstack-mcp-server](https://github.com/notque/openstack-mcp-server) — The Go MCP server this toolkit complements
- [AWS Agent Toolkit](https://github.com/aws/agent-toolkit-for-aws) — Similar pattern for AWS
