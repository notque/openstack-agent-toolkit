# SAP Converged Cloud Guidance

- Use the SAP CC MCP Server for all OpenStack/SAP CC interactions — it provides
  authenticated API access with credential isolation (secrets never reach the LLM).
- Before starting a task, check whether a relevant sapcc-* skill is available.
  Load the skill and prefer its guidance over general knowledge.
- SAP CC uses a Domain → Project hierarchy. Always be aware of the current
  project scope (check with `keystone_token_info` if uncertain).
- For any operation that creates or resizes resources, check quota first
  via `limes_get_project_quota`.
- When debugging issues, check the audit trail (`hermes_list_events`) and
  metrics (`maia_query`) before guessing at root causes.
- When uncertain about SAP CC-specific behavior (Limes, Hermes, Maia,
  Keppel, Archer), load the relevant skill rather than guessing.
- Prefer application credentials over passwords. Use keychain storage for secrets.
- SAP CC regions are independent deployments. Credentials and resources do not
  cross region boundaries. Region naming: `<geo>-<country>-<number>` (e.g., `eu-de-1`).
