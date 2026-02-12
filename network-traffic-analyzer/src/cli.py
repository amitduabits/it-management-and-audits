"""
CLI Module
==========

Click-based command-line interface for the Network Traffic Analyzer.

Subcommands
-----------
- ``parse``     -- Parse a PCAP file and export packet metadata as JSON.
- ``analyze``   -- Run statistical analysis and print results.
- ``detect``    -- Run anomaly detection and print findings.
- ``visualize`` -- Generate charts from a PCAP file.
- ``report``    -- Generate a full Markdown or HTML analysis report.

Usage::

    python -m src.cli parse capture.pcap --output parsed.json
    python -m src.cli analyze capture.pcap
    python -m src.cli detect capture.pcap --port-threshold 20
    python -m src.cli visualize capture.pcap --output-dir charts/
    python -m src.cli report capture.pcap --format html --output report.html

WARNING: Only analyze PCAP files captured from networks you are authorized
to monitor. Unauthorized traffic analysis may violate applicable laws.
"""

import json
import sys

import click

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from src.parser import parse_pcap, export_json, get_parser_backend
from src.analyzer import (
    full_analysis,
    protocol_distribution,
    protocol_distribution_pct,
    top_source_ips,
    top_dest_ips,
    top_talkers,
    destination_port_frequency,
    bandwidth_per_ip,
    bandwidth_summary,
)
from src.anomaly_detector import run_all_detectors, summarize_findings
from src.visualizer import generate_all_charts
from src.reporter import (
    generate_markdown_report,
    generate_html_report,
    write_report,
)


# ===================================================================
# Helpers
# ===================================================================

def _console() -> "Console":
    """Lazy-create a Rich console."""
    return Console(stderr=True)


def _print_disclaimer() -> None:
    """Print a legal disclaimer before analysis."""
    msg = (
        "NOTICE: This tool is for authorized network analysis only. "
        "Ensure you have permission to analyze the target PCAP file."
    )
    if RICH_AVAILABLE:
        _console().print(Panel(msg, title="Disclaimer", style="yellow"))
    else:
        click.echo(f"[!] {msg}")


def _fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024:
            return f"{n:,.1f} {unit}"
        n /= 1024  # type: ignore[assignment]
    return f"{n:,.1f} TB"


# ===================================================================
# CLI Group
# ===================================================================

@click.group()
@click.version_option(version="1.0.0", prog_name="network-traffic-analyzer")
def cli():
    """
    Network Traffic Analyzer -- parse, analyze, and visualize PCAP files.

    Designed for security researchers and network administrators. Only
    analyze traffic you are authorized to inspect.
    """
    pass


# ===================================================================
# parse
# ===================================================================

@cli.command()
@click.argument("pcap_file", type=click.Path(exists=True))
@click.option("--output", "-o", default=None, help="Output JSON file path.")
@click.option("--fallback", is_flag=True, help="Force the pure-Python fallback parser.")
@click.option("--limit", "-n", default=0, type=int, help="Only parse first N packets (0 = all).")
def parse(pcap_file: str, output: str, fallback: bool, limit: int):
    """Parse a PCAP file and export packet metadata as JSON."""
    _print_disclaimer()

    backend = "fallback (forced)" if fallback else get_parser_backend()
    click.echo(f"[*] Parsing {pcap_file} (backend: {backend}) ...")

    packets = parse_pcap(pcap_file, force_fallback=fallback)

    if limit > 0:
        packets = packets[:limit]

    click.echo(f"[+] Parsed {len(packets)} packets.")

    if output:
        path = export_json(packets, output)
        click.echo(f"[+] Exported to {path}")
    else:
        click.echo(json.dumps(packets[:5], indent=2, default=str))
        if len(packets) > 5:
            click.echo(f"... ({len(packets) - 5} more packets, use --output to save all)")


# ===================================================================
# analyze
# ===================================================================

