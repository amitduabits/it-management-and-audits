"""
Unit Tests for src.anomaly_detector
=====================================

Tests cover:
- Port scan detection with various thresholds
- Traffic spike detection across time buckets
- Suspicious DNS query detection (entropy, length, TLDs)
- ICMP flood detection
- ARP anomaly detection
- The aggregate run_all_detectors function
- Finding structure validation
- Edge cases: empty packets, single packet, no anomalies
"""

import unittest
from typing import Any, Dict, List

from src.anomaly_detector import (
    detect_port_scans,
    detect_traffic_spikes,
    detect_suspicious_dns,
    detect_icmp_flood,
    detect_arp_anomalies,
    run_all_detectors,
    summarize_findings,
    _shannon_entropy,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_HIGH,
    SEVERITY_CRITICAL,
)


# ===================================================================
# Helpers: build synthetic packet lists
# ===================================================================

def _make_packet(
    src_ip: str = "192.168.1.10",
    dst_ip: str = "10.0.0.1",
    protocol: str = "TCP",
    src_port: int = 12345,
    dst_port: int = 80,
    timestamp: float = 1700000000.0,
    size: int = 100,
    info: dict = None,
) -> Dict[str, Any]:
    """Create a minimal packet dict."""
    return {
        "timestamp": timestamp,
        "datetime": "2023-11-14T22:13:20+00:00",
        "size": size,
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "protocol": protocol,
        "src_port": src_port,
        "dst_port": dst_port,
        "info": info or {},
    }


def _make_port_scan_packets(
    scanner_ip: str = "10.0.0.99",
    target_ip: str = "192.168.1.1",
    num_ports: int = 50,
    base_time: float = 1700000000.0,
) -> List[Dict[str, Any]]:
    """Generate packets simulating a port scan."""
    packets = []
    for i in range(num_ports):
        packets.append(_make_packet(
            src_ip=scanner_ip,
            dst_ip=target_ip,
            dst_port=i + 1,
            timestamp=base_time + i * 0.01,
            info={"tcp_flags": "S"},
        ))
    return packets


def _make_spike_packets(
    src_ip: str = "192.168.1.200",
    dst_ip: str = "10.0.0.1",
    normal_count: int = 50,
    spike_count: int = 200,
    normal_interval: float = 2.0,
    spike_start: float = 1700000200.0,
) -> List[Dict[str, Any]]:
    """Generate normal traffic with a spike in one bucket."""
    packets = []
    base = 1700000000.0

    # Normal traffic spread over many buckets
    for i in range(normal_count):
        packets.append(_make_packet(
            src_ip=src_ip,
            dst_ip=dst_ip,
            timestamp=base + i * normal_interval,
        ))

    # Spike: many packets in a single bucket
    for i in range(spike_count):
        packets.append(_make_packet(
            src_ip=src_ip,
            dst_ip=dst_ip,
            timestamp=spike_start + i * 0.001,
        ))

    return packets


def _make_dns_packet(
    query: str,
    src_ip: str = "192.168.1.10",
    timestamp: float = 1700000000.0,
) -> Dict[str, Any]:
    """Create a DNS query packet dict."""
    return _make_packet(
        src_ip=src_ip,
        dst_ip="8.8.8.8",
        protocol="DNS",
        src_port=54321,
        dst_port=53,
        timestamp=timestamp,
        info={"dns_query": query},
    )


# ===================================================================
# Test cases
# ===================================================================

class TestShannonEntropy(unittest.TestCase):
    """Test the entropy calculation helper."""

    def test_empty_string(self):
        self.assertEqual(_shannon_entropy(""), 0.0)

    def test_single_char(self):
        self.assertEqual(_shannon_entropy("a"), 0.0)

    def test_uniform_distribution(self):
        # "ab" has 2 equally likely chars -> entropy = 1.0
        self.assertAlmostEqual(_shannon_entropy("ab"), 1.0)

    def test_repeated_chars(self):
        # All same chars -> entropy = 0
        self.assertEqual(_shannon_entropy("aaaa"), 0.0)

    def test_high_entropy(self):
        # Random-looking string should have high entropy
        s = "a1b2c3d4e5f6g7h8"
        self.assertGreater(_shannon_entropy(s), 3.0)


