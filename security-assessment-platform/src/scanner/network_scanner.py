"""
Network Scanner Module - TCP port scanning and service banner grabbing.

Provides comprehensive network reconnaissance through TCP connect scanning
and service identification via banner grabbing. All scanning activities
must be performed only against authorized target systems.

ETHICAL USE NOTICE:
    This module performs active network scanning. Ensure you have explicit
    written authorization before scanning any system. Unauthorized scanning
    may violate laws in your jurisdiction.
"""

import socket
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


# Well-known service-to-port mappings for identification
COMMON_SERVICES: Dict[int, str] = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    111: "RPCBind",
    135: "MSRPC",
    139: "NetBIOS-SSN",
    143: "IMAP",
    443: "HTTPS",
    445: "Microsoft-DS",
    993: "IMAPS",
    995: "POP3S",
    1433: "MSSQL",
    1521: "Oracle",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    6379: "Redis",
    8080: "HTTP-Proxy",
    8443: "HTTPS-Alt",
    8888: "HTTP-Alt",
    9200: "Elasticsearch",
    27017: "MongoDB",
}

# Ports considered high-risk when exposed
HIGH_RISK_PORTS: set = {
    21, 23, 135, 139, 445, 1433, 1521, 3306, 3389,
    5432, 5900, 6379, 9200, 27017,
}

# Ports considered medium-risk when exposed
MEDIUM_RISK_PORTS: set = {
    25, 53, 80, 110, 111, 143, 8080, 8888,
}


@dataclass
class PortResult:
    """Result of a single port scan."""

    port: int
    state: str  # "open", "closed", "filtered"
    service: str = "unknown"
    banner: str = ""
    version: str = ""
    risk_level: str = "info"  # "critical", "high", "medium", "low", "info"
    response_time_ms: float = 0.0


