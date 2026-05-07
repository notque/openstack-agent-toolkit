# Implementation Plan: SAP Converged Cloud Agent Toolkit

## Goal

Build a complete agent toolkit for SAP Converged Cloud that teaches AI agents how to effectively use the openstack-mcp-server's 55 tools across 9 services, following the AWS agent-toolkit-for-aws plugin pattern.

## Phases

### Phase 1: Scaffolding & Infrastructure ✅ (partially done)

**Deliverables:**
- [x] Repository structure (`openstack-agent-toolkit`)
- [x] Initial `knowledge/sapcc/services.md`
- [x] Initial `skills/credential-setup/SKILL.md`
- [ ] Plugin scaffolding (`.claude-plugin/`, `plugins/sapcc/`)
- [ ] Marketplace manifest
- [ ] MCP server config (`.mcp.json`)
- [ ] Rules file (`rules/sapcc-agent-rules.md`)
- [ ] Validation script (`tools/validate.py`)
- [ ] CI workflow (`.github/workflows/validate.yml`)

**Effort:** 1 session

---

### Phase 2: Core Service Skills (Nova, Neutron, Cinder, Keystone)

These are the most-used services and have the most tool coverage in the MCP server.

#### 2a: `sapcc-compute` (Nova)
- Server lifecycle (create → active → stop → delete)
- Flavor selection guide (SAP CC flavor naming conventions)
- Gotchas: quota check first, status transitions, metadata size limits
- Cross-service: "find ports for server" pattern (nova + neutron)
- References: `flavor-families.md`, `server-troubleshooting.md`

#### 2b: `sapcc-networking` (Neutron)
- Network topology understanding (networks → subnets → ports)
- Security group debugging ("why can't I reach my server?")
- Gotchas: default security group blocks everything, port vs floating IP
- Cross-service: correlate ports with servers, check security groups
- References: `security-group-patterns.md`, `network-debugging.md`

#### 2c: `sapcc-storage` (Cinder)
- Volume lifecycle, attachment states
- Performance tiers (SAP CC volume types)
- Gotchas: volume stuck "in-use", can't delete attached volumes
- References: `volume-types.md`

#### 2d: `sapcc-identity` (Keystone)
- Domain → Project hierarchy
- Application credentials (ties into existing credential-setup skill)
- Role model, service catalog interpretation
- Gotchas: scoping matters, app creds inherit current roles
- References: `domain-project-model.md`

**Effort:** 2 sessions

---

### Phase 3: Platform Service Skills (Limes, Hermes, Maia)

These are SAP CC-specific and need the most domain knowledge baked in.

#### 3a: `sapcc-quota` (Limes)
- Quota hierarchy: cluster → domain → project
- Interpreting quota reports (quota, usage, physical_usage, burst)
- "Am I running out?" workflow
- Gotchas: units are base (MiB not GB), physical > logical is normal
- References: `quota-services-mapping.md`, `capacity-planning.md`

#### 3b: `sapcc-audit` (Hermes)
- CADF event format explanation
- "Who did what?" investigation workflow
- "What changed in the last hour?" workflow
- Gotchas: target_type uses slashes, time filter syntax, outcome values
- References: `cadf-event-format.md`, `common-queries.md`

#### 3c: `sapcc-metrics` (Maia)
- PromQL patterns for SAP CC infrastructure
- Metric discovery workflow (names → labels → query)
- Common queries: VM CPU, network throughput, volume IOPS
- Gotchas: tenant-scoped (can only see your project), time format
- References: `promql-patterns.md`, `metric-catalog.md`

**Effort:** 2 sessions

---

### Phase 4: Specialized Service Skills (Keppel, Archer)

#### 4a: `sapcc-registry` (Keppel)
- Account → Repository → Manifest hierarchy
- Image lifecycle, vulnerability status interpretation
- Cross-region federation (images replicated between regions)
- Gotchas: account ≠ project, manifest vs tag, vulnerability scan timing
- References: `image-lifecycle.md`

#### 4b: `sapcc-connectivity` (Archer)
- Service vs Endpoint model (producer/consumer pattern)
- "Access a service privately" workflow
- Gotchas: endpoint requires matching availability zone, status transitions
- References: `endpoint-provisioning.md`

**Effort:** 1 session

---

### Phase 5: Cross-Cutting Concerns

#### 5a: Enhance `credential-setup`
- Migrate from `skills/` to `plugins/sapcc/skills/`
- Add references for multi-region credential management
- Add rotation workflow

#### 5b: Knowledge enhancement
- `knowledge/sapcc/architecture.md` — Regional model, domain hierarchy
- `knowledge/sapcc/troubleshooting-flows.md` — Cross-service debugging patterns
- `knowledge/openstack/api-conventions.md` — Pagination, error codes, microversions

#### 5c: Integration testing
- Test each skill with real MCP server interactions
- Verify gotchas actually prevent common mistakes
- Validate progressive disclosure works (skills load only when needed)

**Effort:** 1 session

---

### Phase 6: Distribution & Documentation

- [ ] README with install instructions (Claude Code, Codex, manual)
- [ ] Update `openstack-mcp-server` README to reference this toolkit
- [ ] GitHub release with version tag
- [ ] Test `/plugin install` flow end-to-end

**Effort:** 1 session

---

## Priority Order

If time is limited, build skills in this order (highest user impact first):

1. **credential-setup** (already done) — Gate to everything else
2. **sapcc-quota** (Limes) — Most confusing service, highest gotcha density
3. **sapcc-compute** (Nova) — Most-used service
4. **sapcc-audit** (Hermes) — Unique to SAP CC, non-obvious API
5. **sapcc-networking** (Neutron) — Critical for debugging
6. **sapcc-metrics** (Maia) — PromQL expertise is rare
7. **sapcc-identity** (Keystone) — Domain model confusion
8. **sapcc-registry** (Keppel) — Growing usage, unique federation
9. **sapcc-storage** (Cinder) — Simpler API, fewer gotchas
10. **sapcc-connectivity** (Archer) — Niche but important

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Single plugin (`sapcc`) | All users need all services — no partial installs |
| Gotchas are numbered | Agents follow numbered lists reliably |
| Each skill ≤ 500 lines | Context budget — progressive disclosure for depth |
| References load on-demand | "Read X only if user needs Y" pattern |
| Cross-service references | Every skill says how it relates to others |
| Validation in CI | Catch broken frontmatter, dead references before merge |

## Success Criteria

- [ ] All 10 skills pass `tools/validate.py`
- [ ] Plugin installs via `/plugin install sapcc@openstack-agent-toolkit`
- [ ] Agent correctly checks quota before server creation (gotcha test)
- [ ] Agent uses Hermes for "who changed X?" questions (skill routing test)
- [ ] Agent correlates Nova servers with Neutron ports (cross-service test)
- [ ] No skill exceeds 500 lines (context budget test)

## Timeline Estimate

| Phase | Sessions | Calendar |
|-------|----------|----------|
| Phase 1: Scaffolding | 1 | Day 1 |
| Phase 2: Core services | 2 | Days 2-3 |
| Phase 3: Platform services | 2 | Days 4-5 |
| Phase 4: Specialized | 1 | Day 6 |
| Phase 5: Cross-cutting | 1 | Day 7 |
| Phase 6: Distribution | 1 | Day 8 |
| **Total** | **8 sessions** | **~2 weeks** |