@cli.command()
@click.argument("pcap_file", type=click.Path(exists=True))
@click.option("--top-n", default=10, type=int, help="Number of top entries to show.")
@click.option("--interval", default=60, type=int, help="Time-series interval in seconds.")
@click.option("--json-output", "-j", default=None, help="Save analysis as JSON.")
def analyze(pcap_file: str, top_n: int, interval: int, json_output: str):
    """Run statistical analysis on a PCAP file."""
    _print_disclaimer()

    click.echo(f"[*] Parsing {pcap_file} ...")
    packets = parse_pcap(pcap_file)
    click.echo(f"[+] Parsed {len(packets)} packets. Running analysis ...")

    results = full_analysis(packets, top_n=top_n, interval=interval)

    if json_output:
        with open(json_output, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2, default=str)
        click.echo(f"[+] Analysis saved to {json_output}")
        return

    # Pretty-print with Rich if available
    if RICH_AVAILABLE:
        console = _console()

        # Summary
        summary = results["summary"]
        tbl = Table(title="Capture Summary", show_header=True)
        tbl.add_column("Metric", style="bold")
        tbl.add_column("Value", justify="right")
        tbl.add_row("Total packets", f"{summary['total_packets']:,}")
        tbl.add_row("Total bytes", _fmt_bytes(summary["total_bytes"]))
        tbl.add_row("Avg packet size", f"{summary['avg_packet_size']:.1f} B")
        tbl.add_row("Duration", f"{summary['duration_seconds']:.2f} s")
        tbl.add_row("Avg pkt/sec", f"{summary['avg_packets_per_second']:.1f}")
        tbl.add_row("Avg bytes/sec", _fmt_bytes(int(summary["avg_bytes_per_second"])))
        console.print(tbl)

        # Protocol distribution
        proto = results["protocol_distribution"]
        proto_pct = results["protocol_distribution_pct"]
        tbl = Table(title="Protocol Distribution")
        tbl.add_column("Protocol", style="cyan")
        tbl.add_column("Packets", justify="right")
        tbl.add_column("%", justify="right")
        for p, c in proto.items():
            tbl.add_row(p, f"{c:,}", f"{proto_pct.get(p, 0):.1f}%")
        console.print(tbl)

        # Top source IPs
        tbl = Table(title="Top Source IPs")
        tbl.add_column("#", justify="right")
        tbl.add_column("IP Address")
        tbl.add_column("Packets", justify="right")
        for i, (ip, c) in enumerate(results["top_source_ips"], 1):
            tbl.add_row(str(i), ip, f"{c:,}")
        console.print(tbl)

        # Top destination IPs
        tbl = Table(title="Top Destination IPs")
        tbl.add_column("#", justify="right")
        tbl.add_column("IP Address")
        tbl.add_column("Packets", justify="right")
        for i, (ip, c) in enumerate(results["top_dest_ips"], 1):
            tbl.add_row(str(i), ip, f"{c:,}")
        console.print(tbl)

        # Port frequency
        tbl = Table(title="Top Destination Ports")
        tbl.add_column("Port", justify="right")
        tbl.add_column("Packets", justify="right")
        for port, c in results["destination_port_frequency"]:
            tbl.add_row(str(port), f"{c:,}")
        console.print(tbl)

    else:
        # Plain text fallback
        summary = results["summary"]
        click.echo("\n--- Capture Summary ---")
        click.echo(f"  Packets:  {summary['total_packets']:,}")
        click.echo(f"  Bytes:    {_fmt_bytes(summary['total_bytes'])}")
        click.echo(f"  Duration: {summary['duration_seconds']:.2f} s")

        click.echo("\n--- Protocol Distribution ---")
        for p, c in results["protocol_distribution"].items():
            pct = results["protocol_distribution_pct"].get(p, 0)
            click.echo(f"  {p:<12} {c:>8,}  ({pct:.1f}%)")

        click.echo("\n--- Top Source IPs ---")
        for ip, c in results["top_source_ips"]:
            click.echo(f"  {ip:<20} {c:>8,}")

        click.echo("\n--- Top Destination IPs ---")
        for ip, c in results["top_dest_ips"]:
            click.echo(f"  {ip:<20} {c:>8,}")

        click.echo("\n--- Top Destination Ports ---")
        for port, c in results["destination_port_frequency"]:
            click.echo(f"  {port:<8} {c:>8,}")


# ===================================================================
# detect
# ===================================================================

@cli.command()
@click.argument("pcap_file", type=click.Path(exists=True))
@click.option("--port-threshold", default=15, type=int,
              help="Port scan threshold (unique ports).")
@click.option("--spike-factor", default=3.0, type=float,
              help="Traffic spike factor (stdevs above mean).")
@click.option("--time-window", default=60, type=int,
              help="Time window for spike detection (seconds).")
@click.option("--dns-entropy", default=4.0, type=float,
              help="DNS query entropy threshold.")
