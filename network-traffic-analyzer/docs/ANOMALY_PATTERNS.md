# Common Network Anomaly Patterns Reference

A reference catalog of network anomaly patterns that security researchers and incident responders frequently encounter in packet captures. Each pattern includes a description, detection indicators, and typical causes.

> **Disclaimer:** This document is for defensive security research and authorized network analysis only.

---

## Table of Contents

1. [Port Scanning](#1-port-scanning)
2. [Network Sweeps (Host Discovery)](#2-network-sweeps-host-discovery)
3. [SYN Floods](#3-syn-floods)
4. [DNS Anomalies](#4-dns-anomalies)
5. [Beaconing / C2 Communication](#5-beaconing--c2-communication)
6. [Data Exfiltration Patterns](#6-data-exfiltration-patterns)
7. [ARP Spoofing / ARP Storm](#7-arp-spoofing--arp-storm)
8. [ICMP Anomalies](#8-icmp-anomalies)
9. [Lateral Movement](#9-lateral-movement)
10. [Protocol Anomalies](#10-protocol-anomalies)

---

## 1. Port Scanning

### Description

An attacker enumerates open ports on a target host by sending connection attempts to many ports and observing which respond.

### Sub-Types

| Scan Type | Technique | Packet Pattern |
|-----------|-----------|---------------|
| **TCP SYN scan** | Send SYN; open port replies SYN-ACK, closed replies RST | Many SYN packets from one source to one destination, each with a different dst_port |
| **TCP connect scan** | Complete 3-way handshake | Full SYN, SYN-ACK, ACK sequences to many ports |
| **TCP FIN/XMAS/NULL scan** | Send FIN, FIN+PSH+URG, or no flags | Unusual TCP flag combinations to many ports |
| **UDP scan** | Send empty UDP packets; closed port replies ICMP port unreachable | UDP packets to many ports + ICMP unreachable responses |
| **ACK scan** | Send ACK to map firewall rules | ACK packets to many ports; filtered ports produce no response |

### Detection Indicators

- One source IP contacts > 15 distinct destination ports on a single host within a short window.
- High ratio of SYN packets with no corresponding SYN-ACK.
- Many RST packets from the target (closed ports responding to SYN).
- Sequential or near-sequential port numbers (tool default behavior).

### Tool Detection

The `detect_port_scans()` function counts unique destination ports per source IP and flags sources exceeding the threshold. SYN-only packets are counted separately as a confidence booster.

---

## 2. Network Sweeps (Host Discovery)

### Description

Before port scanning, attackers often sweep an IP range to find live hosts.

### Sub-Types

| Sweep Type | Method |
|------------|--------|
| **ICMP sweep** | Ping (Echo Request) sent to every IP in a range |
| **TCP SYN sweep** | SYN to a common port (80, 443) across many IPs |
| **ARP sweep** | ARP requests for every IP in the local subnet |

### Detection Indicators

- One source IP sends packets to many destination IPs in a short time.
- Destination IPs are sequential or follow a subnet pattern.
- Uniform packet sizes and timing intervals (tool-generated traffic).

### How to Spot in This Tool

Check `top_source_ips` -- a sweeping host will have a very high packet count. Cross-reference with `top_dest_ips` to see if many destinations received only one or two packets each (characteristic of a sweep).

---

## 3. SYN Floods

### Description

A denial-of-service attack where the attacker sends a massive number of TCP SYN packets to overwhelm a target's connection table.

### Indicators

- Extremely high packet rate of TCP SYN packets to one destination IP and port.
- Source IPs are often spoofed (random or non-routable addresses).
- No corresponding SYN-ACK or ACK packets from the supposed sources.
- The traffic spike detector will flag the volume anomaly.

### Distinguishing from Legitimate Traffic

- Legitimate high-traffic services (web servers) receive SYNs from diverse, real IPs with completed handshakes.
- SYN floods show incomplete handshakes and often use non-responsive source IPs.

---

## 4. DNS Anomalies

### 4a. DNS Tunneling

**Description:** Data is exfiltrated or a covert channel is established by encoding payloads in DNS query labels and responses.

**Indicators:**
- Abnormally long DNS queries (> 50 characters).
- High Shannon entropy in query labels (> 4.0 bits).
- Very high DNS query volume to a single authoritative name server.
- TXT record queries (type 16) are preferred for tunneling due to larger response sizes.
- Base32 or Base64 encoded subdomains.

**Example:**
```
aGVsbG8gd29ybGQ.t.evil.com   (Base64 of "hello world" as subdomain)
```

### 4b. Domain Generation Algorithms (DGA)

**Description:** Malware generates many pseudo-random domain names to locate its C2 server. Only one or a few will resolve at any given time.

**Indicators:**
- Many unique DNS queries that fail (NXDOMAIN responses).
- Query names are random-looking strings (high entropy, no dictionary words).
- Queries are rapid and automated in timing.

### 4c. DNS Amplification

**Description:** Attacker sends small DNS queries with a spoofed source IP (the victim's). The DNS server sends large responses to the victim.

**Indicators:**
- Large number of DNS responses to an IP that did not send queries.
- Response sizes much larger than query sizes (amplification factor).
- ANY record queries (type 255) are commonly used for amplification.

### Tool Detection

The `detect_suspicious_dns()` function applies entropy, length, label-length, and TLD heuristics to each unique DNS query.

---

## 5. Beaconing / C2 Communication

### Description

Compromised hosts periodically contact a command-and-control (C2) server at regular intervals to check for instructions.

### Indicators

- **Periodic connections**: A host connects to the same destination IP/port at regular intervals (e.g., every 60 seconds, every 5 minutes).
- **Consistent packet sizes**: Beacon packets often have identical or near-identical sizes.
- **Low data volume per connection**: Each beacon is typically small (heartbeat).
- **Unusual destination ports**: C2 servers may use non-standard ports.
- **Connections to IP addresses rather than domain names**: Some C2 avoids DNS altogether.

### How to Spot

Use the time-series analysis to look for periodic spikes. Examine `conversation_pairs` for persistent connections to a single external IP with consistent timing.

---

## 6. Data Exfiltration Patterns

### Description

Stolen data leaving the network through various channels.

### Sub-Types

| Channel | Indicators |
|---------|-----------|
| **HTTP/HTTPS POST** | Large outbound POST requests to external servers, unusual User-Agent strings |
| **DNS tunneling** | Encoded data in DNS queries (see section 4a) |
| **ICMP tunneling** | Data encoded in ICMP payloads; unusually large ICMP packets |
| **FTP/SCP** | Outbound file transfers to external servers |
| **Cloud storage** | High-volume HTTPS to cloud storage providers |

### General Indicators

- **Bandwidth asymmetry**: An internal host sending significantly more data outbound than it receives.
- **Off-hours activity**: Data transfers during nights or weekends when the host should be idle.
- **Unusual destinations**: Transfers to IP addresses in unexpected geographies.

### How to Spot

Compare `bandwidth_per_ip(direction="src")` against `bandwidth_per_ip(direction="dst")` for each internal host. A host with high outbound bandwidth relative to inbound warrants investigation.

---

## 7. ARP Spoofing / ARP Storm

### Description

An attacker sends forged ARP messages to associate their MAC address with the IP of another host (usually the gateway), enabling man-in-the-middle attacks.

### Indicators

- **Duplicate IP-to-MAC mappings**: Multiple MAC addresses claiming the same IP.
- **Gratuitous ARP**: Unsolicited ARP replies (the host announces its own mapping without being asked).
- **ARP storm**: An unusually high volume of ARP packets, which can also cause network instability.
- **ARP replies without corresponding requests.**

### Tool Detection

The `detect_arp_anomalies()` function counts ARP packets and flags volumes exceeding the threshold.

---

## 8. ICMP Anomalies

### 8a. ICMP Flood (Ping Flood)

**Description:** Overwhelming a target with ICMP Echo Requests.

**Indicators:**
- Very high ICMP packet rate from one or few sources.
- ICMP as a disproportionate share of total traffic.

### 8b. ICMP Tunneling

**Description:** Data encoded in ICMP payloads to bypass firewalls that allow ICMP.

**Indicators:**
- ICMP packets with payloads significantly larger than the standard 32-64 bytes.
- ICMP packets with non-standard type/code values.
- Consistent, periodic ICMP traffic to a single external host.

### 8c. ICMP Redirect Attacks

**Description:** Forged ICMP Redirect messages to alter a host's routing table.

**Indicators:**
- ICMP Type 5 (Redirect) from unexpected sources.
- Multiple redirect messages in a short period.

### Tool Detection

The `detect_icmp_flood()` function flags captures where ICMP exceeds a percentage threshold.

---

## 9. Lateral Movement

### Description

After initial compromise, an attacker moves between hosts within the network to escalate privileges or access additional systems.

### Indicators

- **SMB traffic (port 445) between workstations**: Workstations rarely connect to each other via SMB in most environments.
- **RDP (port 3389) between internal hosts**: Unexpected internal RDP sessions.
- **WMI / WinRM (port 5985/5986)**: Remote management protocols used for lateral movement.
- **PsExec-like patterns**: TCP connections to port 445 followed by service creation.
- **Pass-the-hash / pass-the-ticket**: Kerberos (port 88) traffic anomalies.

### How to Spot

Examine `destination_port_frequency` for ports 445, 3389, 5985, 5986, 135, 88. Cross-reference with `conversation_pairs` to see which internal hosts are communicating on these ports.

---

## 10. Protocol Anomalies

### 10a. Encapsulation / Tunneling

**Description:** Traffic encapsulated in unexpected protocols to bypass security controls.

| Protocol | Indicators |
|----------|-----------|
| **GRE (protocol 47)** | GRE packets on a network that does not use GRE tunnels |
| **IPv6-in-IPv4 (protocol 41)** | IPv6 encapsulation where IPv6 should not be present |
| **ESP (protocol 50)** | IPsec traffic from unauthorized hosts |

### 10b. Protocol Misuse

- **HTTP on non-standard ports**: HTTP traffic on ports other than 80/8080/8443 may indicate C2 or proxy abuse.
- **DNS on non-standard ports**: DNS traffic not on port 53 may bypass DNS-based security controls.
- **SSH on non-standard ports**: While not inherently malicious, SSH on unusual ports can indicate tunneling.

### How to Spot

Check `protocol_distribution` for unexpected protocol names. Use `port_protocol_matrix` to see if protocols are appearing on unexpected ports.

---

## Quick Reference: Anomaly Detection Checklist

| Check | What to Look For |
|-------|-----------------|
| Protocol distribution | Unexpected protocols, unusual proportions |
| Top talkers | Unknown IPs, asymmetric traffic |
| Port frequency | Backdoor ports (4444, 1337, 31337), unexpected services |
| Bandwidth ratio | High outbound vs. inbound for internal hosts |
| Time series | Regular beaconing, spikes, off-hours activity |
| DNS queries | High entropy, long labels, suspicious TLDs, high volume |
| ICMP volume | Disproportionate ICMP, large ICMP payloads |
| ARP volume | ARP storms, gratuitous ARP |
| Internal lateral | SMB/RDP/WMI between workstations |
| Scan patterns | Many ports from one source, many hosts from one source |

---

## References

- MITRE ATT&CK Framework: https://attack.mitre.org/
- SANS Institute Reading Room: https://www.sans.org/reading-room/
- Wireshark Wiki - Security: https://wiki.wireshark.org/Security
- RFC 791 (IP), RFC 793 (TCP), RFC 768 (UDP), RFC 1035 (DNS)
