"""
PCAP Parser Module
==================

Parses PCAP (Packet Capture) files and extracts structured metadata from each
packet. Uses Scapy as the primary parsing engine with a pure-Python fallback
for environments where Scapy is unavailable.

WARNING: Only analyze PCAP files captured from networks you are authorized to
monitor. Unauthorized traffic analysis may violate applicable laws.
"""

import struct
import socket
import time
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# ---------------------------------------------------------------------------
# Try importing Scapy; set a flag so the rest of the module can branch.
# ---------------------------------------------------------------------------
try:
    from scapy.all import rdpcap, IP, IPv6, TCP, UDP, ICMP, DNS, DNSQR, Raw
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


# ---------------------------------------------------------------------------
# Protocol number -> human-readable name mapping (used by the fallback parser)
# ---------------------------------------------------------------------------
PROTOCOL_MAP: Dict[int, str] = {
    1: "ICMP",
    2: "IGMP",
    6: "TCP",
    17: "UDP",
    41: "IPv6-encap",
    47: "GRE",
    50: "ESP",
    51: "AH",
    58: "ICMPv6",
    89: "OSPF",
    132: "SCTP",
}


def protocol_name(proto_num: int) -> str:
    """Return a human-readable protocol name for *proto_num*."""
    return PROTOCOL_MAP.get(proto_num, f"OTHER({proto_num})")


# ===================================================================
# Scapy-based parser
# ===================================================================

def _parse_with_scapy(filepath: str) -> List[Dict[str, Any]]:
    """Parse *filepath* using Scapy and return a list of packet dicts."""

    packets = rdpcap(filepath)
    results: List[Dict[str, Any]] = []

    for pkt in packets:
        record: Dict[str, Any] = {
            "timestamp": float(pkt.time),
            "datetime": datetime.fromtimestamp(float(pkt.time), tz=timezone.utc).isoformat(),
            "size": len(pkt),
            "src_ip": None,
            "dst_ip": None,
            "protocol": "UNKNOWN",
            "src_port": None,
            "dst_port": None,
            "info": {},
        }

        # --- Layer 3 --------------------------------------------------
        if pkt.haslayer(IP):
            ip_layer = pkt[IP]
            record["src_ip"] = ip_layer.src
            record["dst_ip"] = ip_layer.dst
            record["protocol"] = protocol_name(ip_layer.proto)
            record["ttl"] = ip_layer.ttl
            record["ip_version"] = 4
        elif pkt.haslayer(IPv6):
            ip6 = pkt[IPv6]
            record["src_ip"] = ip6.src
            record["dst_ip"] = ip6.dst
            record["protocol"] = protocol_name(ip6.nh)
            record["ip_version"] = 6

        # --- Layer 4 --------------------------------------------------
        if pkt.haslayer(TCP):
            tcp = pkt[TCP]
            record["src_port"] = tcp.sport
            record["dst_port"] = tcp.dport
            record["protocol"] = "TCP"
            record["info"]["tcp_flags"] = str(tcp.flags)
            record["info"]["seq"] = tcp.seq
            record["info"]["ack"] = tcp.ack
            record["info"]["window"] = tcp.window
        elif pkt.haslayer(UDP):
            udp = pkt[UDP]
            record["src_port"] = udp.sport
            record["dst_port"] = udp.dport
            record["protocol"] = "UDP"
        elif pkt.haslayer(ICMP):
            icmp = pkt[ICMP]
            record["protocol"] = "ICMP"
            record["info"]["icmp_type"] = icmp.type
            record["info"]["icmp_code"] = icmp.code

        # --- DNS -------------------------------------------------------
        if pkt.haslayer(DNS):
            dns = pkt[DNS]
            record["protocol"] = "DNS"
            if dns.qr == 0 and pkt.haslayer(DNSQR):
                qname = pkt[DNSQR].qname
                if isinstance(qname, bytes):
                    qname = qname.decode("utf-8", errors="replace")
                record["info"]["dns_query"] = qname.rstrip(".")
                record["info"]["dns_type"] = pkt[DNSQR].qtype

        # --- Payload size ----------------------------------------------
        if pkt.haslayer(Raw):
            record["info"]["payload_size"] = len(pkt[Raw].load)
        else:
            record["info"]["payload_size"] = 0

        results.append(record)

    return results


# ===================================================================
# Pure-Python fallback PCAP parser
# ===================================================================

# PCAP global header: magic(4) version_major(2) version_minor(2)
#                     thiszone(4) sigfigs(4) snaplen(4) network(4)  = 24 bytes
# PCAP packet header: ts_sec(4) ts_usec(4) incl_len(4) orig_len(4) = 16 bytes
# Ethernet header:    dst_mac(6) src_mac(6) ethertype(2)            = 14 bytes

