"""
TCP Port Scanner
===================
A multi-threaded TCP connect scanner for identifying open ports
and running services on the target host.

Features:
- Configurable port range and common port presets
- Service identification based on port numbers
- Multi-threaded scanning with configurable thread count
- Connection timeout handling
- Banner grabbing for service version detection
- Severity classification based on service type

ETHICAL USE ONLY: Only scan systems you own or have written authorization to test.
Port scanning without authorization may be illegal in your jurisdiction.
"""

import socket
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse


@dataclass
class PortFinding:
    """Represents an open port finding."""
    port: int
    state: str  # open, closed, filtered
    service: str
    banner: Optional[str]
    severity: str
    description: str
    recommendation: str


@dataclass
class PortScanResult:
    """Complete result of a port scan."""
    target_host: str
    target_ip: str
    findings: List[PortFinding] = field(default_factory=list)
    open_ports: List[int] = field(default_factory=list)
    closed_ports: int = 0
    filtered_ports: int = 0
    total_ports_scanned: int = 0
    scan_duration: float = 0.0
    errors: List[str] = field(default_factory=list)


# Well-known service ports and their metadata
COMMON_PORTS = {
    21: {'service': 'FTP', 'severity': 'High',
         'description': 'FTP service detected. FTP transmits data including '
                        'credentials in plaintext.',
         'recommendation': 'Replace FTP with SFTP or SCP. If FTP is required, '
                           'ensure it uses TLS (FTPS) and restrict access.'},
    22: {'service': 'SSH', 'severity': 'Informational',
         'description': 'SSH service detected. SSH provides encrypted remote access.',
         'recommendation': 'Use key-based authentication. Disable password auth. '
                           'Keep SSH updated and use fail2ban.'},
    23: {'service': 'Telnet', 'severity': 'Critical',
         'description': 'Telnet service detected. Telnet transmits all data '
                        'including passwords in plaintext.',
         'recommendation': 'Disable Telnet immediately. Replace with SSH for '
                           'remote access.'},
    25: {'service': 'SMTP', 'severity': 'Medium',
         'description': 'SMTP mail service detected. May be vulnerable to '
                        'open relay or user enumeration.',
         'recommendation': 'Configure SMTP to prevent open relay. Enable '
                           'STARTTLS. Implement SPF, DKIM, and DMARC.'},
    53: {'service': 'DNS', 'severity': 'Low',
         'description': 'DNS service detected.',
         'recommendation': 'Ensure DNS is properly configured. Disable zone '
                           'transfers to unauthorized hosts. Enable DNSSEC.'},
    80: {'service': 'HTTP', 'severity': 'Medium',
         'description': 'HTTP web server detected. Traffic is unencrypted.',
         'recommendation': 'Redirect HTTP to HTTPS. Implement HSTS header.'},
    110: {'service': 'POP3', 'severity': 'High',
          'description': 'POP3 mail service detected. POP3 transmits '
                         'credentials in plaintext.',
          'recommendation': 'Use POP3S (POP3 over TLS) or switch to IMAP '
                            'with TLS.'},
    135: {'service': 'MSRPC', 'severity': 'High',
          'description': 'Microsoft RPC endpoint mapper detected. Commonly '
                         'targeted by worms and exploits.',
          'recommendation': 'Block port 135 at the firewall. Restrict '
                            'access to trusted networks only.'},
    139: {'service': 'NetBIOS', 'severity': 'High',
          'description': 'NetBIOS session service detected. Can expose '
                         'file shares and system information.',
          'recommendation': 'Disable NetBIOS over TCP/IP if not needed. '
                            'Block at the firewall.'},
    143: {'service': 'IMAP', 'severity': 'High',
          'description': 'IMAP mail service detected. Plaintext IMAP exposes '
                         'credentials.',
          'recommendation': 'Use IMAPS (IMAP over TLS on port 993) instead.'},
    443: {'service': 'HTTPS', 'severity': 'Informational',
          'description': 'HTTPS web server detected. Traffic is encrypted.',
          'recommendation': 'Ensure TLS 1.2+ is used. Check certificate '
                            'validity and strength.'},
    445: {'service': 'SMB', 'severity': 'High',
          'description': 'SMB file sharing service detected. Historically '
                         'targeted by major exploits (EternalBlue, WannaCry).',
          'recommendation': 'Block SMB at the firewall for external access. '
                            'Disable SMBv1. Keep systems patched.'},
    993: {'service': 'IMAPS', 'severity': 'Informational',
          'description': 'IMAP over TLS service detected.',
          'recommendation': 'Ensure strong TLS configuration.'},
    995: {'service': 'POP3S', 'severity': 'Informational',
          'description': 'POP3 over TLS service detected.',
          'recommendation': 'Ensure strong TLS configuration.'},
    1433: {'service': 'MSSQL', 'severity': 'Critical',
           'description': 'Microsoft SQL Server detected. Database servers '
                          'should never be directly exposed.',
           'recommendation': 'Block external access to MSSQL. Use a VPN or '
                             'SSH tunnel for remote database access.'},
    1521: {'service': 'Oracle DB', 'severity': 'Critical',
           'description': 'Oracle database listener detected. Direct exposure '
                          'is a critical security risk.',
           'recommendation': 'Block external access to Oracle. Use application '
                             'tiers for database interaction.'},
    3306: {'service': 'MySQL', 'severity': 'Critical',
           'description': 'MySQL database server detected. Direct exposure '
                          'allows brute-force and exploitation.',
           'recommendation': 'Block external access to MySQL. Bind to '
                             '127.0.0.1. Use SSH tunnels for remote access.'},
    3389: {'service': 'RDP', 'severity': 'High',
           'description': 'Remote Desktop Protocol detected. RDP is frequently '
                          'targeted for brute-force and exploitation.',
           'recommendation': 'Use a VPN for RDP access. Enable NLA. '
                             'Implement account lockout and MFA.'},
    5432: {'service': 'PostgreSQL', 'severity': 'Critical',
           'description': 'PostgreSQL database server detected. Direct exposure '
                          'is a critical security risk.',
           'recommendation': 'Block external access. Configure pg_hba.conf '
                             'to restrict connections.'},
    5900: {'service': 'VNC', 'severity': 'High',
           'description': 'VNC remote desktop service detected. VNC often lacks '
                          'strong authentication.',
           'recommendation': 'Use VNC over SSH tunnel. Set strong passwords. '
                             'Consider alternatives like RDP with NLA.'},
    6379: {'service': 'Redis', 'severity': 'Critical',
           'description': 'Redis in-memory database detected. Redis often has '
                          'no authentication by default.',
           'recommendation': 'Never expose Redis to the internet. Set a strong '
                             'password. Bind to 127.0.0.1.'},
    8080: {'service': 'HTTP-Alt', 'severity': 'Medium',
           'description': 'Alternative HTTP service detected. May be a proxy, '
                          'application server, or development server.',
           'recommendation': 'Determine the purpose of this service. Apply '
                             'same security as production HTTP.'},
    8443: {'service': 'HTTPS-Alt', 'severity': 'Low',
           'description': 'Alternative HTTPS service detected.',
           'recommendation': 'Ensure proper TLS configuration.'},
    8888: {'service': 'HTTP-Alt', 'severity': 'Medium',
           'description': 'Alternative HTTP service on port 8888.',
           'recommendation': 'Investigate and secure or close this port.'},
    27017: {'service': 'MongoDB', 'severity': 'Critical',
            'description': 'MongoDB database detected. MongoDB has historically '
                           'been deployed without authentication.',
            'recommendation': 'Enable authentication. Bind to 127.0.0.1. '
                              'Never expose MongoDB to the internet.'},
}

