"""
Unit Tests for src.parser
==========================

Tests cover:
- Packet dictionary structure and required keys
- Scapy backend parsing (if Scapy is installed)
- Pure-Python fallback parsing
- JSON export functionality
- Error handling for missing and invalid files
- DNS query extraction in fallback mode

These tests use a small PCAP file created on the fly with Scapy (if
available) or with raw bytes for the fallback parser.
"""

import json
import os
import struct
import tempfile
import unittest
from datetime import datetime

# Import the module under test
from src.parser import (
    parse_pcap,
    export_json,
    get_parser_backend,
    protocol_name,
    SCAPY_AVAILABLE,
    _parse_fallback,
)


# ===================================================================
# Helpers: build minimal PCAP files in raw bytes
# ===================================================================

def _build_pcap_global_header() -> bytes:
    """Build a standard little-endian PCAP global header."""
    return struct.pack(
        "<IHHiIII",
        0xA1B2C3D4,  # magic
        2, 4,         # version major, minor
        0,            # thiszone
        0,            # sigfigs
        65535,        # snaplen
        1,            # Ethernet link type
    )


def _build_ethernet_ipv4_tcp_packet(
    src_ip: str = "192.168.1.10",
    dst_ip: str = "10.0.0.1",
    src_port: int = 12345,
    dst_port: int = 80,
    tcp_flags: int = 0x02,  # SYN
    payload: bytes = b"",
    ts_sec: int = 1700000000,
    ts_usec: int = 0,
) -> bytes:
    """
    Build a raw Ethernet + IPv4 + TCP packet as bytes, prefixed with
    the PCAP per-packet header.
    """
    import socket as _sock

    # Ethernet header: dst_mac(6) + src_mac(6) + ethertype(2)
    eth = b"\x00" * 6 + b"\x00" * 6 + struct.pack("!H", 0x0800)

    # IP header (20 bytes, no options)
    ip_total_len = 20 + 20 + len(payload)  # IP + TCP + payload
    ip_hdr = struct.pack(
        "!BBHHHBBH4s4s",
        0x45,           # version=4, IHL=5
        0,              # DSCP/ECN
        ip_total_len,
        0,              # identification
        0,              # flags/fragment
        64,             # TTL
        6,              # protocol = TCP
        0,              # checksum (skip for test)
        _sock.inet_aton(src_ip),
        _sock.inet_aton(dst_ip),
    )

    # TCP header (20 bytes, no options)
    data_offset = 5 << 4  # 5 * 4 = 20 bytes
    tcp_hdr = struct.pack(
        "!HHIIBBHHH",
        src_port,
        dst_port,
        1000,           # seq
        0,              # ack
        data_offset,
        tcp_flags,
        65535,          # window
        0,              # checksum
        0,              # urgent pointer
    )

    frame = eth + ip_hdr + tcp_hdr + payload
    incl_len = len(frame)
    orig_len = incl_len

    pkt_hdr = struct.pack("<IIII", ts_sec, ts_usec, incl_len, orig_len)
    return pkt_hdr + frame


def _build_ethernet_ipv4_udp_dns_packet(
    src_ip: str = "192.168.1.10",
    dst_ip: str = "8.8.8.8",
    src_port: int = 54321,
    qname: str = "example.com",
    ts_sec: int = 1700000000,
    ts_usec: int = 500000,
) -> bytes:
    """Build a raw Ethernet + IPv4 + UDP + DNS query packet."""
    import socket as _sock

    eth = b"\x00" * 6 + b"\x00" * 6 + struct.pack("!H", 0x0800)

    # DNS payload: header(12) + qname + qtype(2) + qclass(2)
    dns_payload = struct.pack("!HHHHHH", 0x1234, 0x0100, 1, 0, 0, 0)
    for label in qname.split("."):
        dns_payload += struct.pack("B", len(label)) + label.encode("ascii")
    dns_payload += b"\x00"  # root label
    dns_payload += struct.pack("!HH", 1, 1)  # A record, IN class

    udp_len = 8 + len(dns_payload)
    udp_hdr = struct.pack("!HHHH", src_port, 53, udp_len, 0)

    ip_total_len = 20 + udp_len
    ip_hdr = struct.pack(
        "!BBHHHBBH4s4s",
        0x45, 0, ip_total_len, 0, 0, 64, 17, 0,
        _sock.inet_aton(src_ip),
        _sock.inet_aton(dst_ip),
    )

    frame = eth + ip_hdr + udp_hdr + dns_payload
    pkt_hdr = struct.pack("<IIII", ts_sec, ts_usec, len(frame), len(frame))
    return pkt_hdr + frame