_PCAP_GLOBAL_HDR = 24
_PCAP_PKT_HDR = 16
_ETH_HDR = 14

_MAGIC_LE = 0xA1B2C3D4
_MAGIC_BE = 0xD4C3B2A1
_MAGIC_NS_LE = 0xA1B23C4D  # nanosecond resolution
_MAGIC_NS_BE = 0x4D3CB2A1


def _parse_fallback(filepath: str) -> List[Dict[str, Any]]:
    """
    Minimal PCAP parser that handles Ethernet-encapsulated IPv4 packets
    without any external dependencies.  Designed as a fallback when Scapy
    is not installed.
    """

    results: List[Dict[str, Any]] = []

    with open(filepath, "rb") as fh:
        global_hdr = fh.read(_PCAP_GLOBAL_HDR)
        if len(global_hdr) < _PCAP_GLOBAL_HDR:
            raise ValueError("File too small to contain a valid PCAP global header.")

        magic = struct.unpack("<I", global_hdr[:4])[0]
        if magic == _MAGIC_LE or magic == _MAGIC_NS_LE:
            endian = "<"
            nano = magic == _MAGIC_NS_LE
        elif magic == _MAGIC_BE or magic == _MAGIC_NS_BE:
            endian = ">"
            nano = magic == _MAGIC_NS_BE
        else:
            raise ValueError(f"Unrecognized PCAP magic number: 0x{magic:08X}")

        link_type = struct.unpack(f"{endian}I", global_hdr[20:24])[0]
        if link_type != 1:
            raise ValueError(
                f"Fallback parser only supports Ethernet (link type 1), got {link_type}. "
                "Install Scapy for broader format support."
            )

        while True:
            pkt_hdr = fh.read(_PCAP_PKT_HDR)
            if len(pkt_hdr) < _PCAP_PKT_HDR:
                break  # End of file

            ts_sec, ts_usec, incl_len, orig_len = struct.unpack(
                f"{endian}IIII", pkt_hdr
            )

            if nano:
                timestamp = ts_sec + ts_usec / 1_000_000_000
            else:
                timestamp = ts_sec + ts_usec / 1_000_000

            raw = fh.read(incl_len)
            if len(raw) < incl_len:
                break  # Truncated capture

            record: Dict[str, Any] = {
                "timestamp": timestamp,
                "datetime": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(),
                "size": orig_len,
                "src_ip": None,
                "dst_ip": None,
                "protocol": "UNKNOWN",
                "src_port": None,
                "dst_port": None,
                "info": {},
            }

            # --- Ethernet header ---
            if len(raw) < _ETH_HDR:
                results.append(record)
                continue

            ethertype = struct.unpack("!H", raw[12:14])[0]

            # Only handle IPv4 (0x0800) in fallback
            if ethertype != 0x0800:
                record["protocol"] = f"ETHER(0x{ethertype:04X})"
                results.append(record)
                continue

            # --- IPv4 header ---
            ip_start = _ETH_HDR
            if len(raw) < ip_start + 20:
                results.append(record)
                continue

            version_ihl = raw[ip_start]
            ihl = (version_ihl & 0x0F) * 4
            total_length = struct.unpack("!H", raw[ip_start + 2 : ip_start + 4])[0]
            ttl = raw[ip_start + 8]
            proto_num = raw[ip_start + 9]

            src_ip = socket.inet_ntoa(raw[ip_start + 12 : ip_start + 16])
            dst_ip = socket.inet_ntoa(raw[ip_start + 16 : ip_start + 20])

            record["src_ip"] = src_ip
            record["dst_ip"] = dst_ip
            record["protocol"] = protocol_name(proto_num)
            record["ttl"] = ttl
            record["ip_version"] = 4

            transport_start = ip_start + ihl

            # --- TCP ---
            if proto_num == 6 and len(raw) >= transport_start + 20:
                src_port, dst_port = struct.unpack(
                    "!HH", raw[transport_start : transport_start + 4]
                )
                record["src_port"] = src_port
                record["dst_port"] = dst_port
                record["protocol"] = "TCP"

                data_offset = (raw[transport_start + 12] >> 4) * 4
                flags_byte = raw[transport_start + 13]
                flag_names = []
                for bit, name in [
                    (0x01, "F"), (0x02, "S"), (0x04, "R"),
                    (0x08, "P"), (0x10, "A"), (0x20, "U"),
                ]:
                    if flags_byte & bit:
                        flag_names.append(name)
                record["info"]["tcp_flags"] = "".join(flag_names)

                payload_len = total_length - ihl - data_offset
                record["info"]["payload_size"] = max(payload_len, 0)

            # --- UDP ---
            elif proto_num == 17 and len(raw) >= transport_start + 8:
                src_port, dst_port, udp_len = struct.unpack(
                    "!HHH", raw[transport_start : transport_start + 6]
                )
                record["src_port"] = src_port
                record["dst_port"] = dst_port
                record["protocol"] = "UDP"
                record["info"]["payload_size"] = max(udp_len - 8, 0)

                # Rudimentary DNS detection on port 53
                if src_port == 53 or dst_port == 53:
                    record["protocol"] = "DNS"
                    dns_start = transport_start + 8
                    if len(raw) > dns_start + 12:
                        flags_hi = raw[dns_start + 2]
                        is_query = (flags_hi & 0x80) == 0
                        if is_query:
                            qname = _extract_dns_qname(raw, dns_start + 12)
                            if qname:
                                record["info"]["dns_query"] = qname

            # --- ICMP ---
            elif proto_num == 1 and len(raw) >= transport_start + 4:
                record["protocol"] = "ICMP"
                record["info"]["icmp_type"] = raw[transport_start]
                record["info"]["icmp_code"] = raw[transport_start + 1]
                record["info"]["payload_size"] = max(
                    total_length - ihl - 8, 0
                )

            results.append(record)

    return results


