---
name: sapcc-metrics
description: >
  Maia metrics querying for SAP Converged Cloud (Prometheus-as-a-Service).
  Triggers: metrics, monitoring, prometheus, promql, CPU usage, memory usage, maia, dashboard, alert, performance
version: 1.0.0
metadata:
  service: [maia]
  task: [query, monitor, debug]
  persona: [developer, devops]
---

# SAP CC Metrics (Maia)

Maia is SAP CC's multi-tenant Prometheus-as-a-Service. Same PromQL query language, but tenant-isolated — each project sees only its own metrics. Read-only via MCP.

## MCP Tools

### Read Tools
| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `maia_query` | Execute instant PromQL query | `query`, `time` (optional) |
| `maia_query_range` | Execute range PromQL query over time window | `query`, `start`, `end`, `step` |
| `maia_label_values` | Get values for a specific label | `label` (e.g., `__name__`, `instance`, `job`) |
| `maia_metric_names` | List all available metric names for current project | — |

## Maia vs Regular Prometheus

- **Same PromQL** — all standard functions and operators work (rate, avg, sum, topk, etc.)
- **Tenant-isolated** — you only see metrics from your authenticated project
- **Available metrics vary** — depends on what's instrumented in your project (not all projects have the same metrics)
- **Read-only** — no recording rules, no alert configuration, no write path via MCP
- **Instant and range queries** — maia_query executes point-in-time queries; maia_query_range returns time series over a window

## Gotchas

### 1. Results are scoped to current project — you CANNOT query other projects' metrics

Maia enforces tenant isolation via the OpenStack token. There is no way to query cross-project metrics. If you need fleet-wide data, check Limes for capacity or use cluster-level monitoring.

### 2. maia_query is INSTANT — use maia_query_range for time series

`maia_query` returns a single point in time. Use the `time` parameter to query a historical point. For time series data ("show me the last hour"), use `maia_query_range` with `start`, `end`, and `step` parameters instead.

### 3. Always start with maia_metric_names

Before writing PromQL, discover what's available. Different projects have different metrics. Never assume a metric exists — verify first.

### 4. maia_label_values with label="__name__" equals maia_metric_names

Both return the list of available metric names. Use `maia_label_values` when you need values for other labels (instance, job, device, etc.).

### 5. time parameter defaults to NOW

Optional. Accepts RFC3339 (`2024-03-15T10:00:00Z`) or Unix timestamp (`1710500400`). Omitting it gives current values. For "what was CPU at 3am?" — pass the specific timestamp.

### 6. PromQL syntax errors return generic errors

The API does not give helpful parse errors. If you get an error, validate your query syntax independently before blaming connectivity or permissions. Common mistakes: missing brackets, unbalanced quotes, typos in metric names.

### 7. Metric names vary by project

Not all projects have the same instrumentation. A compute-heavy project might have `node_cpu_seconds_total` while a Kubernetes project has `container_cpu_usage_seconds_total`. Always discover first.

### 8. Large result sets may be truncated

Queries that match many series (e.g., `{__name__=~".+"}`) can hit response size limits. Use specific label selectors to narrow: `{instance="specific-host"}`, `{job="specific-job"}`.

### 9. No aggregation across projects

If the user asks "how much CPU is our whole team using?" — that requires cluster-level access or Limes. Maia only shows the current project's metrics. Redirect to quota tools for cross-project views.

## Common Workflows

### Discover available metrics

```
1. maia_metric_names → see what's instrumented
2. Pick relevant metric name
3. maia_label_values(label="instance") → find dimensions
4. maia_label_values(label="job") → understand metric sources
```

### "Is my server healthy?"

```
1. maia_metric_names → find CPU/memory/disk metrics
2. maia_label_values(label="instance") → identify the server
3. maia_query(query='node_cpu_seconds_total{instance="<host>", mode="idle"}')
4. maia_query(query='node_memory_MemAvailable_bytes{instance="<host>"}')
5. maia_query(query='node_filesystem_avail_bytes{instance="<host>", mountpoint="/"}')
```