def _create_raw_pcap(packets_bytes: list) -> bytes:
    """Concatenate a global header with a list of raw packet byte strings."""
    return _build_pcap_global_header() + b"".join(packets_bytes)


# ===================================================================
# Test cases
# ===================================================================

class TestProtocolName(unittest.TestCase):
    """Test the protocol_name helper."""

    def test_known_protocols(self):
        self.assertEqual(protocol_name(6), "TCP")
        self.assertEqual(protocol_name(17), "UDP")
        self.assertEqual(protocol_name(1), "ICMP")

    def test_unknown_protocol(self):
        result = protocol_name(255)
        self.assertIn("OTHER", result)
        self.assertIn("255", result)


class TestFallbackParser(unittest.TestCase):
    """Test the pure-Python fallback PCAP parser."""

    def setUp(self):
        """Create a temporary PCAP file with known content."""
        raw_tcp = _build_ethernet_ipv4_tcp_packet(
            src_ip="192.168.1.10",
            dst_ip="10.0.0.1",
            src_port=12345,
            dst_port=80,
            tcp_flags=0x02,  # SYN
            ts_sec=1700000000,
            ts_usec=0,
        )
        raw_dns = _build_ethernet_ipv4_udp_dns_packet(
            src_ip="192.168.1.10",
            dst_ip="8.8.8.8",
            qname="example.com",
            ts_sec=1700000001,
            ts_usec=0,
        )
        pcap_data = _create_raw_pcap([raw_tcp, raw_dns])

        self.tmpfile = tempfile.NamedTemporaryFile(
            suffix=".pcap", delete=False
        )
        self.tmpfile.write(pcap_data)
        self.tmpfile.close()
        self.pcap_path = self.tmpfile.name

    def tearDown(self):
        os.unlink(self.pcap_path)

    def test_parse_returns_list(self):
        result = _parse_fallback(self.pcap_path)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_packet_has_required_keys(self):
        result = _parse_fallback(self.pcap_path)
        required_keys = {
            "timestamp", "datetime", "size", "src_ip", "dst_ip",
            "protocol", "src_port", "dst_port", "info",
        }
        for pkt in result:
            self.assertTrue(
                required_keys.issubset(pkt.keys()),
                f"Missing keys: {required_keys - pkt.keys()}",
            )

    def test_tcp_packet_fields(self):
        result = _parse_fallback(self.pcap_path)
        tcp_pkt = result[0]
        self.assertEqual(tcp_pkt["src_ip"], "192.168.1.10")
        self.assertEqual(tcp_pkt["dst_ip"], "10.0.0.1")
        self.assertEqual(tcp_pkt["protocol"], "TCP")
        self.assertEqual(tcp_pkt["src_port"], 12345)
        self.assertEqual(tcp_pkt["dst_port"], 80)
        self.assertIn("tcp_flags", tcp_pkt["info"])
        self.assertIn("S", tcp_pkt["info"]["tcp_flags"])

    def test_dns_packet_detection(self):
        result = _parse_fallback(self.pcap_path)
        dns_pkt = result[1]
        self.assertEqual(dns_pkt["protocol"], "DNS")
        self.assertEqual(dns_pkt["dst_port"], 53)
        self.assertIn("dns_query", dns_pkt["info"])
        self.assertEqual(dns_pkt["info"]["dns_query"], "example.com")

    def test_timestamp_is_float(self):
        result = _parse_fallback(self.pcap_path)
        for pkt in result:
            self.assertIsInstance(pkt["timestamp"], float)

    def test_datetime_is_iso_format(self):
        result = _parse_fallback(self.pcap_path)
        for pkt in result:
            # Should not raise
            datetime.fromisoformat(pkt["datetime"])

    def test_invalid_file_raises(self):
        with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
            f.write(b"not a pcap file")
            path = f.name
        try:
            with self.assertRaises(ValueError):
                _parse_fallback(path)
        finally:
            os.unlink(path)

    def test_truncated_file(self):
        """A file with only the global header should return empty list."""
        with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
            f.write(_build_pcap_global_header())
            path = f.name
        try:
            result = _parse_fallback(path)
            self.assertEqual(result, [])
        finally:
            os.unlink(path)


