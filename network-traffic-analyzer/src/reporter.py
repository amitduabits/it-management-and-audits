"""
Report Generator Module
========================

Produces comprehensive analysis reports in Markdown and HTML formats.
Reports include:

- Capture summary statistics
- Protocol distribution table
- Top source / destination IPs
- Port frequency table
- Bandwidth breakdown
- Anomaly detection findings
- Embedded chart references (for HTML)

WARNING: Only generate reports for traffic you are authorized to analyze.
"""

import os
import html as html_mod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ===================================================================
# Helpers
# ===================================================================

def _fmt_bytes(n: int) -> str:
    """Human-readable byte string."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024:
            return f"{n:,.1f} {unit}"
        n /= 1024  # type: ignore[assignment]
    return f"{n:,.1f} TB"


def _severity_badge_md(severity: str) -> str:
    """Markdown badge text for a severity level."""
    return f"**[{severity.upper()}]**"


def _severity_badge_html(severity: str) -> str:
    """HTML badge for a severity level."""
    colors = {
        "critical": "#D32F2F",
        "high": "#F57C00",
        "medium": "#FBC02D",
        "low": "#388E3C",
    }
    bg = colors.get(severity, "#757575")
    return (
        f'<span style="background:{bg};color:#fff;padding:2px 8px;'
        f'border-radius:4px;font-size:0.85em;font-weight:bold;">'
        f'{severity.upper()}</span>'
    )


def _timestamp_str() -> str:
    """Current UTC timestamp as ISO-8601."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


# ===================================================================
# Markdown Report
# ===================================================================