### "What's the current load?"

```
1. maia_query(query='rate(node_cpu_seconds_total{mode!="idle"}[5m])')
2. maia_query(query='avg by (instance) (rate(node_cpu_seconds_total{mode!="idle"}[5m]))')
```

Note: rate() requires a range vector but returns an instant vector — works with maia_query.

### Troubleshooting a specific issue

```
1. maia_metric_names → find relevant metrics (grep mentally)
2. maia_label_values(label="<relevant_label>") → explore dimensions
3. Write targeted PromQL with specific label selectors
4. Interpret the value in context (e.g., bytes → GiB, ratio → percentage)
```

## PromQL Quick Reference

Common patterns for SAP CC infrastructure metrics:

| Pattern | PromQL | Use Case |
|---------|--------|----------|
| Rate of change | `rate(metric[5m])` | Counter metrics (CPU, network bytes) |
| Average by instance | `avg by (instance) (metric)` | Reduce cardinality |
| Top N | `topk(5, metric)` | Find highest consumers |
| Threshold check | `metric > 0.9` | Alert-style filtering |
| CPU usage % | `1 - rate(node_cpu_seconds_total{mode="idle"}[5m])` | Per-core idle inverse |
| Memory usage % | `1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)` | Available/total ratio |
| Disk usage % | `1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)` | Free/total ratio |
| Sum by label | `sum by (job) (metric)` | Aggregate across instances |
| Filter by regex | `metric{label=~"pattern.*"}` | Flexible label matching |

See `references/promql-patterns.md` for extended pattern library.

## Troubleshooting

### No metrics found (maia_metric_names returns empty)

- Project has no instrumentation configured
- Token might be scoped to wrong project — verify with `keystone_token_info`
- The project may be new with nothing deployed yet

### maia_query returns empty result

- Metric name typo — copy-paste from maia_metric_names output
- Label selector too restrictive — remove labels and broaden
- Metric exists but no data at queried time — try without `time` param (defaults to now)
- Counter metric with rate() on too-short window — try `[10m]` instead of `[1m]`

### Query syntax error

- Unbalanced brackets: `rate(metric[5m]` missing closing `)`
- Wrong bracket type: range vectors use `[5m]` not `(5m)`
- Unquoted label value: must be `{label="value"}` with quotes
- Invalid duration: use `s`, `m`, `h`, `d` — not `sec`, `min`
- Metric name with dots: wrap in `{__name__="metric.with.dots"}`

### Unexpected values

- Counters always increase — use `rate()` or `increase()` to get meaningful values
- Gauge vs counter confusion — check if values only go up (counter) or fluctuate (gauge)
- Unit mismatch — bytes vs bits, MiB vs MB, seconds vs milliseconds
- `NaN` or `+Inf` — division by zero in your query or absent denominator series

## Security

Metrics reveal operational state: CPU patterns, memory pressure, disk growth rates, network traffic volumes, and deployment schedules. This data exposes:

- Capacity planning (how close to limits)
- Traffic patterns (peak times, quiet periods)
- Infrastructure topology (which instances, what roles)
- Potential vulnerabilities (overloaded systems, resource exhaustion)

Treat metric data as internal/confidential. Only query what's needed for the task at hand.

## Cross-Service References

| Need | Service | Tool |
|------|---------|------|
| Map instance label to server name | Nova | `nova_get_server(<instance_id>)` |
| Correlate resource usage with quota | Limes | `limes_get_project_quota` |
| Investigate anomalies in audit trail | Hermes | `hermes_list_events` |
| Network metrics correlation | Neutron | `neutron_list_ports(device_id=<instance_id>)` |

## Routing

| User need | Action |
|-----------|--------|
| PromQL query patterns for SAP CC | Read [promql-patterns.md](references/promql-patterns.md) |
