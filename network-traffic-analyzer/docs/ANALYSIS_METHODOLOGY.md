# Analysis Methodology

This document describes each analysis technique implemented in the Network Traffic Analyzer, how it works, what it reveals, and how to interpret the results.

> **Reminder:** Only analyze traffic captured with proper authorization.

---

## Table of Contents

1. [Protocol Distribution](#1-protocol-distribution)
2. [Top Source and Destination IPs](#2-top-source-and-destination-ips)
3. [Top Talkers](#3-top-talkers)
4. [Port Frequency Analysis](#4-port-frequency-analysis)
5. [Bandwidth per IP](#5-bandwidth-per-ip)
6. [Bandwidth Summary](#6-bandwidth-summary)
7. [Conversation Pairs](#7-conversation-pairs)
8. [Time-Series Analysis](#8-time-series-analysis)
9. [Port Scan Detection](#9-port-scan-detection)
10. [Traffic Spike Detection](#10-traffic-spike-detection)
11. [Suspicious DNS Detection](#11-suspicious-dns-detection)
12. [ICMP Flood Detection](#12-icmp-flood-detection)

---

## 1. Protocol Distribution

### Method

Every parsed packet has a `protocol` field (TCP, UDP, DNS, ICMP, etc.). The analyzer counts the number of packets per protocol and computes the percentage of total traffic each protocol represents.

### Implementation

```
counter = Counter(pkt["protocol"] for pkt in packets)
```

### What It Reveals

- The **dominant protocol** on the network segment. Enterprise LANs typically show 60-80% TCP, 15-25% UDP, with small amounts of ICMP and other protocols.
- Unexpected protocols (e.g., GRE, ESP, or SCTP in an environment that should not use them) may indicate tunneling or misconfiguration.
- A DNS percentage significantly higher than 5-10% may indicate DNS tunneling.

### How to Interpret

| Observation | Possible Meaning |
|-------------|-----------------|
| TCP dominates (>70%) | Normal for most networks |
| UDP unusually high (>40%) | Could indicate streaming, VoIP, DNS amplification, or scanning |
| ICMP > 10% | Possible ICMP flood, traceroute activity, or covert channel |
| Unknown protocols present | Tunneling, VPN, or unsupported encapsulation |

---

## 2. Top Source and Destination IPs

### Method

Count the number of packets originating from each source IP and destined for each destination IP separately. Return the top N by count.

### What It Reveals

- **Top sources** identify the most active senders -- useful for finding hosts generating excessive traffic (potential compromise, misconfiguration, or exfiltration).
- **Top destinations** reveal the most accessed services or endpoints.
- Comparing the two lists highlights asymmetric communication patterns.

### How to Interpret

- An internal IP appearing as a top source with connections to many external IPs may be scanning or exfiltrating.
- A single external IP appearing as a top destination for many internal hosts could be a legitimate service (e.g., CDN) or a command-and-control server.

---

## 3. Top Talkers

### Method

For each IP address, count the total number of packets where it appears as **either** source or destination. This gives a combined "talker" score.

### What It Reveals

- The overall most active hosts on the network, regardless of direction.
- Useful for capacity planning and for identifying hosts that dominate bandwidth.

### Difference from Top Source/Destination

Top source and destination are directional. Top talkers combine both directions, so a host that both sends and receives heavily ranks higher here even if it is not the single top sender or receiver.

---

## 4. Port Frequency Analysis

### Method

Count the number of packets targeting each destination port. Source ports are also tracked separately but are less analytically interesting because ephemeral ports are largely random.

### What It Reveals

- Which **services** are being accessed. Common ports map to well-known services (80=HTTP, 443=HTTPS, 53=DNS, 22=SSH, etc.).
- Unexpected ports (e.g., 4444, 1337, high random ports) may indicate backdoors, C2 channels, or peer-to-peer applications.
- The ratio of traffic across ports gives insight into the network's service profile.

### Port-to-Service Mapping

The reporter module includes a lookup table for well-known ports. Ports not in the table are labeled "Unknown" and warrant manual investigation.

---

## 5. Bandwidth per IP

### Method

Sum the `size` field (original packet length in bytes) for each IP address, grouped by source, destination, or both.

### What It Reveals

- Which hosts are transferring the most data, independent of packet count.
- A host with few packets but very high bandwidth is likely transferring large files or streaming.
- Conversely, a host with many packets but low bandwidth may be doing rapid small requests (scanning, heartbeats, C2 beaconing).

### Packet Count vs. Bandwidth

These two metrics should be considered together:

| High packet count + High bandwidth | Bulk data transfer (backups, downloads) |
|-------------------------------------|----------------------------------------|
| High packet count + Low bandwidth | Scanning, beaconing, keepalive |
| Low packet count + High bandwidth | Large file transfers, jumbo frames |
| Low packet count + Low bandwidth | Idle or minimal activity |

---

## 6. Bandwidth Summary

### Method

Aggregate statistics across the entire capture:
- **Total bytes**: Sum of all packet sizes.
- **Total packets**: Count of all packets.
- **Average packet size**: Total bytes / total packets.
- **Duration**: Time between the first and last packet.
- **Average throughput**: Bytes per second and packets per second over the capture duration.

### What It Reveals

- Baseline traffic volume for comparison against other captures.
- Average packet size can indicate the nature of traffic: small packets (~64 bytes) suggest control/signaling traffic; large packets (~1400+ bytes) suggest data transfer.

---

## 7. Conversation Pairs

### Method

For each packet, extract the (source IP, destination IP) pair, normalize it so (A, B) equals (B, A), and count occurrences. Return the top N pairs by packet count.

### What It Reveals

- The most active communication relationships on the network.
- A conversation pair with an unexpectedly high packet count between an internal host and an external IP may indicate a persistent connection (legitimate VPN, or suspicious C2).
- Pairs involving IP addresses not in your asset inventory warrant investigation.

---

## 8. Time-Series Analysis

### Method

Divide the capture timeline into fixed-width buckets (default: 60 seconds). For each bucket, count:
- **Packets per interval**: Total packets in that time window.
- **Bytes per interval**: Total bytes in that time window.

### What It Reveals

- **Traffic patterns over time**: Periodic spikes may correspond to scheduled jobs (backups, cron tasks). Random spikes may indicate attacks.
- **Baseline establishment**: A flat timeline suggests steady-state traffic. Large variance suggests bursty behavior.
- **Anomaly context**: When combined with spike detection, the timeline shows exactly when anomalies occurred.

### Choosing the Interval

| Interval | Use Case |
|----------|----------|
| 1 second | Very granular analysis, DDoS investigation |
| 10 seconds | Short captures, detailed timing |
| 60 seconds | General purpose (default) |
| 300 seconds | Long captures (hours), trend analysis |

---

## 9. Port Scan Detection

### Method

For each source IP, collect the set of distinct destination ports it contacted. If the cardinality exceeds a configurable threshold (default: 15), flag it as a potential port scan.

Additional heuristic: count SYN-only packets (SYN flag set, ACK flag not set) from the source. A high SYN-only count strengthens the scan classification because SYN scanning is the most common scan technique.

### Severity Scaling

| Condition | Severity |
|-----------|----------|
| Unique ports > threshold * 5 or SYN-only > threshold * 3 | Critical |
| Unique ports > threshold * 3 | High |
| Unique ports > threshold * 1.5 | Medium |
| At or just above threshold | Low |

### Limitations

- Legitimate services that use many ports (e.g., FTP passive mode, RPC) may trigger false positives.
- Distributed scans (multiple source IPs each contacting a few ports) will not be detected by this per-source-IP method.

### Tuning

Increase `port_scan_threshold` to reduce false positives on busy networks. Decrease it for stricter detection in controlled environments.

---

## 10. Traffic Spike Detection

### Method

1. Divide the capture into fixed-width time buckets.
2. Count packets per bucket.
3. Compute the mean and standard deviation of bucket counts.
4. Flag any bucket where `count > mean + spike_factor * stdev`.

### What It Reveals

- **DDoS floods**: Sudden surges in packet volume.
- **Burst transfers**: Scheduled jobs that generate short bursts.
- **Scanning activity**: Aggressive scans produce brief, intense traffic bursts.

### Severity Scaling

Based on the ratio of the bucket's count to the mean:

| ratio > spike_factor * 3 | Critical |
|---------------------------|----------|
| ratio > spike_factor * 2 | High |
| ratio > spike_factor | Medium |
| Just above threshold | Low |

### Tuning

- **spike_factor**: Higher values (4.0, 5.0) reduce false positives but may miss moderate spikes. Lower values (2.0) are more sensitive.
- **time_window**: Smaller windows detect shorter bursts; larger windows smooth out normal variation.

---

## 11. Suspicious DNS Detection

### Method

For each unique DNS query in the capture, apply four heuristics:

1. **Shannon entropy**: Compute the entropy of the subdomain portion (everything before the effective TLD). High entropy (>4.0 bits) suggests randomly generated characters, typical of Domain Generation Algorithms (DGA).

2. **Total query length**: Queries longer than 50 characters may indicate DNS tunneling, where data is encoded in the query label.

3. **Label length**: Any single DNS label (the parts between dots) exceeding 32 characters is unusual and may indicate encoding.

4. **Suspicious TLD**: The effective TLD is checked against a watchlist of TLDs commonly abused for malicious purposes (e.g., `.xyz`, `.top`, `.club`, `.zip`).

### Severity Scaling

| Number of triggered heuristics | Severity |
|-------------------------------|----------|
| 3 or more | High |
| 2 | Medium |
| 1 | Low |

### Shannon Entropy Explained

Shannon entropy measures the randomness of a string. For a string of length *n* with character frequencies *f_i*:

```
H = -SUM( (f_i / n) * log2(f_i / n) )
```

- `"aaa"` has entropy 0 (no randomness).
- `"abcd"` has entropy 2.0 (4 equally likely characters).
- A typical English word has entropy around 2.5-3.5.
- A random alphanumeric string has entropy around 4.5-5.0.

Legitimate domain names usually have entropy below 3.5. DGA domains and tunneling payloads typically exceed 4.0.

### Limitations

- Some legitimate services use long or high-entropy subdomains (e.g., CDN cache keys, tracking pixels).
- The suspicious TLD list is a heuristic; not all domains on those TLDs are malicious, and malicious domains can exist on any TLD.

---

## 12. ICMP Flood Detection

### Method

Count the number of ICMP packets in the capture. If ICMP exceeds a configurable percentage of total packets (default: 25%), flag it.

### What It Reveals

- **ICMP flood / ping flood**: A common denial-of-service technique.
- **ICMP covert channel**: Tools like `icmptunnel` encode data in ICMP payloads.
- **Excessive traceroute**: A large number of ICMP Time Exceeded messages.

### Tuning

- Increase `threshold_pct` on networks where ICMP monitoring is heavy (e.g., networks using ICMP-based health checks).
- The `min_packets` parameter prevents false positives on very small captures where a handful of pings could exceed the percentage threshold.

---

## General Analysis Workflow

The recommended order of analysis for an unknown PCAP:

1. **Bandwidth summary** -- Get the big picture: how many packets, how much data, how long.
2. **Protocol distribution** -- Understand the traffic mix.
3. **Top talkers / top IPs** -- Identify the most active hosts.
4. **Port frequency** -- Determine which services are in use.
5. **Time-series** -- Look for temporal patterns and spikes.
6. **Anomaly detection** -- Run automated detectors for known bad patterns.
7. **Deep-dive** -- For any flagged anomalies, return to the original PCAP in Wireshark for packet-level inspection.

This progressive approach moves from broad context to specific findings, reducing the risk of tunnel vision.
