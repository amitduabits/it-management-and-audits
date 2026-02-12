"""
CLI Interface - Command-line entry point for SecureAudit Pro.

Provides the following commands:
    scan-network      Perform TCP port scan and service detection
    scan-web          Analyze web application security headers
    scan-dns          Enumerate DNS records for a domain
    check-compliance  Run compliance checks against frameworks
    calculate-risk    Calculate weighted risk scores
    generate-report   Generate HTML assessment reports
    start-dashboard   Launch the web dashboard
    full-assessment   Run complete assessment pipeline

Usage:
    python -m src.cli --help
    python -m src.cli scan-network --target 192.168.1.1
    python -m src.cli full-assessment --target example.com

ETHICAL USE NOTICE:
    Only scan systems you own or have explicit written authorization to test.
"""

import sys
import os
import json
import logging
from datetime import datetime

import click

# Configure rich console output if available
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import print as rprint
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

logger = logging.getLogger("secureaudit")


def setup_logging(verbose: bool = False):
    """Configure logging for the CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def print_banner():
    """Print the application banner."""
    banner = """
 ____                            _             _ _ _   ____
/ ___|  ___  ___ _   _ _ __ ___/ \\  _   _  __| (_) |_|  _ \\ _ __ ___
\\___ \\ / _ \\/ __| | | | '__/ _ \\ | | | | |/ _` | | __| |_) | '__/ _ \\
 ___) |  __/ (__| |_| | | |  __/ |_| |_| | (_| | | |_|  __/| | | (_) |
|____/ \\___|\\___|\\__,_|_|  \\___|_|\\__,_|\\__,_|_|\\__|_|   |_|  \\___/
                   Enterprise Security Assessment Platform v1.0
    """
    if RICH_AVAILABLE:
        console.print(Panel(banner.strip(), style="bold blue", border_style="blue"))
    else:
        print(banner)
    print()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, verbose):
    """SecureAudit Pro - Enterprise IT Security Assessment Platform.

    Automated scanning, compliance auditing, risk quantification,
    and executive-ready reporting.

    ETHICAL USE: Only scan systems you own or have authorization to test.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    setup_logging(verbose)


@cli.command("scan-network")
@click.option("--target", "-t", required=True, help="Target IP or hostname")
@click.option("--ports", "-p", default="1-1024", help="Port range (e.g., 1-1024)")
@click.option("--threads", default=50, help="Max concurrent threads")
@click.option("--timeout", default=2.0, help="Connection timeout in seconds")
@click.option("--output", "-o", default=None, help="Output JSON file path")
@click.pass_context
def scan_network(ctx, target, ports, threads, timeout, output):
    """Perform TCP port scan and service detection."""
    print_banner()
    click.echo(f"[*] Starting network scan of {target}...")
    click.echo(f"[*] Port range: {ports} | Threads: {threads} | Timeout: {timeout}s")
    click.echo()

    from src.scanner.network_scanner import NetworkScanner

    # Parse port range
    if "-" in ports:
        start, end = ports.split("-")
        port_range = (int(start), int(end))
        scanner = NetworkScanner(timeout=timeout, max_threads=threads)
        result = scanner.scan(target, port_range=port_range)
    else:
        specific_ports = [int(p.strip()) for p in ports.split(",")]
        scanner = NetworkScanner(timeout=timeout, max_threads=threads)
        result = scanner.scan(target, specific_ports=specific_ports)

    # Display results
    click.echo(f"\n[+] Scan complete in {result.scan_duration_seconds}s")
    click.echo(f"[+] Ports scanned: {result.total_ports_scanned}")
    click.echo(f"[+] Open: {len(result.open_ports)} | Closed: {result.closed_ports} | Filtered: {result.filtered_ports}")

    if result.open_ports:
        click.echo("\n  Open Ports:")
        if RICH_AVAILABLE:
            table = Table(show_header=True, header_style="bold")
            table.add_column("Port", style="cyan")
            table.add_column("Service")
            table.add_column("Risk", justify="center")
            table.add_column("Banner")
            for p in result.open_ports:
                risk_style = {"critical": "red bold", "high": "red", "medium": "yellow", "low": "green"}.get(p.risk_level, "white")
                table.add_row(str(p.port), p.service, f"[{risk_style}]{p.risk_level.upper()}[/]", p.banner[:60] or "N/A")
            console.print(table)
        else:
            for p in result.open_ports:
                click.echo(f"    {p.port:>5}/tcp  {p.service:<16} [{p.risk_level.upper()}]  {p.banner[:50]}")

    if result.findings:
        click.echo(f"\n[!] Security Findings: {len(result.findings)}")
        for f in result.findings:
            click.echo(f"    [{f['severity'].upper()}] {f['title']}")

    # Save output
    if output:
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with open(output, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        click.echo(f"\n[+] Results saved to: {output}")


@cli.command("scan-web")
@click.option("--url", "-u", required=True, help="Target URL (e.g., https://example.com)")
@click.option("--timeout", default=10, help="HTTP request timeout")
@click.option("--output", "-o", default=None, help="Output JSON file path")
@click.pass_context
def scan_web(ctx, url, timeout, output):
    """Analyze web application security headers."""
    print_banner()
    click.echo(f"[*] Starting web security scan of {url}...")

    from src.scanner.web_scanner import WebScanner

    scanner = WebScanner(timeout=timeout)
    result = scanner.scan(url)

    click.echo(f"\n[+] Status Code: {result.status_code}")
    click.echo(f"[+] Response Time: {result.response_time_ms}ms")
    click.echo(f"[+] Security Score: {result.security_score}/100")

    if result.header_findings:
        click.echo("\n  Security Headers:")
        for hf in result.header_findings:
            status_icon = {"present": "+", "missing": "!", "misconfigured": "~"}.get(hf.status, "?")
            click.echo(f"    [{status_icon}] {hf.header_name}: {hf.status.upper()}")

    if result.all_findings:
        click.echo(f"\n[!] Total Findings: {len(result.all_findings)}")
        for f in result.all_findings:
            click.echo(f"    [{f.get('severity', 'info').upper()}] {f.get('title', '')}")

    if output:
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with open(output, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        click.echo(f"\n[+] Results saved to: {output}")


@cli.command("scan-dns")
@click.option("--domain", "-d", required=True, help="Target domain")
@click.option("--output", "-o", default=None, help="Output JSON file path")
@click.pass_context
def scan_dns(ctx, domain, output):
    """Enumerate DNS records for a domain."""
    print_banner()
    click.echo(f"[*] Starting DNS scan for {domain}...")

    from src.scanner.dns_scanner import DNSScanner

    scanner = DNSScanner()
    result = scanner.scan(domain)

    for rtype, records in result.records.items():
        click.echo(f"\n  {rtype} Records ({len(records)}):")
        for r in records:
            click.echo(f"    {r.value}")

    if result.spf:
        click.echo(f"\n  SPF: {'Found' if result.spf.exists else 'Missing'}")
        if result.spf.exists:
            click.echo(f"    Policy: {result.spf.policy}")
    if result.dmarc:
        click.echo(f"  DMARC: {'Found' if result.dmarc.exists else 'Missing'}")
        if result.dmarc.exists:
            click.echo(f"    Policy: {result.dmarc.policy}")
    click.echo(f"  DNSSEC: {'Enabled' if result.has_dnssec else 'Not Enabled'}")

    if result.findings:
        click.echo(f"\n[!] Findings: {len(result.findings)}")
        for f in result.findings:
            click.echo(f"    [{f.get('severity', 'info').upper()}] {f.get('title', '')}")

    if output:
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with open(output, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        click.echo(f"\n[+] Results saved to: {output}")


@cli.command("check-compliance")
@click.option("--framework", "-f", default="all",
              type=click.Choice(["all", "iso27001", "pci-dss", "nist-csf"]),
              help="Compliance framework to check")
@click.option("--input", "-i", "input_file", default=None, help="Input scan data JSON")
@click.option("--output", "-o", default=None, help="Output JSON file path")
@click.pass_context
def check_compliance(ctx, framework, input_file, output):
    """Run compliance checks against security frameworks."""
    print_banner()
    click.echo(f"[*] Running compliance checks: {framework}")

    # Load scan data
    scan_data = {}
    if input_file and os.path.exists(input_file):
        with open(input_file) as f:
            scan_data = json.load(f)

    results = {}

    if framework in ("all", "iso27001"):
        from src.compliance.iso27001 import ISO27001Checker
        checker = ISO27001Checker()
        result = checker.assess(scan_data)
        results["iso27001"] = result.to_dict()
        click.echo(f"\n  ISO 27001: {result.overall_score * 100:.1f}% ({result.passed} pass, {result.failed} fail)")

    if framework in ("all", "pci-dss"):
        from src.compliance.pci_dss import PCIDSSChecker
        checker = PCIDSSChecker()
        result = checker.assess(scan_data)
        results["pci_dss"] = result.to_dict()
        click.echo(f"  PCI-DSS:   {result.overall_score * 100:.1f}% ({result.passed} pass, {result.failed} fail)")

    if framework in ("all", "nist-csf"):
        from src.compliance.nist_csf import NISTCSFChecker
        checker = NISTCSFChecker()
        result = checker.assess(scan_data)
        results["nist_csf"] = result.to_dict()
        click.echo(f"  NIST CSF:  {result.overall_score * 100:.1f}% (Tier {result.overall_tier})")

    if output:
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with open(output, "w") as f:
            json.dump(results, f, indent=2)
        click.echo(f"\n[+] Compliance results saved to: {output}")


@cli.command("calculate-risk")
@click.option("--input", "-i", "input_file", default=None, help="Input scan data JSON")
@click.option("--output", "-o", default=None, help="Output JSON file path")
@click.pass_context
def calculate_risk(ctx, input_file, output):
    """Calculate weighted risk scores."""
    print_banner()
    click.echo("[*] Calculating risk scores...")

    scan_data = {}
    if input_file and os.path.exists(input_file):
        with open(input_file) as f:
            scan_data = json.load(f)

    from src.risk.risk_engine import RiskEngine
    engine = RiskEngine()
    assessment = engine.calculate_risk(scan_data)

    click.echo(f"\n[+] Overall Risk Score: {assessment.overall_risk_score}/10 ({assessment.overall_risk_level.upper()})")
    click.echo(f"[+] Total Findings: {assessment.total_findings}")
    click.echo("\n  Category Scores:")
    for cat in assessment.categories:
        click.echo(f"    {cat.display_name:<25} {cat.raw_score:>5}/10  [{cat.risk_level.upper()}]  (weight: {cat.weight*100:.0f}%)")

    if output:
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with open(output, "w") as f:
            json.dump(assessment.to_dict(), f, indent=2)
        click.echo(f"\n[+] Risk assessment saved to: {output}")


@cli.command("generate-report")
@click.option("--type", "-t", "report_type", default="all",
              type=click.Choice(["all", "executive", "technical", "roadmap"]),
              help="Report type to generate")
@click.option("--input", "-i", "input_file", default=None, help="Input assessment data JSON")
@click.option("--output", "-o", default="./reports", help="Output directory")
@click.option("--organization", default="Organization", help="Organization name")
@click.pass_context
def generate_report(ctx, report_type, input_file, output, organization):
    """Generate HTML assessment reports."""
    print_banner()
    click.echo(f"[*] Generating {report_type} report(s)...")
    os.makedirs(output, exist_ok=True)

    assessment_data = {}
    if input_file and os.path.exists(input_file):
        with open(input_file) as f:
            assessment_data = json.load(f)

    if report_type in ("all", "executive"):
        from src.reporting.executive_report import ExecutiveReportGenerator
        gen = ExecutiveReportGenerator()
        html = gen.generate(
            risk_data=assessment_data.get("risk", {}),
            compliance_data=assessment_data.get("compliance", {}),
            organization=organization,
        )
        path = os.path.join(output, "executive_summary.html")
        gen.save(html, path)
        click.echo(f"  [+] Executive report: {path}")

    if report_type in ("all", "technical"):
        from src.reporting.technical_report import TechnicalReportGenerator
        gen = TechnicalReportGenerator()
        html = gen.generate(
            findings=assessment_data.get("findings", []),
            risk_data=assessment_data.get("risk", {}),
            organization=organization,
        )
        path = os.path.join(output, "technical_report.html")
        gen.save(html, path)
        click.echo(f"  [+] Technical report: {path}")

    if report_type in ("all", "roadmap"):
        from src.reporting.remediation_roadmap import RemediationRoadmapGenerator
        gen = RemediationRoadmapGenerator()
        html = gen.generate(
            findings=assessment_data.get("findings", []),
            risk_data=assessment_data.get("risk", {}),
            compliance_data=assessment_data.get("compliance", {}),
            organization=organization,
        )
        path = os.path.join(output, "remediation_roadmap.html")
        gen.save(html, path)
        click.echo(f"  [+] Remediation roadmap: {path}")


@cli.command("start-dashboard")
@click.option("--host", default="127.0.0.1", help="Dashboard host")
@click.option("--port", default=5000, help="Dashboard port")
@click.option("--input", "-i", "input_file", default=None, help="Assessment data JSON")
@click.pass_context
def start_dashboard(ctx, host, port, input_file):
    """Launch the web dashboard."""
    print_banner()
    click.echo(f"[*] Starting dashboard at http://{host}:{port}")

    assessment_data = None
    if input_file and os.path.exists(input_file):
        with open(input_file) as f:
            assessment_data = json.load(f)

    from dashboard.app import run_dashboard
    run_dashboard(host=host, port=port, assessment_data=assessment_data)


@cli.command("full-assessment")
@click.option("--target", "-t", required=True, help="Target IP/hostname")
@click.option("--url", "-u", default=None, help="Web URL to scan (optional)")
@click.option("--domain", "-d", default=None, help="Domain for DNS scan (optional)")
@click.option("--output", "-o", default="./reports", help="Output directory")
@click.option("--organization", default="Organization", help="Organization name")
@click.pass_context
def full_assessment(ctx, target, url, domain, output, organization):
    """Run complete assessment pipeline."""
    print_banner()
    click.echo("[*] Starting full security assessment...")
    click.echo(f"[*] Target: {target}")

    from src.orchestrator import Orchestrator

    orchestrator = Orchestrator(
        target=target,
        url=url,
        domain=domain,
        output_dir=output,
        organization=organization,
    )
    orchestrator.run()


def main():
    """Entry point for the CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
