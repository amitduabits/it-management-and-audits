# Sample Data

This directory contains sample PCAP files and the script used to generate them.

## Generating a Sample PCAP

The `generate_sample_pcap.py` script creates a synthetic PCAP file containing a controlled mix of normal and anomalous network traffic. No real network access is required -- all traffic is fabricated in memory using Scapy.

### Prerequisites

```bash
pip install scapy
```

### Usage

```bash
# Generate with defaults (~300 normal packets + anomalies, seed=42)
python samples/generate_sample_pcap.py

# Customize output path and packet count
python samples/generate_sample_pcap.py --output samples/demo.pcap --count 500 --seed 123
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--output`, `-o` | `samples/demo.pcap` | Output file path |
| `--count`, `-c` | 300 | Approximate number of normal-traffic packets |
| `--seed`, `-s` | 42 | Random seed for reproducibility |

### What Gets Generated

The synthetic PCAP includes the following traffic categories:

#### Normal Traffic

| Category | % of Normal Count | Description |
|----------|-------------------|-------------|
| HTTP/HTTPS | 40% | TCP 3-way handshakes to ports 80, 443, 8080 with random payloads |
| DNS | 20% | UDP queries to 8.8.8.8 for legitimate domain names |
| SSH | 15% | TCP connections to port 22 with encrypted-style payloads |
| ICMP | 10% | Echo request / reply pairs (pings) |

#### Anomalous Traffic (always appended)

| Category | Details |
|----------|---------|
| **Port scan** | 50 SYN packets from `10.0.0.99` targeting distinct ports on a single host |
| **Traffic spike** | 200 packets in a 0.2-second burst from `192.168.1.200` to `93.184.216.34` |
| **Suspicious DNS** | 15 queries with high-entropy, long labels and suspicious TLDs (`.xyz`, `.top`, `.club`, `.zip`, `.click`) |

### IP Address Ranges

- **Internal hosts:** `192.168.1.0/24` (simulated LAN)
- **External hosts:** Public IPs of well-known services (Google DNS, example.com, CDNs)
- **Scanner IP:** `10.0.0.99`
- **Spike source:** `192.168.1.200`

### Reproducibility

Passing the same `--seed` value produces identical PCAP output. This is useful for regression testing and benchmarking. The default seed is `42`.

### File Format

The output is a standard **libpcap** format PCAP file (magic `0xA1B2C3D4`, Ethernet link layer). It can be opened in:

- Wireshark
- tcpdump
- tshark
- This project's analyzer

### Example Workflow

```bash
# 1. Generate the sample
python samples/generate_sample_pcap.py --output samples/demo.pcap

# 2. Parse it
python -m src.cli parse samples/demo.pcap --output parsed.json

# 3. Analyze
python -m src.cli analyze samples/demo.pcap

# 4. Detect anomalies
python -m src.cli detect samples/demo.pcap

# 5. Visualize
python -m src.cli visualize samples/demo.pcap --output-dir charts/

# 6. Full report
python -m src.cli report samples/demo.pcap --format html --output report.html --include-charts
```

## Using Your Own PCAP Files

Place any `.pcap` or `.pcapng` file in this directory and point the analyzer at it. See `docs/WIRESHARK_GUIDE.md` for instructions on capturing real traffic with Wireshark.

> **Important:** Only analyze traffic from networks you own or have explicit, written authorization to monitor. Unauthorized capture or analysis of network traffic may violate applicable laws.
