# Security Group Patterns for SAP CC

Common security group configurations in SAP Converged Cloud environments.

## Standard Patterns

### Web Server (HTTP/HTTPS)

```
Ingress TCP 80  from 0.0.0.0/0    — HTTP
Ingress TCP 443 from 0.0.0.0/0    — HTTPS
Ingress TCP 22  from <bastion-cidr> — SSH (restricted)
Egress  *   *   to 0.0.0.0/0      — All outbound (default)
```

Use case: Public-facing web application. SSH restricted to jump host CIDR only.

### Database Server (Internal Only)

```
Ingress TCP 5432 from <app-subnet-cidr>  — PostgreSQL
Ingress TCP 3306 from <app-subnet-cidr>  — MySQL
Ingress TCP 22   from <bastion-cidr>     — SSH (restricted)
Ingress ICMP     from <project-cidr>     — Ping for monitoring
Egress  *   *    to 0.0.0.0/0           — All outbound
```

Use case: Database accessible only from application tier. No public access.

### Intra-Project Communication (Remote Group)

```
Ingress *   *   from remote_group_id=<self>  — All traffic within group
Ingress TCP 22  from <bastion-cidr>          — SSH (restricted)
Egress  *   *   to 0.0.0.0/0                — All outbound
```

Use case: Cluster nodes (Kubernetes, Kafka, etc.) that need unrestricted communication with each other. The `remote_group_id` pointing to itself means "any port with this same group."

### Bastion / Jump Host

```
Ingress TCP 22   from <corporate-vpn-cidr>  — SSH from VPN only
Ingress ICMP     from <corporate-vpn-cidr>  — Ping from VPN
Egress  TCP 22   to <project-cidr>          — SSH to internal hosts
Egress  ICMP     to <project-cidr>          — Ping internal hosts
```

Use case: Single point of SSH entry. Tight egress limits prevent lateral movement if compromised. Note: restricted egress is unusual in SAP CC but recommended for bastions.

### Monitoring Agent

```
Ingress TCP 9100 from <prometheus-cidr>     — Node exporter
Ingress TCP 9090 from <prometheus-cidr>     — Prometheus
Ingress TCP 22   from <bastion-cidr>        — SSH
Egress  *   *    to 0.0.0.0/0              — All outbound
```

Use case: Servers running Prometheus exporters. Only the monitoring system can scrape metrics.

### Load Balancer Backend

```
Ingress TCP 8080 from <lb-subnet-cidr>      — App port from LB
Ingress TCP 8443 from <lb-subnet-cidr>      — App TLS port from LB
Ingress TCP 22   from <bastion-cidr>        — SSH
Ingress TCP 9100 from <prometheus-cidr>     — Metrics
Egress  *   *    to 0.0.0.0/0              — All outbound
```

Use case: Application servers behind Octavia load balancer. Only accepts traffic from the LB subnet.

## Anti-Patterns (Flag During Audits)

### Fully Open (Critical Risk)

```
Ingress *   *   from 0.0.0.0/0   — ALL traffic from anywhere
```

This is almost never correct. It means any IP on the internet can reach any port. Immediate remediation required.

### SSH from Anywhere (High Risk)

```
Ingress TCP 22  from 0.0.0.0/0   — SSH from internet
```

Common mistake. Should always be restricted to bastion/VPN CIDR. Brute-force attacks begin within minutes of exposure.

### Overly Broad Port Range

```
Ingress TCP 1-65535 from <cidr>   — All TCP ports
```

Usually indicates the user didn't know which port they needed. Ask them to identify the specific port and narrow the rule.

### Stale Rules (Moderate Risk)

Security groups with rules referencing CIDRs of decommissioned networks or remote_group_ids that no longer exist. These don't cause immediate harm but indicate configuration drift.

## SAP CC Specifics

### Default Security Group Behavior

Every project starts with a "default" security group containing:
```
Egress  *  *  to 0.0.0.0/0             — Allow all outbound (IPv4)
Egress  *  *  to ::/0                   — Allow all outbound (IPv6)
Ingress *  *  from remote_group=default — Allow from same group (IPv4)
Ingress *  *  from remote_group=default — Allow from same group (IPv6)
```

This means: servers in the default group can talk to each other, but nothing external can reach them. Users must explicitly add ingress rules.

### Provider Network Implications

Since SAP CC uses provider networks:
- All subnets in a project may share the same physical network segment
- Security groups are the primary isolation mechanism between workloads
- There is no "network-level" isolation like VPCs — security groups do all the work
- This makes security group hygiene more critical than in self-service environments

### Naming Conventions

Recommended naming for security groups in SAP CC:
```
<project>-<role>-<environment>
```

Examples:
- `myapp-web-prod`
- `myapp-db-prod`
- `myapp-bastion-all`
- `platform-monitoring-prod`

Avoid generic names like "test", "temp", "allow-all" — they accumulate and become impossible to audit.
