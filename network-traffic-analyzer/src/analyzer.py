"""
Traffic Analyzer Module
=======================

Performs statistical analysis on parsed packet data. Computes protocol
distribution, top source/destination IPs, port frequency tables, and
per-IP bandwidth estimates.

All public functions accept the list-of-dicts format returned by
``src.parser.parse_pcap``.

WARNING: Only analyze captures from networks you own or have explicit
authorization to monitor.
"""

from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime, timezone


# ===================================================================
# Protocol Distribution
# ===================================================================

def protocol_distribution(packets: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count packets per protocol.

    Parameters
    ----------
    packets : list[dict]
        Parsed packet metadata.

    Returns
    -------
    dict[str, int]
        Protocol name -> packet count, sorted descending by count.
    """
    counter = Counter(pkt.get("protocol", "UNKNOWN") for pkt in packets)
    return dict(counter.most_common())


def protocol_distribution_pct(packets: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Protocol distribution as percentages (0-100).

    Returns
    -------
    dict[str, float]
        Protocol name -> percentage of total packets.
    """
    dist = protocol_distribution(packets)
    total = sum(dist.values()) or 1
    return {proto: round(count / total * 100, 2) for proto, count in dist.items()}


# ===================================================================
# Top Source / Destination IPs
# ===================================================================

def top_source_ips(
    packets: List[Dict[str, Any]], limit: int = 10
) -> List[Tuple[str, int]]:
    """
    Return the most frequent source IP addresses.

    Parameters
    ----------
    packets : list[dict]
    limit : int
        Maximum number of results.

    Returns
    -------
    list[tuple[str, int]]
        (ip_address, packet_count) pairs sorted descending.
    """
    counter = Counter(
        pkt["src_ip"] for pkt in packets if pkt.get("src_ip") is not None
    )
    return counter.most_common(limit)


def top_dest_ips(
    packets: List[Dict[str, Any]], limit: int = 10
) -> List[Tuple[str, int]]:
    """
    Return the most frequent destination IP addresses.
    """
    counter = Counter(
        pkt["dst_ip"] for pkt in packets if pkt.get("dst_ip") is not None
    )
    return counter.most_common(limit)


def top_talkers(
    packets: List[Dict[str, Any]], limit: int = 10
) -> List[Tuple[str, int]]:
    """
    Top talkers: IPs ranked by total packets sent *or* received.

    An IP's count is the sum of packets where it appears as source **or**
    destination.
    """
    counter: Counter = Counter()
    for pkt in packets:
        src = pkt.get("src_ip")
        dst = pkt.get("dst_ip")
        if src:
            counter[src] += 1
        if dst:
            counter[dst] += 1
    return counter.most_common(limit)


# ===================================================================
# Port Frequency
# ===================================================================

def destination_port_frequency(
    packets: List[Dict[str, Any]], limit: int = 20
) -> List[Tuple[int, int]]:
    """
    Most frequently targeted destination ports across all packets.

    Returns
    -------
    list[tuple[int, int]]
        (port_number, count) sorted descending.
    """
    counter = Counter(
        pkt["dst_port"]
        for pkt in packets
        if pkt.get("dst_port") is not None
    )
    return counter.most_common(limit)


def source_port_frequency(
    packets: List[Dict[str, Any]], limit: int = 20
) -> List[Tuple[int, int]]:
    """Most frequently used source ports."""
    counter = Counter(
        pkt["src_port"]
        for pkt in packets
        if pkt.get("src_port") is not None
    )
    return counter.most_common(limit)


def port_protocol_matrix(
    packets: List[Dict[str, Any]],
) -> Dict[int, Dict[str, int]]:
    """
    Build a matrix of destination_port -> {protocol -> count}.

    Useful for identifying which services are running on which ports.
    """
    matrix: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for pkt in packets:
        port = pkt.get("dst_port")
        proto = pkt.get("protocol", "UNKNOWN")
        if port is not None:
            matrix[port][proto] += 1
    # Convert inner defaultdicts to plain dicts for serialization
    return {port: dict(protos) for port, protos in matrix.items()}


# ===================================================================
# Bandwidth per IP
# ===================================================================

def bandwidth_per_ip(
    packets: List[Dict[str, Any]], direction: str = "src"
) -> Dict[str, int]:
    """
    Total bytes transferred per IP address.

    Parameters
    ----------
    packets : list[dict]
    direction : str
        ``"src"`` to aggregate by source IP, ``"dst"`` for destination,
        ``"both"`` for combined.

    Returns
    -------
    dict[str, int]
        IP address -> total bytes, sorted descending.
    """
    totals: Counter = Counter()

    for pkt in packets:
        size = pkt.get("size", 0)
        if direction in ("src", "both"):
            ip = pkt.get("src_ip")
            if ip:
                totals[ip] += size
        if direction in ("dst", "both"):
            ip = pkt.get("dst_ip")
            if ip:
                totals[ip] += size

    return dict(totals.most_common())


def bandwidth_summary(packets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    High-level bandwidth statistics for the entire capture.

    Returns
    -------
    dict
        Keys: total_bytes, total_packets, avg_packet_size,
        duration_seconds, avg_bytes_per_second, avg_packets_per_second.
    """
    if not packets:
        return {
            "total_bytes": 0,
            "total_packets": 0,
            "avg_packet_size": 0.0,
            "duration_seconds": 0.0,
            "avg_bytes_per_second": 0.0,
            "avg_packets_per_second": 0.0,
        }

    total_bytes = sum(pkt.get("size", 0) for pkt in packets)
    total_packets = len(packets)
    timestamps = [pkt["timestamp"] for pkt in packets if "timestamp" in pkt]
    if len(timestamps) >= 2:
        duration = max(timestamps) - min(timestamps)
    else:
        duration = 0.0

    return {
        "total_bytes": total_bytes,
        "total_packets": total_packets,
        "avg_packet_size": round(total_bytes / total_packets, 2),
        "duration_seconds": round(duration, 3),
        "avg_bytes_per_second": round(total_bytes / duration, 2) if duration > 0 else 0.0,
        "avg_packets_per_second": round(total_packets / duration, 2) if duration > 0 else 0.0,
    }


# ===================================================================
# Conversation Pairs
# ===================================================================

def conversation_pairs(
    packets: List[Dict[str, Any]], limit: int = 10
) -> List[Tuple[Tuple[str, str], int]]:
    """
    Identify the most active IP-pair conversations (bidirectional).

    A pair (A, B) is the same as (B, A). Results are sorted by total
    packet count descending.
    """
    counter: Counter = Counter()
    for pkt in packets:
        src = pkt.get("src_ip")
        dst = pkt.get("dst_ip")
        if src and dst:
            pair = tuple(sorted([src, dst]))
            counter[pair] += 1
    return counter.most_common(limit)


# ===================================================================
# Time-series helpers
# ===================================================================

def packets_per_interval(
    packets: List[Dict[str, Any]], interval_seconds: int = 60
) -> List[Tuple[float, int]]:
    """
    Bucket packets into fixed time intervals and count packets per bucket.

    Parameters
    ----------
    packets : list[dict]
    interval_seconds : int
        Width of each time bucket in seconds.

    Returns
    -------
    list[tuple[float, int]]
        (bucket_start_timestamp, packet_count) pairs in chronological order.
    """
    if not packets:
        return []

    timestamps = sorted(pkt["timestamp"] for pkt in packets if "timestamp" in pkt)
    if not timestamps:
        return []

    start = timestamps[0]
    end = timestamps[-1]
    buckets: Dict[float, int] = {}

    t = start
    while t <= end + interval_seconds:
        buckets[t] = 0
        t += interval_seconds

    for ts in timestamps:
        bucket_start = start + ((ts - start) // interval_seconds) * interval_seconds
        buckets[bucket_start] = buckets.get(bucket_start, 0) + 1

    return sorted(buckets.items())


def bytes_per_interval(
    packets: List[Dict[str, Any]], interval_seconds: int = 60
) -> List[Tuple[float, int]]:
    """
    Bucket packets by time and sum total bytes per bucket.
    """
    if not packets:
        return []

    timestamps_sizes = sorted(
        (pkt["timestamp"], pkt.get("size", 0))
        for pkt in packets
        if "timestamp" in pkt
    )
    if not timestamps_sizes:
        return []

    start = timestamps_sizes[0][0]
    end = timestamps_sizes[-1][0]
    buckets: Dict[float, int] = {}

    t = start
    while t <= end + interval_seconds:
        buckets[t] = 0
        t += interval_seconds

    for ts, size in timestamps_sizes:
        bucket_start = start + ((ts - start) // interval_seconds) * interval_seconds
        buckets[bucket_start] = buckets.get(bucket_start, 0) + size

    return sorted(buckets.items())


# ===================================================================
# Full analysis convenience function
# ===================================================================

def full_analysis(
    packets: List[Dict[str, Any]],
    top_n: int = 10,
    interval: int = 60,
) -> Dict[str, Any]:
    """
    Run all analysis routines and return a consolidated results dict.

    Parameters
    ----------
    packets : list[dict]
        Parsed packet list from ``src.parser.parse_pcap``.
    top_n : int
        Number of results in top-N lists.
    interval : int
        Seconds per time bucket for time-series data.

    Returns
    -------
    dict
        All analysis results keyed by category name.
    """
    return {
        "summary": bandwidth_summary(packets),
        "protocol_distribution": protocol_distribution(packets),
        "protocol_distribution_pct": protocol_distribution_pct(packets),
        "top_source_ips": top_source_ips(packets, limit=top_n),
        "top_dest_ips": top_dest_ips(packets, limit=top_n),
        "top_talkers": top_talkers(packets, limit=top_n),
        "destination_port_frequency": destination_port_frequency(packets, limit=top_n * 2),
        "bandwidth_by_source": bandwidth_per_ip(packets, direction="src"),
        "bandwidth_by_dest": bandwidth_per_ip(packets, direction="dst"),
        "conversation_pairs": conversation_pairs(packets, limit=top_n),
        "packets_per_interval": packets_per_interval(packets, interval_seconds=interval),
        "bytes_per_interval": bytes_per_interval(packets, interval_seconds=interval),
    }