# Quick scan ports (most common)
QUICK_SCAN_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 135, 139, 143,
    443, 445, 993, 995, 1433, 1521, 3306, 3389,
    5432, 5900, 6379, 8080, 8443, 8888, 27017
]

# Full scan includes additional ports
FULL_SCAN_PORTS = list(range(1, 1025)) + [
    1433, 1521, 2049, 3306, 3389, 5432, 5900, 5984,
    6379, 8000, 8080, 8443, 8888, 9090, 9200, 9300,
    11211, 27017, 50000
]


def _resolve_host(target: str) -> Tuple[str, str]:
    """
    Resolve the target to a hostname and IP address.

    Args:
        target: URL or hostname

    Returns:
        (hostname, ip_address) tuple
    """
    # Parse URL if provided
    parsed = urlparse(target)
    hostname = parsed.hostname or target

    # Remove port from hostname if present
    if ':' in hostname and not hostname.startswith('['):
        hostname = hostname.split(':')[0]

    try:
        ip_address = socket.gethostbyname(hostname)
    except socket.gaierror:
        ip_address = hostname

    return hostname, ip_address


def _scan_port(
    host: str,
    port: int,
    timeout: float = 2.0
) -> PortFinding:
    """
    Scan a single port using TCP connect.

    Args:
        host: Target host IP or hostname
        port: Port number to scan
        timeout: Connection timeout in seconds

    Returns:
        PortFinding with the result
    """
    port_info = COMMON_PORTS.get(port, {
        'service': f'unknown-{port}',
        'severity': 'Low',
        'description': f'Service detected on port {port}.',
        'recommendation': 'Investigate the purpose of this service and '
                          'ensure it is properly secured.',
    })

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        result = sock.connect_ex((host, port))

        if result == 0:
            # Port is open - attempt banner grab
            banner = None
            try:
                sock.settimeout(2.0)
                # Send a minimal request for banner
                if port in [80, 8080, 8443, 8888]:
                    sock.send(b'HEAD / HTTP/1.0\r\n\r\n')
                else:
                    sock.send(b'\r\n')
                banner_data = sock.recv(1024)
                banner = banner_data.decode('utf-8', errors='replace').strip()
                if len(banner) > 200:
                    banner = banner[:200] + '...'
            except (socket.timeout, ConnectionResetError, OSError):
                pass

            sock.close()

            return PortFinding(
                port=port,
                state='open',
                service=port_info['service'],
                banner=banner,
                severity=port_info['severity'],
                description=port_info['description'],
                recommendation=port_info['recommendation'],
            )
        else:
            sock.close()
            return PortFinding(
                port=port,
                state='closed',
                service=port_info['service'],
                banner=None,
                severity='Informational',
                description=f'Port {port} is closed.',
                recommendation='No action needed.',
            )

    except socket.timeout:
        return PortFinding(
            port=port,
            state='filtered',
            service=port_info['service'],
            banner=None,
            severity='Low',
            description=(
                f'Port {port} ({port_info["service"]}) appears to be filtered. '
                f'A firewall may be blocking the connection.'
            ),
            recommendation='Verify firewall rules are intentional.',
        )
    except OSError as e:
        return PortFinding(
            port=port,
            state='error',
            service=port_info['service'],
            banner=None,
            severity='Informational',
            description=f'Error scanning port {port}: {str(e)}',
            recommendation='Check network connectivity.',
        )


