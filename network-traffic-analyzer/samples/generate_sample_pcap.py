#!/usr/bin/env python3
"""
Synthetic PCAP Generator
=========================

Generates a PCAP file containing a mix of normal and anomalous network
traffic. The resulting file can be used to exercise every feature of the
Network Traffic Analyzer without needing a real capture.

Traffic categories generated
-----------------------------
1. **Normal HTTP/HTTPS** -- TCP connections to ports 80 and 443.
2. **Normal DNS** -- UDP queries to a DNS server on port 53.
3. **Normal SSH** -- TCP connections to port 22.
4. **ICMP echo** -- Ping requests and replies.
5. **Port scan (anomaly)** -- One source IP sends SYN packets to 50+ ports.
6. **Traffic spike (anomaly)** -- A burst of 200 packets in a short window.
7. **Suspicious DNS (anomaly)** -- Queries with high-entropy and long labels.

Requires Scapy::

    pip install scapy
    python samples/generate_sample_pcap.py --output samples/demo.pcap --count 500

WARNING: This script generates synthetic traffic only. Do not use it to
inject traffic onto real networks.
"""

import argparse
import os
import random
import string
import sys
import time

try:
    from scapy.all import (
        Ether, IP, TCP, UDP, ICMP, DNS, DNSQR, Raw,
        wrpcap, RandShort,
    )
except ImportError:
    print(
        "ERROR: Scapy is required to generate sample PCAPs.\n"
        "Install it with: pip install scapy",
        file=sys.stderr,
    )
    sys.exit(1)


# ===================================================================
# Configuration
# ===================================================================

# "Normal" IPs in our simulated network
INTERNAL_IPS = [
    "192.168.1.10", "192.168.1.11", "192.168.1.20",
    "192.168.1.30", "192.168.1.40", "192.168.1.50",
]

EXTERNAL_IPS = [
    "8.8.8.8", "1.1.1.1", "93.184.216.34",  # example.com
    "151.101.1.69", "104.16.132.229", "172.217.14.206",
    "13.107.42.14", "52.84.125.42",
]

DNS_SERVER = "8.8.8.8"

NORMAL_DOMAINS = [
    "www.example.com", "api.github.com", "docs.python.org",
    "cdn.jsdelivr.net", "fonts.googleapis.com", "registry.npmjs.org",
    "security.stackexchange.com", "news.ycombinator.com",
    "pkg.go.dev", "crates.io",
]

# Anomaly parameters
SCANNER_IP = "10.0.0.99"
SPIKE_SRC = "192.168.1.200"
SPIKE_DST = "93.184.216.34"


# ===================================================================
# Packet generators
# ===================================================================

def _random_payload(min_len: int = 20, max_len: int = 500) -> bytes:
    """Generate a random payload of variable length."""
    length = random.randint(min_len, max_len)
    return bytes(random.getrandbits(8) for _ in range(length))