def _extract_dns_qname(data: bytes, offset: int) -> Optional[str]:
    """Extract the first QNAME from a DNS payload starting at *offset*."""
    labels = []
    pos = offset
    max_pos = len(data)
    safety = 0
    while pos < max_pos and safety < 128:
        length = data[pos]
        if length == 0:
            break
        if (length & 0xC0) == 0xC0:
            # Pointer -- skip for simplicity in fallback
            break
        pos += 1
        if pos + length > max_pos:
            break
        labels.append(data[pos : pos + length].decode("ascii", errors="replace"))
        pos += length
        safety += 1
    return ".".join(labels) if labels else None


# ===================================================================
# Public API
# ===================================================================

def parse_pcap(filepath: str, force_fallback: bool = False) -> List[Dict[str, Any]]:
    """
    Parse a PCAP file and return a list of packet metadata dictionaries.

    Parameters
    ----------
    filepath : str
        Path to the PCAP file.
    force_fallback : bool
        If True, use the pure-Python fallback even when Scapy is available.

    Returns
    -------
    list[dict]
        Each dictionary contains:
        - timestamp (float): Unix epoch timestamp of the packet.
        - datetime (str): ISO-8601 UTC timestamp.
        - size (int): Original packet size in bytes.
        - src_ip (str | None): Source IP address.
        - dst_ip (str | None): Destination IP address.
        - protocol (str): Detected protocol name.
        - src_port (int | None): Source port (TCP/UDP only).
        - dst_port (int | None): Destination port (TCP/UDP only).
        - info (dict): Protocol-specific extra fields.

    Raises
    ------
    FileNotFoundError
        If *filepath* does not exist.
    ValueError
        If the file is not a valid PCAP.
    """

    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"PCAP file not found: {filepath}")

    if SCAPY_AVAILABLE and not force_fallback:
        return _parse_with_scapy(filepath)

    return _parse_fallback(filepath)


def export_json(packets: List[Dict[str, Any]], output_path: str) -> str:
    """
    Serialize a packet list to a JSON file.

    Parameters
    ----------
    packets : list[dict]
        Packet metadata as returned by :func:`parse_pcap`.
    output_path : str
        Destination file path.

    Returns
    -------
    str
        The absolute path of the written file.
    """

    abs_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as fh:
        json.dump(packets, fh, indent=2, default=str)
    return abs_path


def get_parser_backend() -> str:
    """Return the name of the active parsing backend."""
    return "scapy" if SCAPY_AVAILABLE else "fallback"


# ===================================================================
# Convenience: run directly to parse a file from the command line
# ===================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.parser <pcap_file> [output.json]")
        sys.exit(1)

    pcap_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"[*] Parsing {pcap_path} (backend: {get_parser_backend()}) ...")
    parsed = parse_pcap(pcap_path)
    print(f"[+] Parsed {len(parsed)} packets.")

    if out_path:
        written = export_json(parsed, out_path)
        print(f"[+] Exported to {written}")
    else:
        for pkt in parsed[:10]:
            print(pkt)
        if len(parsed) > 10:
            print(f"... and {len(parsed) - 10} more packets.")