def scan_ports(
    target: str,
    ports: Optional[List[int]] = None,
    scan_type: str = 'quick',
    timeout: float = 2.0,
    max_threads: int = 50,
    verbose: bool = False
) -> PortScanResult:
    """
    Run a multi-threaded TCP port scan against the target.

    Args:
        target: Target URL or hostname
        ports: Specific ports to scan (overrides scan_type)
        scan_type: 'quick' (common ports) or 'full' (1-1024 + extras)
        timeout: Connection timeout per port in seconds
        max_threads: Maximum concurrent scanning threads
        verbose: Enable verbose output

    Returns:
        PortScanResult with all findings
    """
    start_time = time.time()

    hostname, ip_address = _resolve_host(target)

    result = PortScanResult(
        target_host=hostname,
        target_ip=ip_address,
    )

    # Determine ports to scan
    if ports:
        scan_ports_list = sorted(set(ports))
    elif scan_type == 'full':
        scan_ports_list = FULL_SCAN_PORTS
    else:
        scan_ports_list = QUICK_SCAN_PORTS

    result.total_ports_scanned = len(scan_ports_list)

    print(f"[*] Starting port scan...")
    print(f"[*] Target: {hostname} ({ip_address})")
    print(f"[*] Scan type: {scan_type}")
    print(f"[*] Ports to scan: {len(scan_ports_list)}")
    print(f"[*] Threads: {max_threads}")
    print(f"[*] Timeout: {timeout}s per port")
    print()

    # Thread-safe counter for progress
    scanned_count = 0
    count_lock = threading.Lock()

    def scan_with_progress(port):
        nonlocal scanned_count
        finding = _scan_port(ip_address, port, timeout)
        with count_lock:
            scanned_count += 1
            if verbose:
                if finding.state == 'open':
                    print(f"  [+] Port {port:5d}/tcp  OPEN    {finding.service}")
                elif finding.state == 'filtered':
                    print(f"  [?] Port {port:5d}/tcp  FILTERED  {finding.service}")
            elif scanned_count % 100 == 0:
                print(f"  [*] Progress: {scanned_count}/{len(scan_ports_list)} ports scanned...")
        return finding

    # Execute scan with thread pool
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {
            executor.submit(scan_with_progress, port): port
            for port in scan_ports_list
        }

        for future in as_completed(futures):
            port = futures[future]
            try:
                finding = future.result()
                if finding.state == 'open':
                    result.findings.append(finding)
                    result.open_ports.append(finding.port)
                elif finding.state == 'closed':
                    result.closed_ports += 1
                elif finding.state == 'filtered':
                    result.filtered_ports += 1
                    result.findings.append(finding)
            except Exception as e:
                result.errors.append(f"Port {port}: {str(e)}")

    # Sort findings by port number
    result.findings.sort(key=lambda f: f.port)
    result.open_ports.sort()

    result.scan_duration = time.time() - start_time

    print()
    print(f"[*] Port scan complete")
    print(f"[*] Duration: {result.scan_duration:.2f}s")
    print(f"[*] Open ports: {len(result.open_ports)}")
    print(f"[*] Closed ports: {result.closed_ports}")
    print(f"[*] Filtered ports: {result.filtered_ports}")

    if result.open_ports:
        print(f"[*] Open ports: {', '.join(str(p) for p in result.open_ports)}")

    return result