def generate_markdown_report(
    analysis: Dict[str, Any],
    findings: Optional[List[Dict[str, Any]]] = None,
    pcap_path: Optional[str] = None,
    chart_dir: Optional[str] = None,
) -> str:
    """
    Generate a full analysis report in Markdown.

    Parameters
    ----------
    analysis : dict
        Output of ``analyzer.full_analysis``.
    findings : list[dict] or None
        Anomaly detection findings from ``anomaly_detector.run_all_detectors``.
    pcap_path : str or None
        Original PCAP file path (for metadata).
    chart_dir : str or None
        Directory containing chart PNGs for image embedding.

    Returns
    -------
    str
        Complete Markdown document.
    """
    lines: List[str] = []
    findings = findings or []
    summary = analysis.get("summary", {})

    # --- Header ---
    lines.append("# Network Traffic Analysis Report")
    lines.append("")
    lines.append(f"**Generated:** {_timestamp_str()}")
    if pcap_path:
        lines.append(f"**Source file:** `{pcap_path}`")
    lines.append("")
    lines.append("> **Disclaimer:** This report was generated for authorized network "
                 "analysis purposes only. Do not distribute without appropriate clearance.")
    lines.append("")

    # --- Summary ---
    lines.append("## Capture Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total packets | {summary.get('total_packets', 0):,} |")
    lines.append(f"| Total bytes | {_fmt_bytes(summary.get('total_bytes', 0))} |")
    lines.append(f"| Average packet size | {summary.get('avg_packet_size', 0):.1f} B |")
    lines.append(f"| Capture duration | {summary.get('duration_seconds', 0):.2f} s |")
    lines.append(f"| Avg packets/sec | {summary.get('avg_packets_per_second', 0):.1f} |")
    lines.append(f"| Avg bytes/sec | {_fmt_bytes(int(summary.get('avg_bytes_per_second', 0)))} |")
    lines.append("")

    # --- Protocol Distribution ---
    proto_dist = analysis.get("protocol_distribution", {})
    if proto_dist:
        proto_pct = analysis.get("protocol_distribution_pct", {})
        lines.append("## Protocol Distribution")
        lines.append("")
        lines.append("| Protocol | Packets | Percentage |")
        lines.append("|----------|---------|------------|")
        for proto, count in proto_dist.items():
            pct = proto_pct.get(proto, 0)
            lines.append(f"| {proto} | {count:,} | {pct:.1f}% |")
        lines.append("")

        if chart_dir:
            chart_path = os.path.join(chart_dir, "protocol_distribution.png")
            if os.path.isfile(chart_path):
                lines.append(f"![Protocol Distribution]({chart_path})")
                lines.append("")

    # --- Top Source IPs ---
    top_src = analysis.get("top_source_ips", [])
    if top_src:
        lines.append("## Top Source IPs")
        lines.append("")
        lines.append("| Rank | IP Address | Packets |")
        lines.append("|------|------------|---------|")
        for rank, (ip, count) in enumerate(top_src, 1):
            lines.append(f"| {rank} | {ip} | {count:,} |")
        lines.append("")

    # --- Top Destination IPs ---
    top_dst = analysis.get("top_dest_ips", [])
    if top_dst:
        lines.append("## Top Destination IPs")
        lines.append("")
        lines.append("| Rank | IP Address | Packets |")
        lines.append("|------|------------|---------|")
        for rank, (ip, count) in enumerate(top_dst, 1):
            lines.append(f"| {rank} | {ip} | {count:,} |")
        lines.append("")

    # --- Top Talkers ---
    talkers = analysis.get("top_talkers", [])
    if talkers:
        lines.append("## Top Talkers (Source + Destination Combined)")
        lines.append("")
        lines.append("| Rank | IP Address | Total Packets |")
        lines.append("|------|------------|---------------|")
        for rank, (ip, count) in enumerate(talkers, 1):
            lines.append(f"| {rank} | {ip} | {count:,} |")
        lines.append("")

        if chart_dir:
            chart_path = os.path.join(chart_dir, "top_talkers.png")
            if os.path.isfile(chart_path):
                lines.append(f"![Top Talkers]({chart_path})")
                lines.append("")

    # --- Port Frequency ---
    port_freq = analysis.get("destination_port_frequency", [])
    if port_freq:
        lines.append("## Destination Port Frequency")
        lines.append("")
        lines.append("| Port | Packets | Common Service |")
        lines.append("|------|---------|----------------|")
        for port, count in port_freq:
            service = _well_known_service(port)
            lines.append(f"| {port} | {count:,} | {service} |")
        lines.append("")

    # --- Bandwidth ---
    bw_src = analysis.get("bandwidth_by_source", {})
    if bw_src:
        lines.append("## Bandwidth by Source IP")
        lines.append("")
        lines.append("| IP Address | Total Bytes |")
        lines.append("|------------|-------------|")
        for ip, total in list(bw_src.items())[:10]:
            lines.append(f"| {ip} | {_fmt_bytes(total)} |")
        lines.append("")

    # --- Conversation Pairs ---
    pairs = analysis.get("conversation_pairs", [])
    if pairs:
        lines.append("## Top Conversation Pairs")
        lines.append("")
        lines.append("| IP A | IP B | Packets |")
        lines.append("|------|------|---------|")
        for (ip_a, ip_b), count in pairs:
            lines.append(f"| {ip_a} | {ip_b} | {count:,} |")
        lines.append("")

    # --- Traffic Timeline ---
    if chart_dir:
        chart_path = os.path.join(chart_dir, "traffic_timeline.png")
        if os.path.isfile(chart_path):
            lines.append("## Traffic Timeline")
            lines.append("")
            lines.append(f"![Traffic Timeline]({chart_path})")
            lines.append("")

    # --- Anomaly Findings ---
    if findings:
        lines.append("## Anomaly Detection Findings")
        lines.append("")
        lines.append(f"**Total findings:** {len(findings)}")
        lines.append("")

        for idx, finding in enumerate(findings, 1):
            sev = _severity_badge_md(finding["severity"])
            lines.append(f"### {idx}. {sev} {finding['title']}")
            lines.append("")
            lines.append(f"**Category:** {finding['category']}")
            lines.append("")
            lines.append(finding["description"])
            lines.append("")

            evidence = finding.get("evidence", {})
            if evidence:
                lines.append("<details>")
                lines.append("<summary>Evidence details</summary>")
                lines.append("")
                lines.append("```")
                for key, val in evidence.items():
                    lines.append(f"  {key}: {val}")
                lines.append("```")
                lines.append("")
                lines.append("</details>")
                lines.append("")
    else:
        lines.append("## Anomaly Detection")
        lines.append("")
        lines.append("No anomalies detected with current thresholds.")
        lines.append("")

    # --- Footer ---
    lines.append("---")
    lines.append("")
    lines.append(f"*Report generated at {_timestamp_str()}. "
                 "Analyze only authorized traffic.*")
    lines.append("")

    return "\n".join(lines)


