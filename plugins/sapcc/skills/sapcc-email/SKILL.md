---
name: sapcc-email
description: >
  Email service operations via Cronus. Triggers: email, cronus, smtp, template,
  email usage, sending. NOT for: monitoring alerts (use sapcc-metrics/Maia).
version: 1.0.0
metadata:
  service: [cronus]
  task: [manage, inspect, debug]
  persona: [developer, platform-engineer]
---

# SAP CC Email (Cronus)

Inspect email service status: check sending usage and list available email templates for the current project.

## MCP Tools

> **Note**: Cronus MCP tools are planned but not yet implemented in the MCP server. The skill documents the service for reference. When tools become available, they will follow the `cronus_` prefix pattern.

### Expected Tools (NOT YET AVAILABLE)

| Tool | Purpose | Expected Parameters |
|------|---------|---------------------|
| `cronus_list_senders` | List verified sender addresses | project_id |
| `cronus_get_usage` | Get email sending usage/limits | project_id |

### Interim Workaround

Until Cronus MCP tools are available:
- Use `hermes_list_events(target_type=email/*)` for email audit trail
- Email configuration is typically managed via the SAP CC dashboard

## Gotchas

1. **No parameters on either tool.** Both Cronus tools operate on the current project scope determined by the authenticated credentials. You cannot query a different project without re-scoping.

2. **Usage is project-scoped, not user-scoped.** The usage endpoint shows aggregate email sending statistics for the entire project, not per-user breakdowns.

3. **Templates are pre-configured, not arbitrary.** Cronus templates are set up by project administrators. You cannot create or modify templates via MCP tools — these are read-only inspection tools.

4. **Cronus is SAP CC-specific.** This is not a standard OpenStack service. It is a SAP Converged Cloud extension for managed email sending. Do not confuse with external SMTP services or third-party email providers.

5. **Rate limits and quotas are enforced server-side.** If usage shows high volume, the project may be approaching sending limits. The usage response typically includes rate/quota information.

6. **Email sending failures are not shown here.** Cronus usage shows aggregate stats. For individual delivery failures or bounces, check application logs or the Cronus dashboard (not available via MCP).

## Common Workflows

### Check Email Service Status

1. `cronus_get_usage` — inspect current sending volume, quotas, and status.
2. Verify the project has email sending enabled (non-error response).
3. Check usage against limits to determine remaining capacity.

### List Available Templates for Integration

1. `cronus_list_senders` — see all configured templates.
2. Note template names/IDs for use in application code.
3. Templates define the email structure; applications provide the dynamic content.

### Diagnose Email Sending Issues

1. `cronus_get_usage` — check if the project has hit sending limits.
2. If usage is near quota, sending may be throttled or blocked.
3. If the API returns an error, the Cronus service may not be enabled for this project.
4. For audit trail: `hermes_list_events` filtered to Cronus actions.

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Who configured email templates | Hermes | `hermes_list_events(target_type=template)` |
| Project identity and scope | Keystone | `keystone_list_projects` |
| Monitoring alerts (not email) | Maia | `maia_list_alerts` |
| Application credentials for SMTP auth | Keystone | `keystone_list_application_credentials` |
