"""
Command-Line Interface for the Web Application Security Scanner
================================================================
Provides a Click-based CLI for running security scans with
configurable modules, output formats, and verbosity levels.

Usage:
    python -m scanner.cli scan --target http://127.0.0.1:5000 --output report.html
    python -m scanner.cli scan --target http://127.0.0.1:5000 --modules headers,sqli
    python -m scanner.cli scan --verbose

ETHICAL USE ONLY: Only scan targets you own or have written authorization to test.
"""

import os
import sys
import time
from datetime import datetime

import click
import requests
import urllib3

# Suppress insecure request warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner.header_check import check_headers
from scanner.sqli_scanner import scan_sqli
from scanner.xss_scanner import scan_xss
from scanner.port_scanner import scan_ports
from scanner.directory_scanner import scan_directories
from scanner.reporter import (
    build_report, render_html_report, render_json_report, print_summary
)


BANNER = r"""
 __        __   _        _                ____
 \ \      / /__| |__    / \   _ __  _ __ / ___|  ___ __ _ _ __
  \ \ /\ / / _ \ '_ \  / _ \ | '_ \| '_ \\___ \ / __/ _` | '_ \
   \ V  V /  __/ |_) |/ ___ \| |_) | |_) |___) | (_| (_| | | | |
    \_/\_/ \___|_.__//_/   \_\ .__/| .__/|____/ \___\__,_|_| |_|
                              |_|   |_|
    Web Application Security Scanner v1.0.0
"""

DISCLAIMER = """
+==========================================================================+
|                      ETHICAL USE DISCLAIMER                               |
|                                                                           |
|  This tool is for AUTHORIZED security testing ONLY.                       |
|  You MUST have written permission to scan the target system.              |
|  Unauthorized scanning is ILLEGAL and may result in prosecution.          |
|  The authors assume NO LIABILITY for misuse.                              |
+==========================================================================+
"""

AVAILABLE_MODULES = {
    'headers': 'HTTP Security Header Analysis',
    'sqli': 'SQL Injection Scanner',
    'xss': 'Cross-Site Scripting Scanner',
    'ports': 'TCP Port Scanner',
    'dirs': 'Directory Enumeration Scanner',
}


def validate_target(target_url: str) -> bool:
    """Validate that the target is reachable."""
    try:
        response = requests.get(target_url, timeout=10, verify=False)
        return True
    except requests.exceptions.ConnectionError:
        return False
    except requests.exceptions.RequestException:
        return False


@click.group()
@click.version_option(version='1.0.0', prog_name='WebAppScanner')
def cli():
    """Web Application Security Scanner - CLI Interface.

    A modular security scanner for identifying common web application
    vulnerabilities based on the OWASP Top 10 methodology.

    Use 'scan' command to run a security assessment.
    """
    pass