@dataclass
class NetworkScanResult:
    """Complete result of a network scan against a target."""

    target: str
    scan_start: str = ""
    scan_end: str = ""
    scan_duration_seconds: float = 0.0
    total_ports_scanned: int = 0
    open_ports: List[PortResult] = field(default_factory=list)
    closed_ports: int = 0
    filtered_ports: int = 0
    findings: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert scan result to dictionary for serialization."""
        return {
            "target": self.target,
            "scan_start": self.scan_start,
            "scan_end": self.scan_end,
            "scan_duration_seconds": self.scan_duration_seconds,
            "total_ports_scanned": self.total_ports_scanned,
            "open_ports_count": len(self.open_ports),
            "closed_ports_count": self.closed_ports,
            "filtered_ports_count": self.filtered_ports,
            "open_ports": [
                {
                    "port": p.port,
                    "state": p.state,
                    "service": p.service,
                    "banner": p.banner,
                    "version": p.version,
                    "risk_level": p.risk_level,
                    "response_time_ms": p.response_time_ms,
                }
                for p in self.open_ports
            ],
            "findings": self.findings,
        }


class NetworkScanner:
    """
    TCP port scanner with service banner grabbing.

    Performs TCP connect scans against specified port ranges and attempts
    to identify services through banner grabbing. Supports concurrent
    scanning with configurable thread pools.

    Attributes:
        timeout: Socket connection timeout in seconds.
        max_threads: Maximum number of concurrent scan threads.
        banner_timeout: Timeout for banner grabbing in seconds.

    Example:
        scanner = NetworkScanner(timeout=2.0, max_threads=50)
        result = scanner.scan("192.168.1.1", port_range=(1, 1024))
        for port in result.open_ports:
            print(f"Port {port.port}: {port.service} ({port.banner})")
    """

    def __init__(
        self,
        timeout: float = 2.0,
        max_threads: int = 50,
        banner_timeout: float = 3.0,
    ):
        """
        Initialize the NetworkScanner.

        Args:
            timeout: TCP connection timeout in seconds (default 2.0).
            max_threads: Maximum concurrent scanning threads (default 50).
            banner_timeout: Timeout for banner grabbing in seconds (default 3.0).
        """
        self.timeout = timeout
        self.max_threads = max_threads
        self.banner_timeout = banner_timeout

    def scan(
        self,
        target: str,
        port_range: Tuple[int, int] = (1, 1024),
        specific_ports: Optional[List[int]] = None,
    ) -> NetworkScanResult:
        """
        Perform a comprehensive port scan on the target.

        Scans either a range of ports or a specific list of ports using
        TCP connect scanning. For each open port, attempts banner grabbing
        and service identification.

        Args:
            target: IP address or hostname to scan.
            port_range: Tuple of (start_port, end_port) inclusive.
            specific_ports: Optional list of specific ports to scan.
                If provided, overrides port_range.

        Returns:
            NetworkScanResult with all findings and open port details.

        Raises:
            ValueError: If target is empty or port range is invalid.
        """
        if not target:
            raise ValueError("Target host must be specified")

        if specific_ports:
            ports = specific_ports
        else:
            start, end = port_range
            if start < 1 or end > 65535 or start > end:
                raise ValueError(
                    f"Invalid port range: {start}-{end}. "
                    "Must be between 1-65535 with start <= end."
                )
            ports = list(range(start, end + 1))

        result = NetworkScanResult(target=target)
        result.scan_start = datetime.now().isoformat()
        result.total_ports_scanned = len(ports)

        logger.info(
            f"Starting scan of {target}: {len(ports)} ports "
            f"with {self.max_threads} threads"
        )

        scan_start_time = time.time()

        # Resolve hostname to IP for logging
        try:
            resolved_ip = socket.gethostbyname(target)
            if resolved_ip != target:
                logger.info(f"Resolved {target} to {resolved_ip}")
        except socket.gaierror:
            logger.warning(f"Could not resolve hostname: {target}")
            resolved_ip = target

        # Concurrent port scanning
        port_results = []
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_port = {
                executor.submit(self._scan_port, target, port): port
                for port in ports
            }

            for future in as_completed(future_to_port):
                port_num = future_to_port[future]
                try:
                    port_result = future.result()
                    port_results.append(port_result)
                except Exception as exc:
                    logger.error(f"Port {port_num} scan raised: {exc}")

        # Process results
        for pr in sorted(port_results, key=lambda x: x.port):
            if pr.state == "open":
                result.open_ports.append(pr)
            elif pr.state == "closed":
                result.closed_ports += 1
            else:
                result.filtered_ports += 1

        # Generate findings from open ports
        result.findings = self._generate_findings(result.open_ports, target)

        result.scan_end = datetime.now().isoformat()
        result.scan_duration_seconds = round(time.time() - scan_start_time, 2)

        logger.info(
            f"Scan complete: {len(result.open_ports)} open, "
            f"{result.closed_ports} closed, "
            f"{result.filtered_ports} filtered "
            f"in {result.scan_duration_seconds}s"
        )

        return result

    def _scan_port(self, target: str, port: int) -> PortResult:
        """
        Scan a single TCP port and attempt banner grabbing if open.

        Args:
            target: Target IP address or hostname.
            port: Port number to scan.

        Returns:
            PortResult with the scan outcome.
        """
        start_time = time.time()
        result = PortResult(port=port, state="closed")

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            connection_result = sock.connect_ex((target, port))

            if connection_result == 0:
                result.state = "open"
                result.response_time_ms = round(
                    (time.time() - start_time) * 1000, 2
                )
                result.service = COMMON_SERVICES.get(port, "unknown")

                # Determine risk level
                if port in HIGH_RISK_PORTS:
                    result.risk_level = "high"
                elif port in MEDIUM_RISK_PORTS:
                    result.risk_level = "medium"
                else:
                    result.risk_level = "low"

                # Attempt banner grabbing
                result.banner = self._grab_banner(sock, port)
                if result.banner:
                    result.version = self._extract_version(result.banner)

            sock.close()

        except socket.timeout:
            result.state = "filtered"
            result.response_time_ms = round(
                (time.time() - start_time) * 1000, 2
            )
        except socket.error as e:
            logger.debug(f"Socket error on {target}:{port}: {e}")
            result.state = "filtered"
        except Exception as e:
            logger.debug(f"Unexpected error scanning {target}:{port}: {e}")

        return result

    def _grab_banner(self, sock: socket.socket, port: int) -> str:
        """
        Attempt to grab the service banner from an open port.

        Sends protocol-appropriate probes for known services and reads
        the response. Falls back to a generic read for unknown services.

        Args:
            sock: Connected socket to the target port.
            port: The port number (used for protocol-specific probes).

        Returns:
            Banner string, or empty string if no banner received.
        """
        try:
            sock.settimeout(self.banner_timeout)

            # HTTP probe for web servers
            if port in (80, 8080, 8888, 8443):
                sock.send(b"HEAD / HTTP/1.0\r\nHost: target\r\n\r\n")
            # SMTP probe
            elif port == 25:
                sock.send(b"EHLO probe\r\n")
            # FTP - just read the welcome banner
            elif port == 21:
                pass  # FTP sends banner on connect
            # Generic: try reading first, then send probe
            else:
                pass

            banner_bytes = sock.recv(1024)
            banner = banner_bytes.decode("utf-8", errors="replace").strip()

            # Sanitize: take first line only, limit length
            if banner:
                first_line = banner.split("\n")[0].strip()
                return first_line[:256]

            return ""

        except (socket.timeout, socket.error, UnicodeDecodeError):
            return ""
        except Exception:
            return ""

    def _extract_version(self, banner: str) -> str:
        """
        Extract version information from a service banner.

        Parses common banner formats to identify software versions.

        Args:
            banner: Raw banner string from the service.

        Returns:
            Extracted version string, or empty string if not found.
        """
        version_indicators = [
            "Server:", "SSH-", "220 ", "MySQL", "PostgreSQL",
            "Redis", "MongoDB", "Apache", "nginx", "Microsoft",
            "OpenSSH", "ProFTPD", "vsftpd", "Exim", "Postfix",
        ]

        for indicator in version_indicators:
            if indicator.lower() in banner.lower():
                # Try to extract the version substring
                idx = banner.lower().find(indicator.lower())
                version_part = banner[idx:idx + 80].strip()
                return version_part

        return ""

    def _generate_findings(
        self, open_ports: List[PortResult], target: str
    ) -> List[Dict]:
        """
        Generate security findings from discovered open ports.

        Analyzes open ports for known security issues and generates
        structured finding records with severity ratings and
        remediation recommendations.

        Args:
            open_ports: List of PortResult objects for open ports.
            target: The scanned target hostname or IP.

        Returns:
            List of finding dictionaries.
        """
        findings = []

        # Dangerous services findings
        dangerous_services = {
            21: {
                "title": "FTP Service Exposed",
                "description": (
                    "FTP transmits credentials in plaintext. "
                    "Consider using SFTP or FTPS instead."
                ),
                "severity": "high",
                "cvss_score": 7.5,
                "remediation": (
                    "Disable FTP and migrate to SFTP (SSH File Transfer Protocol) "
                    "or FTPS (FTP over TLS). If FTP is required, restrict access "
                    "via firewall rules and enforce TLS."
                ),
            },
            23: {
                "title": "Telnet Service Exposed",
                "description": (
                    "Telnet transmits all data including credentials in plaintext. "
                    "This is a critical security risk."
                ),
                "severity": "critical",
                "cvss_score": 9.1,
                "remediation": (
                    "Immediately disable Telnet and replace with SSH. "
                    "Block port 23 at the network firewall level."
                ),
            },
            135: {
                "title": "MSRPC Service Exposed",
                "description": (
                    "Microsoft RPC endpoint mapper is accessible. "
                    "This can facilitate lateral movement and enumeration."
                ),
                "severity": "high",
                "cvss_score": 7.0,
                "remediation": (
                    "Restrict RPC access using Windows Firewall with Advanced Security. "
                    "Limit to required internal subnets only."
                ),
            },
            139: {
                "title": "NetBIOS Session Service Exposed",
                "description": (
                    "NetBIOS allows file and printer sharing and can leak "
                    "system information including usernames and shares."
                ),
                "severity": "high",
                "cvss_score": 7.2,
                "remediation": (
                    "Disable NetBIOS over TCP/IP in network adapter settings. "
                    "Use SMB over TCP (port 445) with proper authentication."
                ),
            },
            445: {
                "title": "SMB Service Exposed",
                "description": (
                    "Server Message Block (SMB) service is accessible. "
                    "Historic target for ransomware (WannaCry, NotPetya)."
                ),
                "severity": "high",
                "cvss_score": 8.0,
                "remediation": (
                    "Ensure SMBv1 is disabled. Require SMB signing. "
                    "Restrict SMB access to authorized networks via firewall. "
                    "Apply latest security patches."
                ),
            },
            1433: {
                "title": "MSSQL Service Exposed",
                "description": (
                    "Microsoft SQL Server is directly accessible on the network, "
                    "presenting a risk of data breach through SQL injection or "
                    "brute-force attacks."
                ),
                "severity": "high",
                "cvss_score": 8.5,
                "remediation": (
                    "Restrict database access to application servers only. "
                    "Implement network segmentation. Use Windows Authentication "
                    "instead of SQL authentication where possible."
                ),
            },
            3306: {
                "title": "MySQL Service Exposed",
                "description": (
                    "MySQL database server is directly accessible, "
                    "risking unauthorized data access."
                ),
                "severity": "high",
                "cvss_score": 8.5,
                "remediation": (
                    "Bind MySQL to localhost or private network interfaces. "
                    "Use SSH tunneling or VPN for remote access. "
                    "Implement strong authentication and access controls."
                ),
            },
            3389: {
                "title": "RDP Service Exposed",
                "description": (
                    "Remote Desktop Protocol is accessible. RDP is a frequent "
                    "target for brute-force and credential-stuffing attacks."
                ),
                "severity": "critical",
                "cvss_score": 9.0,
                "remediation": (
                    "Require VPN for RDP access. Enable Network Level Authentication (NLA). "
                    "Implement account lockout policies. Consider using a Remote Desktop Gateway."
                ),
            },
            5432: {
                "title": "PostgreSQL Service Exposed",
                "description": (
                    "PostgreSQL database is directly accessible on the network."
                ),
                "severity": "high",
                "cvss_score": 8.5,
                "remediation": (
                    "Configure pg_hba.conf to restrict client connections. "
                    "Use SSL/TLS for all connections. Bind to localhost "
                    "and use SSH tunneling for remote access."
                ),
            },
            5900: {
                "title": "VNC Service Exposed",
                "description": (
                    "VNC remote desktop service is accessible. VNC authentication "
                    "is often weak and traffic may be unencrypted."
                ),
                "severity": "critical",
                "cvss_score": 9.0,
                "remediation": (
                    "Disable VNC if not required. If needed, require SSH tunneling "
                    "or VPN. Enforce strong passwords and enable encryption."
                ),
            },
            6379: {
                "title": "Redis Service Exposed",
                "description": (
                    "Redis is accessible without authentication by default. "
                    "Unauthenticated Redis can lead to remote code execution."
                ),
                "severity": "critical",
                "cvss_score": 9.8,
                "remediation": (
                    "Enable Redis AUTH with a strong password. Bind to localhost. "
                    "Use firewall rules to restrict access. Disable dangerous commands."
                ),
            },
            9200: {
                "title": "Elasticsearch Service Exposed",
                "description": (
                    "Elasticsearch API is accessible. Unauthenticated Elasticsearch "
                    "instances have been responsible for major data breaches."
                ),
                "severity": "critical",
                "cvss_score": 9.5,
                "remediation": (
                    "Enable X-Pack Security or OpenSearch security plugin. "
                    "Require authentication. Bind to private interfaces. "
                    "Use TLS for all connections."
                ),
            },
            27017: {
                "title": "MongoDB Service Exposed",
                "description": (
                    "MongoDB is accessible on the network. Misconfigured MongoDB "
                    "instances are a leading cause of database ransomware."
                ),
                "severity": "critical",
                "cvss_score": 9.5,
                "remediation": (
                    "Enable authentication (--auth flag). Bind to localhost. "
                    "Use TLS/SSL. Implement IP whitelisting. "
                    "Disable REST API and HTTP interface."
                ),
            },
        }

        for port_result in open_ports:
            port = port_result.port

            if port in dangerous_services:
                finding_template = dangerous_services[port]
                findings.append({
                    "id": f"NET-{port:05d}",
                    "category": "Network Security",
                    "title": finding_template["title"],
                    "description": finding_template["description"],
                    "target": target,
                    "port": port,
                    "service": port_result.service,
                    "banner": port_result.banner,
                    "severity": finding_template["severity"],
                    "cvss_score": finding_template["cvss_score"],
                    "remediation": finding_template["remediation"],
                    "evidence": (
                        f"Port {port}/{port_result.service} is open on {target}. "
                        f"Banner: {port_result.banner or 'N/A'}"
                    ),
                    "compliance_refs": self._get_compliance_refs(port),
                    "discovered_at": datetime.now().isoformat(),
                })

        # General finding: excessive open ports
        if len(open_ports) > 10:
            findings.append({
                "id": "NET-EXCESS",
                "category": "Network Security",
                "title": "Excessive Number of Open Ports",
                "description": (
                    f"{len(open_ports)} open ports detected. A large attack surface "
                    "increases the probability of exploitation."
                ),
                "target": target,
                "port": None,
                "service": "multiple",
                "banner": "",
                "severity": "medium",
                "cvss_score": 5.0,
                "remediation": (
                    "Review all open services and disable unnecessary ones. "
                    "Implement the principle of least privilege for network services. "
                    "Use host-based firewalls to restrict access."
                ),
                "evidence": (
                    f"Total open ports: {len(open_ports)}. "
                    f"Ports: {', '.join(str(p.port) for p in open_ports[:20])}"
                    f"{'...' if len(open_ports) > 20 else ''}"
                ),
                "compliance_refs": ["ISO 27001 A.13.1.1", "PCI-DSS Req 1.1.6"],
                "discovered_at": datetime.now().isoformat(),
            })

        return findings

    def _get_compliance_refs(self, port: int) -> List[str]:
        """
        Get compliance framework references for a port-related finding.

        Args:
            port: The port number.

        Returns:
            List of compliance reference strings.
        """
        refs = ["ISO 27001 A.13.1.1"]  # Network controls

        if port in HIGH_RISK_PORTS:
            refs.extend([
                "PCI-DSS Req 1.1.6",
                "PCI-DSS Req 2.2.2",
                "NIST CSF PR.AC-5",
            ])

        if port in (1433, 3306, 5432, 27017, 9200, 6379):
            refs.append("PCI-DSS Req 6.5.3")

        if port in (3389, 5900, 23):
            refs.append("NIST CSF PR.AC-3")

        return refs

    def scan_common_ports(self, target: str) -> NetworkScanResult:
        """
        Quick scan of the most commonly targeted ports.

        Scans a curated list of high-value ports rather than a full range,
        providing faster results for initial reconnaissance.

        Args:
            target: IP address or hostname to scan.

        Returns:
            NetworkScanResult for the common ports.
        """
        common_ports = sorted(COMMON_SERVICES.keys())
        return self.scan(target, specific_ports=common_ports)

    def validate_target(self, target: str) -> bool:
        """
        Validate that a target is reachable before scanning.

        Args:
            target: IP address or hostname to validate.

        Returns:
            True if the target is reachable, False otherwise.
        """
        try:
            socket.gethostbyname(target)
            return True
        except socket.gaierror:
            return False