@click.option("--json-output", "-j", default=None, help="Save findings as JSON.")
def detect(pcap_file: str, port_threshold: int, spike_factor: float,
           time_window: int, dns_entropy: float, json_output: str):
    """Run anomaly detection on a PCAP file."""
    _print_disclaimer()

    click.echo(f"[*] Parsing {pcap_file} ...")
    packets = parse_pcap(pcap_file)
    click.echo(f"[+] Parsed {len(packets)} packets. Running detectors ...")

    findings = run_all_detectors(
        packets,
        port_scan_threshold=port_threshold,
        spike_factor=spike_factor,
        time_window=time_window,
        dns_entropy_threshold=dns_entropy,
    )

    summary = summarize_findings(findings)
    click.echo(f"[+] Detection complete: {summary['total']} finding(s).")

    if json_output:
        with open(json_output, "w", encoding="utf-8") as fh:
            json.dump({"summary": summary, "findings": findings}, fh, indent=2, default=str)
        click.echo(f"[+] Findings saved to {json_output}")
        return

    if not findings:
        click.echo("[*] No anomalies detected with current thresholds.")
        return

    if RICH_AVAILABLE:
        console = _console()
        severity_styles = {
            "critical": "bold red",
            "high": "bold yellow",
            "medium": "yellow",
            "low": "green",
        }
        for idx, finding in enumerate(findings, 1):
            style = severity_styles.get(finding["severity"], "white")
            console.print(
                f"\n[{style}][{finding['severity'].upper()}][/{style}] "
                f"#{idx}: {finding['title']}"
            )
            console.print(f"  Category: {finding['category']}")
            console.print(f"  {finding['description']}")
            evidence = finding.get("evidence", {})
            if evidence:
                for k, v in evidence.items():
                    console.print(f"    {k}: {v}", style="dim")
    else:
        for idx, finding in enumerate(findings, 1):
            click.echo(f"\n[{finding['severity'].upper()}] #{idx}: {finding['title']}")
            click.echo(f"  Category: {finding['category']}")
            click.echo(f"  {finding['description']}")


# ===================================================================
# visualize
# ===================================================================

@cli.command()
@click.argument("pcap_file", type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="charts",
              help="Directory to save chart images.")
@click.option("--interval", default=60, type=int,
              help="Time bucket interval in seconds for timeline chart.")
@click.option("--top-n", default=10, type=int,
              help="Number of top entries in bar charts.")
def visualize(pcap_file: str, output_dir: str, interval: int, top_n: int):
    """Generate charts from a PCAP file."""
    _print_disclaimer()

    click.echo(f"[*] Parsing {pcap_file} ...")
    packets = parse_pcap(pcap_file)
    click.echo(f"[+] Parsed {len(packets)} packets. Generating charts ...")

    results = full_analysis(packets, top_n=top_n, interval=interval)
    saved = generate_all_charts(results, output_dir=output_dir)

    click.echo(f"[+] Generated {len(saved)} chart(s):")
    for name, path in saved.items():
        click.echo(f"    {name}: {path}")


# ===================================================================
# report
# ===================================================================

@cli.command()
@click.argument("pcap_file", type=click.Path(exists=True))
@click.option("--format", "fmt", type=click.Choice(["markdown", "html"]),
              default="markdown", help="Report format.")
@click.option("--output", "-o", default=None,
              help="Output file path (default: report.md or report.html).")
@click.option("--chart-dir", default=None,
              help="Directory with chart PNGs to embed in report.")
@click.option("--include-charts", is_flag=True,
              help="Auto-generate charts and include in report.")
@click.option("--top-n", default=10, type=int)
@click.option("--port-threshold", default=15, type=int)
@click.option("--spike-factor", default=3.0, type=float)
def report(pcap_file: str, fmt: str, output: str, chart_dir: str,
           include_charts: bool, top_n: int, port_threshold: int,
           spike_factor: float):
    """Generate a full analysis report from a PCAP file."""
    _print_disclaimer()

    click.echo(f"[*] Parsing {pcap_file} ...")
    packets = parse_pcap(pcap_file)
    click.echo(f"[+] Parsed {len(packets)} packets.")

    click.echo("[*] Running analysis ...")
    analysis = full_analysis(packets, top_n=top_n)

    click.echo("[*] Running anomaly detection ...")
    findings = run_all_detectors(packets, port_scan_threshold=port_threshold,
                                 spike_factor=spike_factor)

    if include_charts:
        chart_dir = chart_dir or "charts"
        click.echo(f"[*] Generating charts in {chart_dir}/ ...")
        generate_all_charts(analysis, output_dir=chart_dir)

    if not output:
        output = "report.html" if fmt == "html" else "report.md"

    click.echo(f"[*] Generating {fmt} report ...")
    if fmt == "html":
        content = generate_html_report(analysis, findings, pcap_file, chart_dir)
    else:
        content = generate_markdown_report(analysis, findings, pcap_file, chart_dir)

    path = write_report(content, output)
    click.echo(f"[+] Report saved to {path}")


# ===================================================================
# Entry point
# ===================================================================

if __name__ == "__main__":
    cli()