# ===================================================================
# HTML Report
# ===================================================================

def generate_html_report(
    analysis: Dict[str, Any],
    findings: Optional[List[Dict[str, Any]]] = None,
    pcap_path: Optional[str] = None,
    chart_dir: Optional[str] = None,
) -> str:
    """
    Generate a full analysis report in self-contained HTML.

    Parameters
    ----------
    analysis : dict
    findings : list[dict] or None
    pcap_path : str or None
    chart_dir : str or None

    Returns
    -------
    str
        Complete HTML document.
    """
    findings = findings or []
    summary = analysis.get("summary", {})
    esc = html_mod.escape

    parts: List[str] = []

    parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Network Traffic Analysis Report</title>
<style>
  :root {
    --bg: #f5f7fa; --card: #ffffff; --border: #e0e0e0;
    --text: #333333; --muted: #777777; --accent: #2196F3;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: var(--bg); color: var(--text); line-height: 1.6; padding: 2rem; }
  .container { max-width: 1100px; margin: 0 auto; }
  h1 { font-size: 1.8rem; margin-bottom: 0.5rem; color: var(--accent); }
  h2 { font-size: 1.3rem; margin: 2rem 0 0.8rem; padding-bottom: 0.3rem;
       border-bottom: 2px solid var(--accent); }
  h3 { font-size: 1.1rem; margin: 1.2rem 0 0.5rem; }
  .meta { color: var(--muted); font-size: 0.9rem; margin-bottom: 1rem; }
  .disclaimer { background: #fff3e0; border-left: 4px solid #FF9800; padding: 0.8rem 1rem;
                margin-bottom: 1.5rem; font-size: 0.9rem; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 1.5rem;
          background: var(--card); border-radius: 6px; overflow: hidden;
          box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
  th, td { text-align: left; padding: 0.6rem 1rem; border-bottom: 1px solid var(--border); }
  th { background: #f0f4f8; font-weight: 600; font-size: 0.9rem; }
  tr:hover { background: #f9fbfd; }
  .finding { background: var(--card); border-radius: 6px; padding: 1rem 1.2rem;
             margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
  .finding-title { font-weight: 600; margin-bottom: 0.3rem; }
  .evidence { background: #f8f8f8; border-radius: 4px; padding: 0.6rem 1rem;
              margin-top: 0.5rem; font-family: monospace; font-size: 0.85rem;
              white-space: pre-wrap; }
  img { max-width: 100%; height: auto; border-radius: 6px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1); margin: 1rem 0; }
  .footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border);
            color: var(--muted); font-size: 0.85rem; text-align: center; }
</style>
</head>
<body>
<div class="container">
""")

    # Header
    parts.append("<h1>Network Traffic Analysis Report</h1>")
    parts.append(f'<p class="meta">Generated: {_timestamp_str()}')
    if pcap_path:
        parts.append(f" | Source: <code>{esc(pcap_path)}</code>")
    parts.append("</p>")
    parts.append('<p class="disclaimer">This report is for authorized network '
                 "analysis only. Do not distribute without appropriate clearance.</p>")

    # Summary
    parts.append("<h2>Capture Summary</h2>")
    parts.append("<table><tr><th>Metric</th><th>Value</th></tr>")
    parts.append(f"<tr><td>Total packets</td><td>{summary.get('total_packets', 0):,}</td></tr>")
    parts.append(f"<tr><td>Total bytes</td><td>{_fmt_bytes(summary.get('total_bytes', 0))}</td></tr>")
    parts.append(f"<tr><td>Avg packet size</td><td>{summary.get('avg_packet_size', 0):.1f} B</td></tr>")
    parts.append(f"<tr><td>Duration</td><td>{summary.get('duration_seconds', 0):.2f} s</td></tr>")
    parts.append(f"<tr><td>Avg packets/sec</td><td>{summary.get('avg_packets_per_second', 0):.1f}</td></tr>")
    parts.append(f"<tr><td>Avg bytes/sec</td><td>{_fmt_bytes(int(summary.get('avg_bytes_per_second', 0)))}</td></tr>")
    parts.append("</table>")

    # Protocol Distribution
    proto_dist = analysis.get("protocol_distribution", {})
    proto_pct = analysis.get("protocol_distribution_pct", {})
    if proto_dist:
        parts.append("<h2>Protocol Distribution</h2>")
        parts.append("<table><tr><th>Protocol</th><th>Packets</th><th>%</th></tr>")
        for proto, count in proto_dist.items():
            pct = proto_pct.get(proto, 0)
            parts.append(f"<tr><td>{esc(proto)}</td><td>{count:,}</td><td>{pct:.1f}%</td></tr>")
        parts.append("</table>")
        _maybe_embed_chart(parts, chart_dir, "protocol_distribution.png", "Protocol Distribution")

    # Top Source IPs
    top_src = analysis.get("top_source_ips", [])
    if top_src:
        parts.append("<h2>Top Source IPs</h2>")
        parts.append("<table><tr><th>#</th><th>IP Address</th><th>Packets</th></tr>")
        for rank, (ip, count) in enumerate(top_src, 1):
            parts.append(f"<tr><td>{rank}</td><td>{esc(ip)}</td><td>{count:,}</td></tr>")
        parts.append("</table>")

    # Top Destination IPs
    top_dst = analysis.get("top_dest_ips", [])
    if top_dst:
        parts.append("<h2>Top Destination IPs</h2>")
        parts.append("<table><tr><th>#</th><th>IP Address</th><th>Packets</th></tr>")
        for rank, (ip, count) in enumerate(top_dst, 1):
            parts.append(f"<tr><td>{rank}</td><td>{esc(ip)}</td><td>{count:,}</td></tr>")
        parts.append("</table>")

    # Top Talkers
    talkers = analysis.get("top_talkers", [])
    if talkers:
        parts.append("<h2>Top Talkers</h2>")
        parts.append("<table><tr><th>#</th><th>IP Address</th><th>Packets</th></tr>")
        for rank, (ip, count) in enumerate(talkers, 1):
            parts.append(f"<tr><td>{rank}</td><td>{esc(ip)}</td><td>{count:,}</td></tr>")
        parts.append("</table>")
        _maybe_embed_chart(parts, chart_dir, "top_talkers.png", "Top Talkers")

    # Port Frequency
    port_freq = analysis.get("destination_port_frequency", [])
    if port_freq:
        parts.append("<h2>Destination Port Frequency</h2>")
        parts.append("<table><tr><th>Port</th><th>Packets</th><th>Common Service</th></tr>")
        for port, count in port_freq:
            svc = _well_known_service(port)
            parts.append(f"<tr><td>{port}</td><td>{count:,}</td><td>{esc(svc)}</td></tr>")
        parts.append("</table>")
        _maybe_embed_chart(parts, chart_dir, "port_frequency.png", "Port Frequency")

    # Bandwidth
    bw_src = analysis.get("bandwidth_by_source", {})
    if bw_src:
        parts.append("<h2>Bandwidth by Source IP</h2>")
        parts.append("<table><tr><th>IP Address</th><th>Total Bytes</th></tr>")
        for ip, total in list(bw_src.items())[:10]:
            parts.append(f"<tr><td>{esc(ip)}</td><td>{_fmt_bytes(total)}</td></tr>")
        parts.append("</table>")
        _maybe_embed_chart(parts, chart_dir, "bandwidth_by_source.png", "Bandwidth by Source IP")

    # Conversation Pairs
    pairs = analysis.get("conversation_pairs", [])
    if pairs:
        parts.append("<h2>Top Conversation Pairs</h2>")
        parts.append("<table><tr><th>IP A</th><th>IP B</th><th>Packets</th></tr>")
        for (ip_a, ip_b), count in pairs:
            parts.append(f"<tr><td>{esc(ip_a)}</td><td>{esc(ip_b)}</td><td>{count:,}</td></tr>")
        parts.append("</table>")

    # Timeline chart
    _maybe_embed_chart(parts, chart_dir, "traffic_timeline.png", "Traffic Timeline")

    # Anomaly Findings
    parts.append("<h2>Anomaly Detection Findings</h2>")
    if findings:
        parts.append(f"<p><strong>Total findings:</strong> {len(findings)}</p>")
        for idx, finding in enumerate(findings, 1):
            badge = _severity_badge_html(finding["severity"])
            parts.append(f'<div class="finding">')
            parts.append(f'<div class="finding-title">{idx}. {badge} {esc(finding["title"])}</div>')
            parts.append(f"<p><strong>Category:</strong> {esc(finding['category'])}</p>")
            parts.append(f"<p>{esc(finding['description'])}</p>")
            evidence = finding.get("evidence", {})
            if evidence:
                parts.append('<div class="evidence">')
                for key, val in evidence.items():
                    parts.append(f"{esc(str(key))}: {esc(str(val))}")
                parts.append("</div>")
            parts.append("</div>")
    else:
        parts.append("<p>No anomalies detected with current thresholds.</p>")

    # Footer
    parts.append(f'<div class="footer">Report generated at {_timestamp_str()}. '
                 "Analyze only authorized traffic.</div>")
    parts.append("</div></body></html>")

    return "\n".join(parts)


# ===================================================================
# Report file writer
# ===================================================================

def write_report(
    content: str,
    output_path: str,
) -> str:
    """
    Write report content to a file.

    Parameters
    ----------
    content : str
        Markdown or HTML string.
    output_path : str

    Returns
    -------
    str
        Absolute path of the written report.
    """
    abs_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return abs_path


# ===================================================================
# Helpers
# ===================================================================

def _maybe_embed_chart(
    parts: List[str],
    chart_dir: Optional[str],
    filename: str,
    alt: str,
) -> None:
    """Append an <img> tag if the chart file exists."""
    if not chart_dir:
        return
    path = os.path.join(chart_dir, filename)
    if os.path.isfile(path):
        parts.append(f'<h2>{alt}</h2>')
        parts.append(f'<img src="{html_mod.escape(path)}" alt="{html_mod.escape(alt)}">')


_WELL_KNOWN_PORTS: Dict[int, str] = {
    20: "FTP Data", 21: "FTP Control", 22: "SSH", 23: "Telnet",
    25: "SMTP", 53: "DNS", 67: "DHCP Server", 68: "DHCP Client",
    80: "HTTP", 110: "POP3", 119: "NNTP", 123: "NTP",
    135: "MS RPC", 137: "NetBIOS Name", 138: "NetBIOS Datagram",
    139: "NetBIOS Session", 143: "IMAP", 161: "SNMP", 162: "SNMP Trap",
    389: "LDAP", 443: "HTTPS", 445: "SMB", 465: "SMTPS",
    514: "Syslog", 587: "SMTP Submission", 636: "LDAPS",
    993: "IMAPS", 995: "POP3S", 1433: "MSSQL", 1521: "Oracle DB",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC",
    6379: "Redis", 8080: "HTTP Proxy", 8443: "HTTPS Alt",
    8888: "HTTP Alt", 9200: "Elasticsearch", 27017: "MongoDB",
}


def _well_known_service(port: int) -> str:
    """Return the common service name for a well-known port."""
    return _WELL_KNOWN_PORTS.get(port, "Unknown")
