# Architecture Guide

## Overview

The Cloud Infrastructure Lab builds a standard three-tier cloud architecture pattern on AWS. This document explains each component, how they interconnect, and the design decisions behind the architecture.

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        AWS Cloud                             │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              VPC (10.0.0.0/16)                         │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │         Public Subnet (10.0.1.0/24)              │  │  │
│  │  │              Availability Zone: us-east-1a       │  │  │
│  │  │                                                  │  │  │
│  │  │  ┌────────────────────────────────────────────┐  │  │  │
│  │  │  │          EC2 Instance (t2.micro)            │  │  │  │
│  │  │  │          Ubuntu 22.04 LTS                   │  │  │  │
│  │  │  │                                            │  │  │  │
│  │  │  │  ┌──────────┐    ┌───────────────────┐    │  │  │  │
│  │  │  │  │  Nginx   │───▶│  Node.js Express  │    │  │  │  │
│  │  │  │  │  :80     │    │  :3000            │    │  │  │  │
│  │  │  │  └──────────┘    └───────────────────┘    │  │  │  │
│  │  │  │          │ Managed by PM2                  │  │  │  │
│  │  │  └────────────────────────────────────────────┘  │  │  │
│  │  │         ▲                                        │  │  │
│  │  │         │ Security Group                         │  │  │
│  │  │         │ Inbound: 22, 80, 3000                  │  │  │
│  │  │         │ Outbound: All                          │  │  │
│  │  └─────────┼────────────────────────────────────────┘  │  │
│  │            │                                            │  │
│  │  ┌─────────┼──────┐                                    │  │
│  │  │  Route Table    │                                    │  │
│  │  │  0.0.0.0/0 → IGW│                                   │  │
│  │  └─────────┼──────┘                                    │  │
│  └────────────┼───────────────────────────────────────────┘  │
│               │                                              │
│       ┌───────┴───────┐         ┌──────────────┐            │
│       │ Internet      │         │  CloudWatch  │            │
│       │ Gateway       │         │  Monitoring  │            │
│       └───────┬───────┘         └──────────────┘            │
└───────────────┼──────────────────────────────────────────────┘
                │
         ┌──────┴──────┐
         │   Internet  │
         │   (Users)   │
         └─────────────┘
```

---

## Component Details

### 1. VPC (Virtual Private Cloud)
- **CIDR Block:** `10.0.0.0/16` — provides 65,536 private IP addresses
- **Purpose:** Isolates our infrastructure in a logically separated network
- **DNS:** Both DNS support and DNS hostnames are enabled

### 2. Public Subnet
- **CIDR Block:** `10.0.1.0/24` — 256 addresses within the VPC
- **Availability Zone:** `us-east-1a`
- **Auto-assign Public IP:** Enabled — instances get public IPs automatically
- **Purpose:** Hosts internet-facing resources

### 3. Internet Gateway
- Provides bidirectional internet access for the VPC
- Attached to the VPC and referenced in the route table
- Required for any resource in the VPC to communicate with the internet

### 4. Route Table
- Routes `10.0.0.0/16` traffic locally within the VPC
- Routes `0.0.0.0/0` (all other traffic) through the Internet Gateway
- Associated with the public subnet

### 5. Security Group
Acts as a virtual firewall for the EC2 instance:

| Direction | Port | Protocol | Source | Purpose |
|-----------|------|----------|--------|---------|
| Inbound | 22 | TCP | 0.0.0.0/0 | SSH access |
| Inbound | 80 | TCP | 0.0.0.0/0 | HTTP (Nginx) |
| Inbound | 3000 | TCP | 0.0.0.0/0 | Node.js direct |
| Outbound | All | All | 0.0.0.0/0 | All outbound |

### 6. EC2 Instance
- **AMI:** Ubuntu Server 22.04 LTS
- **Type:** t2.micro (1 vCPU, 1 GB RAM — Free Tier)
- **Storage:** 20 GB gp3 EBS volume
- **User Data:** Bootstrap script installs Nginx, Node.js, and deploys the app

### 7. Application Stack

#### Nginx (Reverse Proxy)
- Listens on port 80
- Forwards requests to Node.js on port 3000
- Adds security headers (X-Frame-Options, X-Content-Type-Options)
- Handles connection upgrades for WebSocket compatibility

#### Node.js Express Server
- Runs on port 3000, managed by PM2
- Endpoints: `/` (status), `/health` (detailed), `/metrics` (Prometheus), `/ready` (probe)
- PM2 ensures automatic restart on crash and startup on boot

### 8. CloudWatch Monitoring
- **Detailed Monitoring:** 1-minute metric intervals
- **Alarms:** CPU utilization > 80%, status check failures
- **Dashboard:** Visual overview of instance health

---

## Data Flow

1. **User Request** → Internet → Internet Gateway
2. **Internet Gateway** → Routes to EC2 via public subnet
3. **Security Group** → Allows traffic on port 80
4. **Nginx (:80)** → Reverse proxies to Node.js (:3000)
5. **Node.js** → Processes request, returns JSON response
6. **Response** → Nginx → Internet Gateway → User

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Single AZ deployment | Simplicity for learning; production would use multi-AZ |
| t2.micro instance | Free Tier eligible, sufficient for demo workload |
| Nginx reverse proxy | Industry standard, adds security headers, handles static files |
| PM2 process manager | Auto-restart, log management, startup scripts |
| gp3 storage | Better price-performance than gp2, baseline 3000 IOPS |
| Public subnet only | Simplicity; production would add private subnets for databases |

---

## Production Considerations

For a production deployment, you would add:
- **Multi-AZ:** Deploy across 2+ availability zones
- **Load Balancer:** Application Load Balancer (ALB) in front of instances
- **Auto Scaling:** Scale instances based on CPU/request metrics
- **Private Subnets:** Databases and internal services in private subnets
- **NAT Gateway:** Allow private subnet resources to access the internet
- **SSL/TLS:** ACM certificate on the ALB for HTTPS
- **RDS:** Managed database instead of local storage
- **S3:** Static asset storage
- **CloudFront:** CDN for global content delivery
