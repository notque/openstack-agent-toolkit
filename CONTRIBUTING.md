<!--
SPDX-FileCopyrightText: 2026 SAP SE or an SAP affiliate company

SPDX-License-Identifier: Apache-2.0
-->

# Contributing to SAP Converged Cloud Agent Toolkit

## How to Contribute

We welcome contributions — especially new service skills, gotcha documentation from production experience, and error-handling improvements.

### Adding a New Skill

1. **Create the directory:**
   ```bash
   mkdir -p plugins/sapcc/skills/<skill-name>
   ```

2. **Create `SKILL.md`** with required frontmatter:
   ```yaml
   ---
   name: <skill-name>          # must be kebab-case, match directory name
   description: >-
     One paragraph describing the skill. Include trigger phrases
     that agents should match on.
   version: 1.0.0
   metadata:
     service: [service-name]   # MCP tool prefix (nova, neutron, etc.)
     task: [list, inspect, debug, lifecycle]
     persona: [developer, platform-engineer]
   ---
   ```

3. **Required sections** (in order):
   - `## MCP Tools` — table of tools with key parameters
   - `## Gotchas` — numbered list of pitfalls (aim for 5-10)
   - `## Common Workflows` — step-by-step recipes
   - `## Troubleshooting` — diagnosed failure scenarios
   - `## Security Considerations` — data sensitivity, confirmation requirements
   - `## Cross-Service References` — table linking to other skills
   - `## Routing` — when to load reference files

4. **Add reference files** (if needed):
   ```bash
   mkdir -p plugins/sapcc/skills/<skill-name>/references/
   ```
   Keep SKILL.md under 500 lines. Extract deep content to references/.

5. **Validate:**
   ```bash
   python3 tools/validate.py --plugin sapcc
   ```

6. **Register in marketplace** (both formats):
   - `.claude-plugin/marketplace.json` — Claude Code
   - `.agents/plugins/marketplace.json` — Codex/Agents

### Improving an Existing Skill

The most valuable contributions are:

- **New gotchas** from production experience (with concrete examples)
- **Workflow improvements** based on real debugging sessions
- **Parameter corrections** when MCP server tools change
- **Cross-service references** connecting related skills

### Rules Contributions

The rules file (`rules/sapcc-agent-rules.md`) provides baseline agent behavior. Changes here affect ALL skill invocations — keep rules universal and test carefully.

## Quality Standards

| Requirement | Check |
|-------------|-------|
| Frontmatter valid | `python3 tools/validate.py` passes |
| Name is kebab-case | Matches `^[a-z][a-z0-9]*(-[a-z0-9]+)*$` |
| Name matches directory | Skill name == parent directory name |
| Description ≥ 20 chars | Meaningful for progressive disclosure |
| Under 500 lines | Extract to `references/` if longer |
| Parameters verified | Cross-check against MCP server source |
| No secrets in examples | Use placeholders, never real credentials |

## Development Workflow

```bash
# Fork and clone
git clone https://github.com/<your-fork>/openstack-agent-toolkit
cd openstack-agent-toolkit

# Create feature branch
git checkout -b add-sapcc-<service>

# Make changes, validate
python3 tools/validate.py

# Commit (conventional commits preferred)
git commit -m "feat(skills): add sapcc-<service> skill"

# Push and create PR
git push origin add-sapcc-<service>
```

## Developer Certificate of Origin (DCO)

Due to legal reasons, contributors will be asked to accept a DCO when they create their first pull request. This happens in an automated fashion during the submission process. SAP uses [the standard DCO text of the Linux Foundation](https://developercertificate.org/).

## Code of Conduct

We follow the [SAP Open Source Code of Conduct](CODE_OF_CONDUCT.md).
