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
- Cross-Service References
- Routing (to reference files)

## Available Skills

| Skill | Service | Description |
|-------|---------|-------------|
| credential-setup | Keystone | Guided auth setup with keychain storage |
| sapcc-audit | Hermes | CADF event investigation, compliance queries |
| sapcc-autoscaling | Castellum | Autoscaling policies, resource operations |
| sapcc-baremetal | Ironic | Bare metal node provisioning and lifecycle |
| sapcc-compute | Nova | Server lifecycle, flavors, actions |
| sapcc-connectivity | Archer | Private endpoint services, discovery |
| sapcc-dns | Designate | DNS zones and recordsets |
| sapcc-email | Cronus | Email notifications and SMTP relay |
| sapcc-identity | Keystone | Domain/project model, app credentials |
| sapcc-images | Glance | VM boot images, properties, visibility |
| sapcc-loadbalancer | Octavia | Load balancers, pools, health monitors |
| sapcc-metrics | Maia | PromQL queries, metric discovery |
| sapcc-networking | Neutron | Networks, subnets, ports, security groups |
| sapcc-object-storage | Swift | Object storage, containers, large objects |
| sapcc-quota | Limes | Quota interpretation, capacity planning |
| sapcc-registry | Keppel | Container images, vulnerabilities, federation |
| sapcc-secrets | Barbican | Secret management, certificates, keys |
| sapcc-shared-storage | Manila | Shared file systems, exports, share networks |
| sapcc-storage | Cinder | Block storage volumes, snapshots |