class TestPortScanDetection(unittest.TestCase):
    """Test port scan detection."""

    def test_scan_above_threshold(self):
        packets = _make_port_scan_packets(num_ports=50)
        findings = detect_port_scans(packets, threshold=15)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["category"], "port_scan")
        self.assertEqual(findings[0]["evidence"]["source_ip"], "10.0.0.99")
        self.assertEqual(findings[0]["evidence"]["unique_ports"], 50)

    def test_scan_below_threshold(self):
        packets = _make_port_scan_packets(num_ports=10)
        findings = detect_port_scans(packets, threshold=15)
        self.assertEqual(len(findings), 0)

    def test_scan_exactly_at_threshold(self):
        packets = _make_port_scan_packets(num_ports=15)
        findings = detect_port_scans(packets, threshold=15)
        self.assertEqual(len(findings), 1)

    def test_multiple_scanners(self):
        packets = (
            _make_port_scan_packets("10.0.0.1", num_ports=20) +
            _make_port_scan_packets("10.0.0.2", num_ports=30)
        )
        findings = detect_port_scans(packets, threshold=15)
        self.assertEqual(len(findings), 2)
        # Should be sorted by unique_ports descending
        self.assertGreaterEqual(
            findings[0]["evidence"]["unique_ports"],
            findings[1]["evidence"]["unique_ports"],
        )

    def test_syn_only_tracking(self):
        packets = _make_port_scan_packets(num_ports=20)
        findings = detect_port_scans(packets, threshold=15)
        self.assertGreater(findings[0]["evidence"]["syn_only_packets"], 0)

    def test_severity_escalation(self):
        # 100 ports should be higher severity than 16
        packets_low = _make_port_scan_packets(num_ports=16)
        packets_high = _make_port_scan_packets(num_ports=100)

        findings_low = detect_port_scans(packets_low, threshold=15)
        findings_high = detect_port_scans(packets_high, threshold=15)

        severity_order = [SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL]
        idx_low = severity_order.index(findings_low[0]["severity"])
        idx_high = severity_order.index(findings_high[0]["severity"])
        self.assertGreaterEqual(idx_high, idx_low)

    def test_no_packets(self):
        findings = detect_port_scans([], threshold=15)
        self.assertEqual(findings, [])

    def test_packets_without_ports(self):
        packets = [_make_packet(dst_port=None, src_port=None, protocol="ICMP")]
        findings = detect_port_scans(packets, threshold=1)
        self.assertEqual(findings, [])


class TestTrafficSpikeDetection(unittest.TestCase):
    """Test traffic spike detection."""

    def test_spike_detected(self):
        packets = _make_spike_packets(
            normal_count=50,
            spike_count=200,
        )
        findings = detect_traffic_spikes(packets, time_window=60, spike_factor=2.0)
        self.assertGreater(len(findings), 0)
        self.assertEqual(findings[0]["category"], "traffic_spike")

    def test_no_spike_with_uniform_traffic(self):
        # All packets evenly distributed
        packets = [
            _make_packet(timestamp=1700000000.0 + i * 1.0)
            for i in range(100)
        ]
        findings = detect_traffic_spikes(packets, time_window=60, spike_factor=3.0)
        self.assertEqual(len(findings), 0)

    def test_empty_packets(self):
        findings = detect_traffic_spikes([], time_window=60, spike_factor=3.0)
        self.assertEqual(findings, [])

    def test_single_packet(self):
        packets = [_make_packet()]
        findings = detect_traffic_spikes(packets, time_window=60, spike_factor=3.0)
        self.assertEqual(findings, [])

    def test_ratio_in_evidence(self):
        packets = _make_spike_packets(normal_count=30, spike_count=300)
        findings = detect_traffic_spikes(packets, time_window=60, spike_factor=2.0)
        if findings:
            self.assertIn("ratio_to_mean", findings[0]["evidence"])
            self.assertGreater(findings[0]["evidence"]["ratio_to_mean"], 1.0)

    def test_high_spike_factor_suppresses(self):
        packets = _make_spike_packets(normal_count=50, spike_count=60)
        findings = detect_traffic_spikes(packets, time_window=60, spike_factor=100.0)
        self.assertEqual(len(findings), 0)


