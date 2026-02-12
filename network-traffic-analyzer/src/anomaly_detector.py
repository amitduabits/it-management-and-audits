"""
Anomaly Detection Module
=========================

Detects common network anomalies in parsed packet data:

- **Port scans**: A single source IP contacting many distinct destination ports.
- **Traffic spikes**: Time intervals where the packet rate far exceeds the mean.
- **Suspicious DNS queries**: Queries with high entropy, excessive length, or
  known-bad TLD patterns that may indicate tunneling or DGA activity.

Each detector returns a list of "finding" dictionaries with a consistent
schema so callers can aggregate, filter, and report them uniformly.

WARNING: Analyze only traffic you are authorized to inspect.
"""

import math
import statistics
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Set


# ===================================================================
# Finding severity levels
# ===================================================================

SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"
SEVERITY_CRITICAL = "critical"


def _make_finding(
    category: str,
    title: str,
    description: str,
    severity: str,
    evidence: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a standardized finding dictionary."""
    return {
        "category": category,
        "title": title,
        "description": description,
        "severity": severity,
        "evidence": evidence or {},
    }


# ===================================================================
# 1. Port Scan Detection
# ===================================================================

def detect_port_scans(
    packets: List[Dict[str, Any]],
    threshold: int = 15,
) -> List[Dict[str, Any]]:
    """
    Detect potential port scans.

    A port scan is flagged when a single source IP contacts more than
    *threshold* distinct destination ports.  SYN-only scans (SYN flag
    set, no ACK) are weighted more heavily.

    Parameters
    ----------
    packets : list[dict]
    threshold : int
        Minimum unique destination ports from one source to trigger a finding.

    Returns
    -------
    list[dict]
        Findings with category ``"port_scan"``.
    """
    # Map: src_ip -> set of dst_ports
    ip_ports: Dict[str, Set[int]] = defaultdict(set)
    # Track SYN-only packets per source (strong scan indicator)
    syn_only: Dict[str, int] = Counter()

    for pkt in packets:
        src = pkt.get("src_ip")
        dst_port = pkt.get("dst_port")
        if src is None or dst_port is None:
            continue
        ip_ports[src].add(dst_port)

        tcp_flags = pkt.get("info", {}).get("tcp_flags", "")
        if "S" in tcp_flags and "A" not in tcp_flags:
            syn_only[src] += 1

    findings: List[Dict[str, Any]] = []
    for ip, ports in ip_ports.items():
        num_ports = len(ports)
        if num_ports < threshold:
            continue

        # Determine severity based on port count and SYN behavior
        syn_count = syn_only.get(ip, 0)
        if num_ports > threshold * 5 or syn_count > threshold * 3:
            severity = SEVERITY_CRITICAL
        elif num_ports > threshold * 3:
            severity = SEVERITY_HIGH
        elif num_ports > threshold * 1.5:
            severity = SEVERITY_MEDIUM
        else:
            severity = SEVERITY_LOW

        sorted_ports = sorted(ports)
        sample_ports = sorted_ports[:25]

        findings.append(
            _make_finding(
                category="port_scan",
                title=f"Potential port scan from {ip}",
                description=(
                    f"Source IP {ip} contacted {num_ports} distinct destination "
                    f"ports (threshold: {threshold}). SYN-only packets: {syn_count}."
                ),
                severity=severity,
                evidence={
                    "source_ip": ip,
                    "unique_ports": num_ports,
                    "syn_only_packets": syn_count,
                    "sample_ports": sample_ports,
                    "threshold": threshold,
                },
            )
        )

    # Sort by unique_ports descending so the most aggressive scans appear first
    findings.sort(key=lambda f: f["evidence"]["unique_ports"], reverse=True)
    return findings


# ===================================================================
# 2. Traffic Spike Detection
# ===================================================================

def detect_traffic_spikes(
    packets: List[Dict[str, Any]],
    time_window: int = 60,
    spike_factor: float = 3.0,
) -> List[Dict[str, Any]]:
    """
    Detect time intervals with abnormally high packet rates.

    The capture is divided into fixed *time_window*-second buckets. Any
    bucket whose packet count exceeds ``mean + spike_factor * stdev`` is
    flagged.

    Parameters
    ----------
    packets : list[dict]
    time_window : int
        Bucket width in seconds.
    spike_factor : float
        Standard deviations above the mean to consider a spike.

    Returns
    -------
    list[dict]
        Findings with category ``"traffic_spike"``.
    """
    if not packets:
        return []

    timestamps = sorted(pkt["timestamp"] for pkt in packets if "timestamp" in pkt)
    if len(timestamps) < 2:
        return []

    start = timestamps[0]

    # Bucket packets
    buckets: Dict[int, int] = Counter()
    for ts in timestamps:
        bucket_idx = int((ts - start) // time_window)
        buckets[bucket_idx] += 1

    # Fill empty buckets with zero to get an accurate mean/stdev
    max_bucket = max(buckets.keys())
    counts = [buckets.get(i, 0) for i in range(max_bucket + 1)]

    if len(counts) < 3:
        return []

    mean = statistics.mean(counts)
    stdev = statistics.stdev(counts) if len(counts) > 1 else 0.0
    spike_threshold = mean + spike_factor * stdev

    if spike_threshold <= 0:
        return []

    findings: List[Dict[str, Any]] = []
    for idx, count in enumerate(counts):
        if count <= spike_threshold:
            continue

        bucket_start_ts = start + idx * time_window
        ratio = round(count / mean, 2) if mean > 0 else float("inf")

        if ratio > spike_factor * 3:
            severity = SEVERITY_CRITICAL
        elif ratio > spike_factor * 2:
            severity = SEVERITY_HIGH
        elif ratio > spike_factor:
            severity = SEVERITY_MEDIUM
        else:
            severity = SEVERITY_LOW

        findings.append(
            _make_finding(
                category="traffic_spike",
                title=f"Traffic spike at bucket {idx}",
                description=(
                    f"Bucket starting at t+{idx * time_window}s contains "
                    f"{count} packets ({ratio}x the mean of {mean:.1f}). "
                    f"Threshold was {spike_threshold:.1f}."
                ),
                severity=severity,
                evidence={
                    "bucket_index": idx,
                    "bucket_start_timestamp": bucket_start_ts,
                    "packet_count": count,
                    "mean": round(mean, 2),
                    "stdev": round(stdev, 2),
                    "ratio_to_mean": ratio,
                    "time_window": time_window,
                    "spike_factor": spike_factor,
                },
            )
        )

    findings.sort(key=lambda f: f["evidence"]["ratio_to_mean"], reverse=True)
    return findings


# ===================================================================
# 3. Suspicious DNS Queries
# ===================================================================

# TLDs sometimes associated with disposable / malicious domains
_SUSPICIOUS_TLDS: Set[str] = {
    "xyz", "top", "club", "work", "date", "racing", "win", "bid",
    "stream", "download", "gdn", "loan", "men", "click", "link",
    "trade", "accountant", "science", "cricket", "faith", "review",
    "party", "zip", "mov",
}


def _shannon_entropy(s: str) -> float:
    """Calculate the Shannon entropy of a string."""
    if not s:
        return 0.0
    length = len(s)
    freq = Counter(s)
    return -sum(
        (count / length) * math.log2(count / length)
        for count in freq.values()
    )


def _label_max_length(domain: str) -> int:
    """Return the length of the longest label in a domain name."""
    labels = domain.split(".")
    return max((len(lbl) for lbl in labels), default=0)


def detect_suspicious_dns(
    packets: List[Dict[str, Any]],
    entropy_threshold: float = 4.0,
    length_threshold: int = 50,
    label_length_threshold: int = 32,
) -> List[Dict[str, Any]]:
    """
    Flag DNS queries that may indicate tunneling, DGA, or data exfiltration.

    Heuristics
    ----------
    - **High entropy**: The query name has Shannon entropy above
      *entropy_threshold*, suggesting randomly generated labels (DGA).
    - **Excessive length**: Total query length exceeds *length_threshold*
      characters (potential data exfiltration via DNS tunneling).
    - **Long labels**: Any single label exceeds *label_length_threshold*
      characters.
    - **Suspicious TLD**: The effective TLD is in a watchlist of TLDs
      commonly abused by threat actors.

    Parameters
    ----------
    packets : list[dict]
    entropy_threshold : float
    length_threshold : int
    label_length_threshold : int

    Returns
    -------
    list[dict]
        Findings with category ``"suspicious_dns"``.
    """
    findings: List[Dict[str, Any]] = []
    seen_queries: Set[str] = set()

    for pkt in packets:
        info = pkt.get("info", {})
        query = info.get("dns_query")
        if not query or query in seen_queries:
            continue
        seen_queries.add(query)

        reasons: List[str] = []
        query_lower = query.lower().rstrip(".")
        labels = query_lower.split(".")

        # --- Entropy check ---
        # Compute entropy on the part before the effective TLD
        base = ".".join(labels[:-1]) if len(labels) > 1 else query_lower
        entropy = _shannon_entropy(base)
        if entropy > entropy_threshold:
            reasons.append(f"high entropy ({entropy:.2f} > {entropy_threshold})")

        # --- Length check ---
        if len(query_lower) > length_threshold:
            reasons.append(f"excessive length ({len(query_lower)} chars)")

        # --- Label length check ---
        max_lbl = _label_max_length(query_lower)
        if max_lbl > label_length_threshold:
            reasons.append(f"long label ({max_lbl} chars)")

        # --- Suspicious TLD ---
        tld = labels[-1] if labels else ""
        if tld in _SUSPICIOUS_TLDS:
            reasons.append(f"suspicious TLD (.{tld})")

        if not reasons:
            continue

        if len(reasons) >= 3:
            severity = SEVERITY_HIGH
        elif len(reasons) == 2:
            severity = SEVERITY_MEDIUM
        else:
            severity = SEVERITY_LOW

        findings.append(
            _make_finding(
                category="suspicious_dns",
                title=f"Suspicious DNS query: {query_lower}",
                description=(
                    f"DNS query \"{query_lower}\" flagged for: "
                    + "; ".join(reasons) + "."
                ),
                severity=severity,
                evidence={
                    "query": query_lower,
                    "entropy": round(entropy, 2),
                    "length": len(query_lower),
                    "max_label_length": max_lbl,
                    "tld": tld,
                    "reasons": reasons,
                    "source_ip": pkt.get("src_ip"),
                    "dest_ip": pkt.get("dst_ip"),
                },
            )
        )

    findings.sort(
        key=lambda f: len(f["evidence"]["reasons"]), reverse=True
    )
    return findings


# ===================================================================
# 4. Additional heuristic: unusual ICMP volume
# ===================================================================

def detect_icmp_flood(
    packets: List[Dict[str, Any]],
    threshold_pct: float = 25.0,
    min_packets: int = 50,
) -> List[Dict[str, Any]]:
    """
    Flag captures where ICMP traffic exceeds *threshold_pct* percent of
    all packets, which may indicate an ICMP flood or covert channel.

    Parameters
    ----------
    packets : list[dict]
    threshold_pct : float
        Percentage threshold (0-100).
    min_packets : int
        Minimum total packets to evaluate (avoids false positives on tiny captures).

    Returns
    -------
    list[dict]
        Findings with category ``"icmp_flood"``.
    """
    if len(packets) < min_packets:
        return []

    icmp_count = sum(
        1 for pkt in packets if pkt.get("protocol", "").upper() == "ICMP"
    )
    pct = (icmp_count / len(packets)) * 100

    if pct < threshold_pct:
        return []

    # Identify the top ICMP sources
    icmp_sources = Counter(
        pkt["src_ip"]
        for pkt in packets
        if pkt.get("protocol", "").upper() == "ICMP" and pkt.get("src_ip")
    )

    severity = SEVERITY_HIGH if pct > 50 else SEVERITY_MEDIUM

    return [
        _make_finding(
            category="icmp_flood",
            title="Unusually high ICMP traffic volume",
            description=(
                f"ICMP accounts for {pct:.1f}% of all packets "
                f"({icmp_count}/{len(packets)}), exceeding the {threshold_pct}% threshold."
            ),
            severity=severity,
            evidence={
                "icmp_count": icmp_count,
                "total_packets": len(packets),
                "percentage": round(pct, 2),
                "threshold_pct": threshold_pct,
                "top_sources": icmp_sources.most_common(5),
            },
        )
    ]


# ===================================================================
# 5. ARP anomaly detection (gratuitous ARP / ARP storm)
# ===================================================================

def detect_arp_anomalies(
    packets: List[Dict[str, Any]],
    storm_threshold: int = 100,
) -> List[Dict[str, Any]]:
    """
    Detect unusually high volumes of ARP-like traffic (protocol ``ARP``
    or ethertype 0x0806 captured by the fallback parser as
    ``ETHER(0x0806)``).

    Parameters
    ----------
    packets : list[dict]
    storm_threshold : int
        Minimum ARP packets to flag as a storm.

    Returns
    -------
    list[dict]
        Findings with category ``"arp_anomaly"``.
    """
    arp_count = sum(
        1
        for pkt in packets
        if "ARP" in pkt.get("protocol", "").upper()
        or pkt.get("protocol", "") == "ETHER(0x0806)"
    )

    if arp_count < storm_threshold:
        return []

    return [
        _make_finding(
            category="arp_anomaly",
            title="Possible ARP storm or spoofing",
            description=(
                f"Detected {arp_count} ARP packets in the capture "
                f"(threshold: {storm_threshold})."
            ),
            severity=SEVERITY_MEDIUM,
            evidence={
                "arp_count": arp_count,
                "storm_threshold": storm_threshold,
            },
        )
    ]


# ===================================================================
# Aggregate runner
# ===================================================================

def run_all_detectors(
    packets: List[Dict[str, Any]],
    port_scan_threshold: int = 15,
    spike_factor: float = 3.0,
    time_window: int = 60,
    dns_entropy_threshold: float = 4.0,
) -> List[Dict[str, Any]]:
    """
    Execute every anomaly detector and return a combined findings list.

    Parameters
    ----------
    packets : list[dict]
    port_scan_threshold : int
    spike_factor : float
    time_window : int
    dns_entropy_threshold : float

    Returns
    -------
    list[dict]
        Combined and severity-sorted findings from all detectors.
    """
    all_findings: List[Dict[str, Any]] = []

    all_findings.extend(detect_port_scans(packets, threshold=port_scan_threshold))
    all_findings.extend(
        detect_traffic_spikes(packets, time_window=time_window, spike_factor=spike_factor)
    )
    all_findings.extend(
        detect_suspicious_dns(packets, entropy_threshold=dns_entropy_threshold)
    )
    all_findings.extend(detect_icmp_flood(packets))
    all_findings.extend(detect_arp_anomalies(packets))

    # Sort: critical first, then high, medium, low
    severity_order = {
        SEVERITY_CRITICAL: 0,
        SEVERITY_HIGH: 1,
        SEVERITY_MEDIUM: 2,
        SEVERITY_LOW: 3,
    }
    all_findings.sort(key=lambda f: severity_order.get(f["severity"], 99))

    return all_findings


def summarize_findings(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Return a summary of findings grouped by category and severity.

    Returns
    -------
    dict
        Keys: total, by_severity, by_category.
    """
    by_severity: Dict[str, int] = Counter()
    by_category: Dict[str, int] = Counter()

    for f in findings:
        by_severity[f["severity"]] += 1
        by_category[f["category"]] += 1

    return {
        "total": len(findings),
        "by_severity": dict(by_severity),
        "by_category": dict(by_category),
    }