def format_port_report(result: PortScanResult) -> str:
    """Format the port scan result as a text report."""
    lines = [
        "=" * 70,
        "  TCP PORT SCAN REPORT",
        "=" * 70,
        f"  Target: {result.target_host} ({result.target_ip})",
        f"  Ports Scanned: {result.total_ports_scanned}",
        f"  Open: {len(result.open_ports)} | Closed: {result.closed_ports} | "
        f"Filtered: {result.filtered_ports}",
        f"  Duration: {result.scan_duration:.2f}s",
        "=" * 70,
        "",
        "  PORT      STATE     SERVICE         SEVERITY",
        "  " + "-" * 55,
    ]

    for finding in result.findings:
        if finding.state == 'open':
            lines.append(
                f"  {finding.port:<9d} {finding.state:<9s} {finding.service:<15s} "
                f"{finding.severity}"
            )
            if finding.banner:
                banner_short = finding.banner.split('\n')[0][:60]
                lines.append(f"            Banner: {banner_short}")

    lines.append("")
    return "\n".join(lines)


if __name__ == '__main__':
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5000'
    verbose = '--verbose' in sys.argv
    scan_type = 'full' if '--full' in sys.argv else 'quick'

    result = scan_ports(target, scan_type=scan_type, verbose=verbose)
    print()
    print(format_port_report(result))