class TestSuspiciousDNS(unittest.TestCase):
    """Test suspicious DNS query detection."""

    def test_high_entropy_query(self):
        # Random-looking domain
        query = "a1b2c3d4e5f6g7h8i9j0.randomlabel.xyz"
        packets = [_make_dns_packet(query)]
        findings = detect_suspicious_dns(packets, entropy_threshold=3.5)
        self.assertGreater(len(findings), 0)
        self.assertEqual(findings[0]["category"], "suspicious_dns")

    def test_normal_domain_not_flagged(self):
        query = "www.example.com"
        packets = [_make_dns_packet(query)]
        findings = detect_suspicious_dns(
            packets,
            entropy_threshold=4.0,
            length_threshold=50,
            label_length_threshold=32,
        )
        self.assertEqual(len(findings), 0)

    def test_long_query_flagged(self):
        query = "a" * 60 + ".example.com"
        packets = [_make_dns_packet(query)]
        findings = detect_suspicious_dns(packets, length_threshold=50)
        self.assertGreater(len(findings), 0)
        reasons = findings[0]["evidence"]["reasons"]
        self.assertTrue(any("length" in r or "label" in r for r in reasons))

    def test_suspicious_tld(self):
        query = "something.xyz"
        packets = [_make_dns_packet(query)]
        findings = detect_suspicious_dns(
            packets,
            entropy_threshold=10.0,   # very high so entropy alone won't trigger
            length_threshold=1000,
            label_length_threshold=1000,
        )
        self.assertGreater(len(findings), 0)
        reasons = findings[0]["evidence"]["reasons"]
        self.assertTrue(any("TLD" in r for r in reasons))

    def test_deduplication(self):
        """Same query appearing multiple times should produce only one finding."""
        query = "a1b2c3d4e5f6.badsite.xyz"
        packets = [_make_dns_packet(query, timestamp=i) for i in range(5)]
        findings = detect_suspicious_dns(packets, entropy_threshold=3.0)
        query_findings = [f for f in findings if query.rstrip(".") in f["evidence"]["query"]]
        self.assertEqual(len(query_findings), 1)

    def test_empty_packets(self):
        findings = detect_suspicious_dns([])
        self.assertEqual(findings, [])

    def test_non_dns_packets_ignored(self):
        packets = [_make_packet(protocol="TCP")]
        findings = detect_suspicious_dns(packets)
        self.assertEqual(findings, [])

    def test_multiple_reasons_increase_severity(self):
        # Long + high entropy + suspicious TLD
        query = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7.badsite.xyz"
        packets = [_make_dns_packet(query)]
        findings = detect_suspicious_dns(
            packets,
            entropy_threshold=3.0,
            length_threshold=40,
            label_length_threshold=30,
        )
        self.assertGreater(len(findings), 0)
        self.assertGreaterEqual(len(findings[0]["evidence"]["reasons"]), 2)


class TestICMPFlood(unittest.TestCase):
    """Test ICMP flood detection."""

    def test_icmp_flood_detected(self):
        packets = [_make_packet(protocol="ICMP") for _ in range(40)]
        packets += [_make_packet(protocol="TCP") for _ in range(60)]
        findings = detect_icmp_flood(packets, threshold_pct=25.0, min_packets=50)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["category"], "icmp_flood")

    def test_icmp_below_threshold(self):
        packets = [_make_packet(protocol="ICMP") for _ in range(5)]
        packets += [_make_packet(protocol="TCP") for _ in range(95)]
        findings = detect_icmp_flood(packets, threshold_pct=25.0, min_packets=50)
        self.assertEqual(len(findings), 0)

    def test_too_few_packets(self):
        packets = [_make_packet(protocol="ICMP") for _ in range(10)]
        findings = detect_icmp_flood(packets, threshold_pct=25.0, min_packets=50)
        self.assertEqual(len(findings), 0)

    def test_top_sources_in_evidence(self):
        packets = [
            _make_packet(protocol="ICMP", src_ip="10.0.0.1")
            for _ in range(80)
        ]
        packets += [_make_packet(protocol="TCP") for _ in range(20)]
        findings = detect_icmp_flood(packets, threshold_pct=25.0, min_packets=50)
        self.assertIn("top_sources", findings[0]["evidence"])