def _random_string(length: int) -> str:
    """Random lowercase + digit string."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_normal_http(base_time: float, count: int) -> list:
    """Generate TCP packets to port 80 (HTTP) and 443 (HTTPS)."""
    packets = []
    for i in range(count):
        src = random.choice(INTERNAL_IPS)
        dst = random.choice(EXTERNAL_IPS)
        sport = random.randint(49152, 65535)
        dport = random.choice([80, 80, 443, 443, 443, 8080])
        ts = base_time + i * random.uniform(0.01, 0.5)

        # SYN
        syn = (
            IP(src=src, dst=dst) /
            TCP(sport=sport, dport=dport, flags="S", seq=1000)
        )
        syn.time = ts
        packets.append(syn)

        # SYN-ACK
        synack = (
            IP(src=dst, dst=src) /
            TCP(sport=dport, dport=sport, flags="SA", seq=2000, ack=1001)
        )
        synack.time = ts + 0.005
        packets.append(synack)

        # ACK + data
        ack = (
            IP(src=src, dst=dst) /
            TCP(sport=sport, dport=dport, flags="PA", seq=1001, ack=2001) /
            Raw(load=_random_payload(50, 300))
        )
        ack.time = ts + 0.01
        packets.append(ack)

    return packets


def generate_normal_dns(base_time: float, count: int) -> list:
    """Generate DNS query packets."""
    packets = []
    for i in range(count):
        src = random.choice(INTERNAL_IPS)
        domain = random.choice(NORMAL_DOMAINS)
        ts = base_time + i * random.uniform(0.05, 1.0)

        query = (
            IP(src=src, dst=DNS_SERVER) /
            UDP(sport=random.randint(49152, 65535), dport=53) /
            DNS(rd=1, qd=DNSQR(qname=domain))
        )
        query.time = ts
        packets.append(query)

    return packets


def generate_normal_ssh(base_time: float, count: int) -> list:
    """Generate TCP packets to port 22 (SSH)."""
    packets = []
    for i in range(count):
        src = random.choice(INTERNAL_IPS)
        dst = random.choice(EXTERNAL_IPS[:3])
        sport = random.randint(49152, 65535)
        ts = base_time + i * random.uniform(0.1, 2.0)

        syn = IP(src=src, dst=dst) / TCP(sport=sport, dport=22, flags="S")
        syn.time = ts
        packets.append(syn)

        synack = IP(src=dst, dst=src) / TCP(sport=22, dport=sport, flags="SA")
        synack.time = ts + 0.008
        packets.append(synack)

        data = (
            IP(src=src, dst=dst) /
            TCP(sport=sport, dport=22, flags="PA") /
            Raw(load=_random_payload(64, 256))
        )
        data.time = ts + 0.02
        packets.append(data)

    return packets


def generate_icmp(base_time: float, count: int) -> list:
    """Generate ICMP echo request / reply pairs."""
    packets = []
    for i in range(count):
        src = random.choice(INTERNAL_IPS)
        dst = random.choice(EXTERNAL_IPS)
        ts = base_time + i * random.uniform(0.5, 2.0)

        echo_req = IP(src=src, dst=dst) / ICMP(type=8, code=0) / Raw(load=b"\x00" * 32)
        echo_req.time = ts
        packets.append(echo_req)

        echo_reply = IP(src=dst, dst=src) / ICMP(type=0, code=0) / Raw(load=b"\x00" * 32)
        echo_reply.time = ts + 0.015
        packets.append(echo_reply)

    return packets


# ===================================================================
# Anomaly generators
# ===================================================================

def generate_port_scan(base_time: float, num_ports: int = 50) -> list:
    """
    Generate a SYN scan from SCANNER_IP to a single target across
    *num_ports* distinct destination ports.
    """
    packets = []
    target = random.choice(EXTERNAL_IPS)
    ports = random.sample(range(1, 65535), num_ports)

    for i, port in enumerate(ports):
        ts = base_time + i * random.uniform(0.001, 0.01)
        syn = (
            IP(src=SCANNER_IP, dst=target) /
            TCP(sport=random.randint(49152, 65535), dport=port, flags="S")
        )
        syn.time = ts
        packets.append(syn)

    return packets


def generate_traffic_spike(base_time: float, burst_count: int = 200) -> list:
    """
    Generate a burst of *burst_count* packets in a very short time window
    to simulate a traffic spike.
    """
    packets = []
    for i in range(burst_count):
        ts = base_time + i * 0.001  # 1 ms apart -> 200 packets in 0.2 s
        pkt = (
            IP(src=SPIKE_SRC, dst=SPIKE_DST) /
            TCP(
                sport=random.randint(49152, 65535),
                dport=80,
                flags="PA",
            ) /
            Raw(load=_random_payload(100, 1000))
        )
        pkt.time = ts
        packets.append(pkt)

    return packets


def generate_suspicious_dns(base_time: float, count: int = 10) -> list:
    """
    Generate DNS queries with high-entropy labels and suspicious TLDs
    to simulate DGA / DNS tunneling.
    """
    suspicious_tlds = ["xyz", "top", "club", "zip", "click"]
    packets = []

    for i in range(count):
        # Generate a random, high-entropy subdomain
        label_len = random.randint(20, 50)
        label = _random_string(label_len)
        tld = random.choice(suspicious_tlds)
        domain = f"{label}.{_random_string(8)}.{tld}"

        src = random.choice(INTERNAL_IPS)
        ts = base_time + i * random.uniform(0.1, 0.5)

        query = (
            IP(src=src, dst=DNS_SERVER) /
            UDP(sport=random.randint(49152, 65535), dport=53) /
            DNS(rd=1, qd=DNSQR(qname=domain))
        )
        query.time = ts
        packets.append(query)

    return packets


# ===================================================================
# Main generator
# ===================================================================

def generate_sample_pcap(
    output_path: str,
    total_normal: int = 300,
    seed: int = 42,
) -> int:
    """
    Generate a synthetic PCAP file with normal + anomalous traffic.

    Parameters
    ----------
    output_path : str
        Where to write the PCAP file.
    total_normal : int
        Approximate number of normal traffic packets to generate.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    int
        Total number of packets written.
    """
    random.seed(seed)
    base_time = 1700000000.0  # Arbitrary epoch

    all_packets = []

    # --- Normal traffic ---
    http_count = int(total_normal * 0.40)
    dns_count = int(total_normal * 0.20)
    ssh_count = int(total_normal * 0.15)
    icmp_count = int(total_normal * 0.10)

    all_packets.extend(generate_normal_http(base_time, http_count))
    all_packets.extend(generate_normal_dns(base_time + 5, dns_count))
    all_packets.extend(generate_normal_ssh(base_time + 10, ssh_count))
    all_packets.extend(generate_icmp(base_time + 15, icmp_count))

    # --- Anomalous traffic ---
    # Port scan starting at base_time + 100
    all_packets.extend(generate_port_scan(base_time + 100, num_ports=50))

    # Traffic spike at base_time + 200
    all_packets.extend(generate_traffic_spike(base_time + 200, burst_count=200))

    # Suspicious DNS at base_time + 300
    all_packets.extend(generate_suspicious_dns(base_time + 300, count=15))

    # Sort all packets by timestamp
    all_packets.sort(key=lambda p: float(p.time))

    # Write PCAP
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    wrpcap(output_path, all_packets)

    return len(all_packets)


# ===================================================================
# CLI entry point
# ===================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate a synthetic PCAP file with normal + anomalous traffic."
    )
    parser.add_argument(
        "--output", "-o",
        default="samples/demo.pcap",
        help="Output PCAP file path (default: samples/demo.pcap).",
    )
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=300,
        help="Approximate number of normal-traffic packets (default: 300).",
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )

    args = parser.parse_args()

    print(f"[*] Generating synthetic PCAP: {args.output}")
    print(f"    Normal packets: ~{args.count}, Seed: {args.seed}")

    total = generate_sample_pcap(args.output, total_normal=args.count, seed=args.seed)

    print(f"[+] Wrote {total} packets to {args.output}")
    print(f"    File size: {os.path.getsize(args.output):,} bytes")
    print()
    print("Traffic breakdown:")
    print(f"  Normal HTTP/HTTPS : ~{int(args.count * 0.40) * 3} packets (3 per connection)")
    print(f"  Normal DNS        : ~{int(args.count * 0.20)} packets")
    print(f"  Normal SSH        : ~{int(args.count * 0.15) * 3} packets")
    print(f"  ICMP echo         : ~{int(args.count * 0.10) * 2} packets")
    print(f"  Port scan         :  50 SYN packets from {SCANNER_IP}")
    print(f"  Traffic spike     : 200 burst packets from {SPIKE_SRC}")
    print(f"  Suspicious DNS    :  15 high-entropy queries")


if __name__ == "__main__":
    main()
