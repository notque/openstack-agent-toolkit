# PromQL Patterns for SAP CC / OpenStack Infrastructure

## CPU Metrics

### CPU utilization per instance (percentage)
```promql
100 * (1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])))
```

### CPU breakdown by mode
```promql
avg by (mode) (rate(node_cpu_seconds_total[5m]))
```

### High CPU alert (>90%)
```promql
100 * (1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m]))) > 90
```

### CPU steal time (noisy neighbor detection)
```promql
rate(node_cpu_seconds_total{mode="steal"}[5m]) > 0.05
```

## Memory Metrics

### Memory usage percentage
```promql
100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)
```

### Available memory in GiB
```promql
node_memory_MemAvailable_bytes / 1024 / 1024 / 1024
```

### Memory pressure (low available)
```promql
(node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) < 0.1
```

### Swap usage (indicates memory pressure)
```promql
node_memory_SwapTotal_bytes - node_memory_SwapFree_bytes
```

## Disk Metrics

### Disk usage percentage by mountpoint
```promql
100 * (1 - node_filesystem_avail_bytes / node_filesystem_size_bytes)
```

### Disk filling prediction (hours until full at current rate)
```promql
node_filesystem_avail_bytes / (rate(node_filesystem_avail_bytes[1h]) * -1) / 3600
```

### Disk I/O utilization
```promql
rate(node_disk_io_time_seconds_total[5m])
```

### Disk read/write throughput (bytes/sec)
```promql
rate(node_disk_read_bytes_total[5m])
rate(node_disk_written_bytes_total[5m])
```

### IOPS
```promql
rate(node_disk_reads_completed_total[5m])
rate(node_disk_writes_completed_total[5m])
```

## Network Metrics

### Network throughput (bytes/sec per interface)
```promql
rate(node_network_receive_bytes_total{device!="lo"}[5m])
rate(node_network_transmit_bytes_total{device!="lo"}[5m])
```

### Network errors
```promql
rate(node_network_receive_errs_total[5m]) > 0
rate(node_network_transmit_errs_total[5m]) > 0
```

### Packet drops
```promql
rate(node_network_receive_drop_total[5m]) > 0
rate(node_network_transmit_drop_total[5m]) > 0
```

### TCP connection states
```promql
node_netstat_Tcp_CurrEstab
```

## OpenStack Nova (Compute) Metrics

### VM count by hypervisor
```promql
openstack_nova_running_vms
```

### vCPU allocation ratio
```promql
openstack_nova_vcpus_used / openstack_nova_vcpus_available
```

### Memory allocation
```promql
openstack_nova_memory_used_bytes / openstack_nova_memory_available_bytes
```

### Local disk usage
```promql
openstack_nova_local_storage_used_bytes / openstack_nova_local_storage_available_bytes
```

## OpenStack Neutron (Network) Metrics

### Port count by network
```promql
openstack_neutron_ports{status="ACTIVE"}
```

### Floating IP usage
```promql
openstack_neutron_floating_ips{status="ACTIVE"}
```

## Container/Kubernetes Metrics (if project runs K8s)

### Container CPU usage
```promql
rate(container_cpu_usage_seconds_total{container!=""}[5m])
```

### Container memory usage
```promql
container_memory_working_set_bytes{container!=""}
```

### Pod restart count
```promql
increase(kube_pod_container_status_restarts_total[1h])
```

### OOMKill events
```promql
increase(kube_pod_container_status_last_terminated_reason{reason="OOMKilled"}[1h])
```

## Aggregation Patterns

### Top 5 by CPU usage
```promql
topk(5, 100 * (1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m]))))
```

### Bottom 5 by free disk
```promql
bottomk(5, node_filesystem_avail_bytes{mountpoint="/"})
```

### Count instances above threshold
```promql
count(node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes < 0.2)
```

### Average across all instances
```promql
avg(rate(node_cpu_seconds_total{mode!="idle"}[5m]))
```

### Sum total network traffic
```promql
sum(rate(node_network_receive_bytes_total{device!="lo"}[5m]))
```

## Time-Based Patterns

### Compare to 1 hour ago (requires two separate instant queries)

Query at current time:
```promql
avg(rate(node_cpu_seconds_total{mode!="idle"}[5m]))
```
Then query with `time` parameter set to 1 hour ago for comparison.

### Rate over different windows

Short-term spike detection:
```promql
rate(metric[1m])
```

Smoothed trend:
```promql
rate(metric[30m])
```

## Label Manipulation

### Group by job
```promql
sum by (job) (up)
```

### Filter by regex on instance name
```promql
node_cpu_seconds_total{instance=~"web-.*"}
```

### Exclude specific labels
```promql
node_network_receive_bytes_total{device!~"lo|veth.*|docker.*"}
```

## Useful Instant Checks

### "Is everything up?"
```promql
up == 0
```

### "Which targets are being scraped?"
```promql
up
```

### "How long since last scrape?"
```promql
time() - node_time_seconds
```

## Notes on SAP CC Context

- Metric availability depends entirely on project instrumentation
- `node_*` metrics appear when node-exporter is deployed on instances
- `openstack_*` metrics appear when OpenStack exporters are configured
- `container_*` and `kube_*` metrics appear in Kubernetes-enabled projects
- Always run `maia_metric_names` first to confirm which metric families exist
- Metric retention varies — very old historical points may not be available