class TestARPAnomalies(unittest.TestCase):
    """Test ARP anomaly detection."""

    def test_arp_storm_detected(self):
        packets = [_make_packet(protocol="ARP") for _ in range(150)]
        findings = detect_arp_anomalies(packets, storm_threshold=100)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["category"], "arp_anomaly")

    def test_arp_below_threshold(self):
        packets = [_make_packet(protocol="ARP") for _ in range(50)]
        findings = detect_arp_anomalies(packets, storm_threshold=100)
        self.assertEqual(len(findings), 0)

    def test_ether_0806_detected(self):
        """Fallback parser labels ARP as ETHER(0x0806)."""
        packets = [_make_packet(protocol="ETHER(0x0806)") for _ in range(120)]
        findings = detect_arp_anomalies(packets, storm_threshold=100)
        self.assertEqual(len(findings), 1)


class TestRunAllDetectors(unittest.TestCase):
    """Test the aggregate detector runner."""

    def test_combined_findings(self):
        # Port scan packets
        packets = _make_port_scan_packets(num_ports=30)
        # Plus some suspicious DNS
        packets.append(_make_dns_packet(
            "x1y2z3a4b5c6d7e8f9.evil.xyz",
            timestamp=1700000100.0,
        ))
        findings = run_all_detectors(
            packets,
            port_scan_threshold=15,
            spike_factor=3.0,
            dns_entropy_threshold=3.5,
        )
        categories = {f["category"] for f in findings}
        self.assertIn("port_scan", categories)
        self.assertIn("suspicious_dns", categories)

    def test_severity_sorted(self):
        packets = _make_port_scan_packets(num_ports=100)
        packets.append(_make_dns_packet(
            "x1y2z3.test.xyz",
            timestamp=1700000100.0,
        ))
        findings = run_all_detectors(packets, port_scan_threshold=15)
        severity_order = {
            "critical": 0, "high": 1, "medium": 2, "low": 3,
        }
        for i in range(len(findings) - 1):
            current = severity_order.get(findings[i]["severity"], 99)
            nxt = severity_order.get(findings[i + 1]["severity"], 99)
            self.assertLessEqual(current, nxt)

    def test_empty_packets(self):
        findings = run_all_detectors([])
        self.assertEqual(findings, [])


class TestSummarizeFindings(unittest.TestCase):
    """Test the findings summary helper."""

    def test_summary_structure(self):
        findings = [
            {"category": "port_scan", "severity": "high",
             "title": "t", "description": "d", "evidence": {}},
            {"category": "suspicious_dns", "severity": "low",
             "title": "t", "description": "d", "evidence": {}},
            {"category": "port_scan", "severity": "medium",
             "title": "t", "description": "d", "evidence": {}},
        ]
        summary = summarize_findings(findings)
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["by_category"]["port_scan"], 2)
        self.assertEqual(summary["by_category"]["suspicious_dns"], 1)
        self.assertEqual(summary["by_severity"]["high"], 1)
        self.assertEqual(summary["by_severity"]["low"], 1)
        self.assertEqual(summary["by_severity"]["medium"], 1)

    def test_empty_findings(self):
        summary = summarize_findings([])
        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["by_severity"], {})
        self.assertEqual(summary["by_category"], {})


class TestFindingStructure(unittest.TestCase):
    """Verify that every finding has the expected keys."""

    def test_finding_keys(self):
        packets = _make_port_scan_packets(num_ports=20)
        findings = detect_port_scans(packets, threshold=15)
        required_keys = {"category", "title", "description", "severity", "evidence"}
        for finding in findings:
            self.assertTrue(
                required_keys.issubset(finding.keys()),
                f"Missing keys: {required_keys - finding.keys()}",
            )

    def test_severity_values(self):
        valid = {SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL}
        packets = _make_port_scan_packets(num_ports=100)
        findings = detect_port_scans(packets, threshold=5)
        for finding in findings:
            self.assertIn(finding["severity"], valid)


if __name__ == "__main__":
    unittest.main()
