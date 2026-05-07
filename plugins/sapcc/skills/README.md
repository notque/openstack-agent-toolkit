# Skills

This directory contains all SAP CC agent skills, accessible through the `sapcc` plugin.

## How Skills Work

Each skill is a directory containing a `SKILL.md` file with instructions, plus optional reference files. Skills use progressive disclosure:

1. At startup, the agent reads only the skill name and description (~50 tokens per skill)
2. When a task matches a skill's description, the agent loads the full instructions
3. Reference files load on-demand as specific phases require them
4. Skill context releases when the task completes

## Skill Format

```
skill-name/
├── SKILL.md              # Required: frontmatter + workflow + gotchas
└── references/           # Optional: deep-dive content loaded on demand
    ├── topic-a.md
    └── topic-b.md
```

The `SKILL.md` includes YAML frontmatter with `name` and `description`, followed by:
- MCP Tools table
- Gotchas (numbered agent mistake corrections)
- Common Workflows
- Troubleshooting
- Security Considerations