class TestParsePcap(unittest.TestCase):
    """Test the public parse_pcap function."""

    def setUp(self):
        raw_tcp = _build_ethernet_ipv4_tcp_packet()
        pcap_data = _create_raw_pcap([raw_tcp])
        self.tmpfile = tempfile.NamedTemporaryFile(
            suffix=".pcap", delete=False
        )
        self.tmpfile.write(pcap_data)
        self.tmpfile.close()
        self.pcap_path = self.tmpfile.name

    def tearDown(self):
        os.unlink(self.pcap_path)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            parse_pcap("/nonexistent/path/file.pcap")

    def test_force_fallback(self):
        result = parse_pcap(self.pcap_path, force_fallback=True)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_backend_detection(self):
        backend = get_parser_backend()
        self.assertIn(backend, ("scapy", "fallback"))

    @unittest.skipUnless(SCAPY_AVAILABLE, "Scapy not installed")
    def test_scapy_parser(self):
        result = parse_pcap(self.pcap_path, force_fallback=False)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        pkt = result[0]
        self.assertIn("src_ip", pkt)
        self.assertIn("dst_ip", pkt)


class TestExportJson(unittest.TestCase):
    """Test the JSON export function."""

    def test_export_creates_file(self):
        packets = [
            {
                "timestamp": 1700000000.0,
                "datetime": "2023-11-14T22:13:20+00:00",
                "size": 100,
                "src_ip": "192.168.1.1",
                "dst_ip": "10.0.0.1",
                "protocol": "TCP",
                "src_port": 12345,
                "dst_port": 80,
                "info": {"tcp_flags": "S"},
            }
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "test_output.json")
            result = export_json(packets, out_path)
            self.assertTrue(os.path.isfile(result))

            with open(result, "r", encoding="utf-8") as fh:
                data = json.load(fh)

            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["src_ip"], "192.168.1.1")

    def test_export_creates_subdirectories(self):
        packets = [{"test": True}]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "sub", "dir", "output.json")
            result = export_json(packets, out_path)
            self.assertTrue(os.path.isfile(result))


class TestMultiplePacketParsing(unittest.TestCase):
    """Test parsing a PCAP with multiple packets of different types."""

    def test_mixed_packet_types(self):
        tcp1 = _build_ethernet_ipv4_tcp_packet(
            src_ip="10.0.0.1", dst_ip="10.0.0.2", dst_port=443,
            ts_sec=1700000000,
        )
        tcp2 = _build_ethernet_ipv4_tcp_packet(
            src_ip="10.0.0.3", dst_ip="10.0.0.4", dst_port=22,
            ts_sec=1700000001,
        )
        dns = _build_ethernet_ipv4_udp_dns_packet(
            src_ip="10.0.0.5", qname="test.org",
            ts_sec=1700000002,
        )
        pcap_data = _create_raw_pcap([tcp1, tcp2, dns])

        with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
            f.write(pcap_data)
            path = f.name

        try:
            result = _parse_fallback(path)
            self.assertEqual(len(result), 3)

            # Check first TCP
            self.assertEqual(result[0]["src_ip"], "10.0.0.1")
            self.assertEqual(result[0]["dst_port"], 443)

            # Check second TCP
            self.assertEqual(result[1]["src_ip"], "10.0.0.3")
            self.assertEqual(result[1]["dst_port"], 22)

            # Check DNS
            self.assertEqual(result[2]["protocol"], "DNS")
            self.assertEqual(result[2]["info"]["dns_query"], "test.org")
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