@cli.command()
@click.option(
    '--target', '-t',
    default='http://127.0.0.1:5000',
    help='Target URL to scan (default: http://127.0.0.1:5000)'
)
@click.option(
    '--output', '-o',
    default=None,
    help='Output file path for the report (e.g., reports/scan_report.html)'
)
@click.option(
    '--format', '-f', 'output_format',
    type=click.Choice(['html', 'json', 'both'], case_sensitive=False),
    default='html',
    help='Report output format (default: html)'
)
@click.option(
    '--modules', '-m',
    default='all',
    help='Comma-separated modules: headers,sqli,xss,ports,dirs (default: all)'
)
@click.option(
    '--timeout',
    default=10,
    type=int,
    help='Request timeout in seconds (default: 10)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    default=False,
    help='Enable verbose output'
)
@click.option(
    '--port-scan-type',
    type=click.Choice(['quick', 'full'], case_sensitive=False),
    default='quick',
    help='Port scan type: quick (common ports) or full (1-1024+) (default: quick)'
)
@click.option(
    '--accept-disclaimer',
    is_flag=True,
    default=False,
    help='Accept the ethical use disclaimer without prompting'
)
def scan(target, output, output_format, modules, timeout, verbose,
         port_scan_type, accept_disclaimer):
    """Run a security scan against a target web application.

    Examples:

        # Full scan against localhost vulnerable app
        python -m scanner.cli scan --target http://127.0.0.1:5000

        # Scan specific modules only
        python -m scanner.cli scan -t http://127.0.0.1:5000 -m headers,sqli

        # Verbose scan with JSON output
        python -m scanner.cli scan -t http://127.0.0.1:5000 -v -f json

        # Save report to specific path
        python -m scanner.cli scan -o reports/my_report.html
    """
    click.echo(BANNER)
    click.echo(DISCLAIMER)

    # Confirm ethical use
    if not accept_disclaimer:
        click.echo("  Do you have authorization to scan the target system?")
        confirmed = click.confirm("  Type 'y' to confirm and proceed", default=False)
        if not confirmed:
            click.echo("\n  [!] Scan aborted. Only scan systems you are authorized to test.")
            sys.exit(0)

    click.echo()

    # Parse modules
    if modules.lower() == 'all':
        selected_modules = list(AVAILABLE_MODULES.keys())
    else:
        selected_modules = [m.strip().lower() for m in modules.split(',')]
        invalid = [m for m in selected_modules if m not in AVAILABLE_MODULES]
        if invalid:
            click.echo(f"  [!] Invalid modules: {', '.join(invalid)}")
            click.echo(f"  [*] Available: {', '.join(AVAILABLE_MODULES.keys())}")
            sys.exit(1)

    # Display scan configuration
    click.echo("  SCAN CONFIGURATION:")
    click.echo(f"  Target:     {target}")
    click.echo(f"  Modules:    {', '.join(selected_modules)}")
    click.echo(f"  Timeout:    {timeout}s")
    click.echo(f"  Verbose:    {verbose}")
    click.echo(f"  Format:     {output_format}")
    click.echo()

    # Validate target connectivity
    click.echo(f"  [*] Validating target connectivity...")
    if not validate_target(target):
        click.echo(f"  [!] Cannot connect to {target}")
        click.echo(f"  [!] Ensure the target is running and accessible.")
        click.echo(f"  [!] For the vulnerable app: cd vulnerable_app && python app.py")
        sys.exit(1)
    click.echo(f"  [+] Target is reachable.")
    click.echo()

    # Initialize results storage
    scan_start = datetime.now()
    header_results = None
    sqli_results = None
    xss_results = None
    port_results = None
    directory_results = None
    total_requests = 0

    # -----------------------------------------------------------------------
    # Execute selected scan modules
    # -----------------------------------------------------------------------

    # Module 1: Security Headers
    if 'headers' in selected_modules:
        click.echo("=" * 70)
        click.echo("  MODULE: HTTP Security Header Analysis")
        click.echo("=" * 70)
        header_results = check_headers(target, timeout=timeout, verbose=verbose)
        total_requests += 1
        click.echo()

    # Module 2: SQL Injection
    if 'sqli' in selected_modules:
        click.echo("=" * 70)
        click.echo("  MODULE: SQL Injection Scanner")
        click.echo("=" * 70)
        sqli_results = scan_sqli(target, timeout=timeout, verbose=verbose)
        total_requests += sqli_results.payloads_sent
        click.echo()

    # Module 3: Cross-Site Scripting
    if 'xss' in selected_modules:
        click.echo("=" * 70)
        click.echo("  MODULE: Cross-Site Scripting Scanner")
        click.echo("=" * 70)
        xss_results = scan_xss(target, timeout=timeout, verbose=verbose)
        total_requests += xss_results.payloads_sent
        click.echo()

    # Module 4: Port Scanner
    if 'ports' in selected_modules:
        click.echo("=" * 70)
        click.echo("  MODULE: TCP Port Scanner")
        click.echo("=" * 70)
        port_results = scan_ports(
            target,
            scan_type=port_scan_type,
            timeout=min(timeout, 3),
            verbose=verbose
        )
        total_requests += port_results.total_ports_scanned
        click.echo()

    # Module 5: Directory Enumeration
    if 'dirs' in selected_modules:
        click.echo("=" * 70)
        click.echo("  MODULE: Directory Enumeration Scanner")
        click.echo("=" * 70)
        directory_results = scan_directories(
            target, timeout=timeout, verbose=verbose
        )
        total_requests += directory_results.paths_checked
        click.echo()

    # -----------------------------------------------------------------------
    # Build and generate report
    # -----------------------------------------------------------------------

    scan_end = datetime.now()

    click.echo("=" * 70)
    click.echo("  GENERATING REPORT")
    click.echo("=" * 70)

    report = build_report(
        target_url=target,
        scan_start=scan_start,
        scan_end=scan_end,
        modules_executed=selected_modules,
        header_results=header_results,
        sqli_results=sqli_results,
        xss_results=xss_results,
        port_results=port_results,
        directory_results=directory_results,
        total_requests=total_requests,
    )

    # Generate default output path if not specified
    if output is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        reports_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'reports'
        )
        os.makedirs(reports_dir, exist_ok=True)

        if output_format in ('html', 'both'):
            output = os.path.join(reports_dir, f'scan_report_{timestamp}.html')
        else:
            output = os.path.join(reports_dir, f'scan_report_{timestamp}.json')

    # Render report(s)
    if output_format in ('html', 'both'):
        html_path = output if output.endswith('.html') else output + '.html'
        render_html_report(report, html_path)

    if output_format in ('json', 'both'):
        json_path = output.replace('.html', '.json') if output.endswith('.html') else output
        if not json_path.endswith('.json'):
            json_path += '.json'
        render_json_report(report, json_path)

    # Print summary
    print_summary(report)

    click.echo()
    click.echo("  Scan complete. Review the report for detailed findings.")
    click.echo("  Remember: Only use findings for authorized remediation.")
    click.echo()


@cli.command()
def modules():
    """List available scan modules."""
    click.echo("\n  Available Scan Modules:\n")
    for name, description in AVAILABLE_MODULES.items():
        click.echo(f"    {name:<12s} - {description}")
    click.echo()
    click.echo("  Usage: python -m scanner.cli scan --modules headers,sqli,xss")
    click.echo()


@cli.command()
@click.option('--target', '-t', default='http://127.0.0.1:5000',
              help='Target URL to check')
def check(target):
    """Quick connectivity check for the target."""
    click.echo(f"\n  [*] Checking connectivity to: {target}")

    if validate_target(target):
        click.echo(f"  [+] Target is reachable!")
        try:
            response = requests.get(target, timeout=10, verify=False)
            click.echo(f"  [+] Status Code: {response.status_code}")
            click.echo(f"  [+] Server: {response.headers.get('Server', 'N/A')}")
            click.echo(f"  [+] Content-Length: {len(response.content)} bytes")
        except Exception:
            pass
    else:
        click.echo(f"  [!] Target is NOT reachable.")
        click.echo(f"  [!] Ensure the application is running.")
    click.echo()


if __name__ == '__main__':
    cli()
