"""
Visualization Module
====================

Generates publication-ready charts from traffic analysis results using
matplotlib. Each function produces a single figure, displays it optionally,
and saves it to disk as a PNG.

Charts
------
- Protocol distribution pie chart
- Traffic timeline (packets and bytes over time)
- Top talkers horizontal bar chart
- Destination port frequency bar chart
- Bandwidth by IP bar chart

All public functions follow the same pattern:

    fig = create_<chart>(data, ...)
    save_figure(fig, path)

WARNING: Only visualize captures you are authorized to analyze.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend so it works headless
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure


# ===================================================================
# Style defaults
# ===================================================================

_COLOR_PALETTE = [
    "#2196F3", "#4CAF50", "#FF9800", "#F44336", "#9C27B0",
    "#00BCD4", "#795548", "#607D8B", "#E91E63", "#CDDC39",
    "#3F51B5", "#009688", "#FF5722", "#8BC34A", "#FFC107",
]

_FIGURE_DPI = 150
_FIGURE_SIZE = (10, 6)


def _apply_style() -> None:
    """Apply a consistent visual style to all charts."""
    plt.rcParams.update({
        "figure.facecolor": "#FAFAFA",
        "axes.facecolor": "#FFFFFF",
        "axes.edgecolor": "#CCCCCC",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "font.family": "sans-serif",
        "font.size": 10,
    })


def save_figure(fig: Figure, filepath: str, dpi: int = _FIGURE_DPI) -> str:
    """
    Save a matplotlib Figure to disk.

    Parameters
    ----------
    fig : Figure
    filepath : str
        Destination path (directories are created automatically).
    dpi : int

    Returns
    -------
    str
        Absolute path of the saved file.
    """
    abs_path = os.path.abspath(filepath)
    os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
    fig.savefig(abs_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return abs_path


# ===================================================================
# 1. Protocol Distribution Pie Chart
# ===================================================================

def create_protocol_pie_chart(
    protocol_dist: Dict[str, int],
    title: str = "Protocol Distribution",
    max_slices: int = 8,
) -> Figure:
    """
    Create a pie chart showing the share of each protocol.

    Protocols beyond *max_slices* are grouped into an "Other" slice to
    keep the chart readable.

    Parameters
    ----------
    protocol_dist : dict[str, int]
        Protocol name -> packet count (from ``analyzer.protocol_distribution``).
    title : str
    max_slices : int

    Returns
    -------
    Figure
    """
    _apply_style()

    # Sort and optionally collapse small slices
    items = sorted(protocol_dist.items(), key=lambda x: x[1], reverse=True)
    if len(items) > max_slices:
        top = items[:max_slices - 1]
        other_total = sum(v for _, v in items[max_slices - 1:])
        top.append(("Other", other_total))
        items = top

    labels = [name for name, _ in items]
    sizes = [count for _, count in items]
    colors = _COLOR_PALETTE[: len(labels)]

    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct=lambda pct: f"{pct:.1f}%" if pct > 2 else "",
        colors=colors,
        startangle=140,
        pctdistance=0.8,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )

    for text in autotexts:
        text.set_fontsize(9)
        text.set_color("#333333")

    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

    # Legend
    total = sum(sizes)
    legend_labels = [
        f"{label}: {count:,} ({count/total*100:.1f}%)"
        for label, count in zip(labels, sizes)
    ]
    ax.legend(
        wedges, legend_labels,
        title="Protocols",
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
        fontsize=9,
    )

    return fig


# ===================================================================
# 2. Traffic Timeline
# ===================================================================

def create_traffic_timeline(
    packets_series: List[Tuple[float, int]],
    bytes_series: Optional[List[Tuple[float, int]]] = None,
    title: str = "Traffic Over Time",
) -> Figure:
    """
    Line chart of packets (and optionally bytes) per time bucket.

    Parameters
    ----------
    packets_series : list[tuple[float, int]]
        (bucket_start_timestamp, packet_count) from ``analyzer.packets_per_interval``.
    bytes_series : list[tuple[float, int]] or None
        (bucket_start_timestamp, byte_count) from ``analyzer.bytes_per_interval``.
    title : str

    Returns
    -------
    Figure
    """
    _apply_style()

    has_bytes = bytes_series is not None and len(bytes_series) > 0
    nrows = 2 if has_bytes else 1
    fig, axes = plt.subplots(nrows, 1, figsize=(12, 5 * nrows), sharex=True)

    if nrows == 1:
        axes = [axes]

    # Convert timestamps to datetime objects for readable x-axis
    pkt_times = [datetime.fromtimestamp(ts, tz=timezone.utc) for ts, _ in packets_series]
    pkt_counts = [c for _, c in packets_series]

    ax_pkt = axes[0]
    ax_pkt.fill_between(pkt_times, pkt_counts, alpha=0.3, color=_COLOR_PALETTE[0])
    ax_pkt.plot(pkt_times, pkt_counts, color=_COLOR_PALETTE[0], linewidth=1.2)
    ax_pkt.set_ylabel("Packets", fontsize=11)
    ax_pkt.set_title(title, fontsize=14, fontweight="bold")

    # Mark the mean rate as a horizontal line
    if pkt_counts:
        mean_pkts = sum(pkt_counts) / len(pkt_counts)
        ax_pkt.axhline(
            mean_pkts, color=_COLOR_PALETTE[3], linestyle="--",
            linewidth=0.8, label=f"Mean: {mean_pkts:.0f}",
        )
        ax_pkt.legend(fontsize=9)

    if has_bytes:
        byte_times = [datetime.fromtimestamp(ts, tz=timezone.utc) for ts, _ in bytes_series]
        byte_counts = [c for _, c in bytes_series]

        ax_bytes = axes[1]
        ax_bytes.fill_between(byte_times, byte_counts, alpha=0.3, color=_COLOR_PALETTE[1])
        ax_bytes.plot(byte_times, byte_counts, color=_COLOR_PALETTE[1], linewidth=1.2)
        ax_bytes.set_ylabel("Bytes", fontsize=11)
        ax_bytes.set_xlabel("Time (UTC)", fontsize=11)

        if byte_counts:
            mean_bytes = sum(byte_counts) / len(byte_counts)
            ax_bytes.axhline(
                mean_bytes, color=_COLOR_PALETTE[3], linestyle="--",
                linewidth=0.8, label=f"Mean: {mean_bytes:,.0f}",
            )
            ax_bytes.legend(fontsize=9)

    # Format x-axis
    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        fig.autofmt_xdate(rotation=30)

    fig.tight_layout()
    return fig


# ===================================================================
# 3. Top Talkers Bar Chart
# ===================================================================

def create_top_talkers_chart(
    talkers: List[Tuple[str, int]],
    title: str = "Top Talkers by Packet Count",
) -> Figure:
    """
    Horizontal bar chart of the top talking IP addresses.

    Parameters
    ----------
    talkers : list[tuple[str, int]]
        (ip_address, count) from ``analyzer.top_talkers`` or similar.
    title : str

    Returns
    -------
    Figure
    """
    _apply_style()

    if not talkers:
        fig, ax = plt.subplots(figsize=_FIGURE_SIZE)
        ax.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=14)
        return fig

    # Reverse so the largest bar is at the top
    talkers_sorted = list(reversed(talkers))
    ips = [ip for ip, _ in talkers_sorted]
    counts = [c for _, c in talkers_sorted]

    fig, ax = plt.subplots(figsize=_FIGURE_SIZE)
    bars = ax.barh(
        ips, counts,
        color=_COLOR_PALETTE[0],
        edgecolor="white",
        linewidth=0.5,
        height=0.6,
    )

    # Annotate bars with counts
    max_count = max(counts) if counts else 1
    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_width() + max_count * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{count:,}",
            va="center",
            fontsize=9,
            color="#555555",
        )

    ax.set_xlabel("Packet Count", fontsize=11)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.margins(x=0.15)
    fig.tight_layout()
    return fig


# ===================================================================
# 4. Destination Port Frequency Chart
# ===================================================================

def create_port_frequency_chart(
    port_freq: List[Tuple[int, int]],
    title: str = "Top Destination Ports",
    max_bars: int = 15,
) -> Figure:
    """
    Vertical bar chart of the most-targeted destination ports.

    Parameters
    ----------
    port_freq : list[tuple[int, int]]
        (port_number, count) from ``analyzer.destination_port_frequency``.
    title : str
    max_bars : int

    Returns
    -------
    Figure
    """
    _apply_style()

    data = port_freq[:max_bars]
    if not data:
        fig, ax = plt.subplots(figsize=_FIGURE_SIZE)
        ax.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=14)
        return fig

    ports = [str(p) for p, _ in data]
    counts = [c for _, c in data]

    fig, ax = plt.subplots(figsize=_FIGURE_SIZE)
    bars = ax.bar(
        ports, counts,
        color=_COLOR_PALETTE[2],
        edgecolor="white",
        linewidth=0.5,
    )

    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(counts) * 0.01,
            str(count),
            ha="center",
            va="bottom",
            fontsize=8,
            color="#555555",
        )

    ax.set_xlabel("Destination Port", fontsize=11)
    ax.set_ylabel("Packet Count", fontsize=11)
    ax.set_title(title, fontsize=14, fontweight="bold")
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    return fig


# ===================================================================
# 5. Bandwidth per IP Chart
# ===================================================================

def create_bandwidth_chart(
    bw_data: Dict[str, int],
    title: str = "Bandwidth by Source IP",
    top_n: int = 10,
) -> Figure:
    """
    Horizontal bar chart of bytes transferred per IP address.

    Parameters
    ----------
    bw_data : dict[str, int]
        IP -> total_bytes from ``analyzer.bandwidth_per_ip``.
    title : str
    top_n : int

    Returns
    -------
    Figure
    """
    _apply_style()

    items = sorted(bw_data.items(), key=lambda x: x[1], reverse=True)[:top_n]
    if not items:
        fig, ax = plt.subplots(figsize=_FIGURE_SIZE)
        ax.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=14)
        return fig

    items_reversed = list(reversed(items))
    ips = [ip for ip, _ in items_reversed]
    byte_vals = [b for _, b in items_reversed]

    # Human-readable byte labels
    def _fmt_bytes(n: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if abs(n) < 1024:
                return f"{n:,.1f} {unit}"
            n /= 1024  # type: ignore[assignment]
        return f"{n:,.1f} TB"

    fig, ax = plt.subplots(figsize=_FIGURE_SIZE)
    bars = ax.barh(
        ips, byte_vals,
        color=_COLOR_PALETTE[4],
        edgecolor="white",
        linewidth=0.5,
        height=0.6,
    )

    max_val = max(byte_vals) if byte_vals else 1
    for bar, val in zip(bars, byte_vals):
        ax.text(
            bar.get_width() + max_val * 0.01,
            bar.get_y() + bar.get_height() / 2,
            _fmt_bytes(val),
            va="center",
            fontsize=9,
            color="#555555",
        )

    ax.set_xlabel("Total Bytes", fontsize=11)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.margins(x=0.2)
    fig.tight_layout()
    return fig


# ===================================================================
# Convenience: generate all charts at once
# ===================================================================

def generate_all_charts(
    analysis: Dict[str, Any],
    output_dir: str = "charts",
) -> Dict[str, str]:
    """
    Generate all available charts from a full analysis result dict
    (as returned by ``analyzer.full_analysis``) and save them to
    *output_dir*.

    Parameters
    ----------
    analysis : dict
        Output of ``analyzer.full_analysis``.
    output_dir : str
        Directory to save chart PNGs.

    Returns
    -------
    dict[str, str]
        Chart name -> absolute file path of the saved PNG.
    """
    saved: Dict[str, str] = {}

    # Protocol pie chart
    proto = analysis.get("protocol_distribution", {})
    if proto:
        fig = create_protocol_pie_chart(proto)
        path = save_figure(fig, os.path.join(output_dir, "protocol_distribution.png"))
        saved["protocol_distribution"] = path

    # Traffic timeline
    pkt_series = analysis.get("packets_per_interval", [])
    byte_series = analysis.get("bytes_per_interval", [])
    if pkt_series:
        fig = create_traffic_timeline(pkt_series, byte_series)
        path = save_figure(fig, os.path.join(output_dir, "traffic_timeline.png"))
        saved["traffic_timeline"] = path

    # Top talkers
    talkers = analysis.get("top_talkers", [])
    if talkers:
        fig = create_top_talkers_chart(talkers)
        path = save_figure(fig, os.path.join(output_dir, "top_talkers.png"))
        saved["top_talkers"] = path

    # Port frequency
    port_freq = analysis.get("destination_port_frequency", [])
    if port_freq:
        fig = create_port_frequency_chart(port_freq)
        path = save_figure(fig, os.path.join(output_dir, "port_frequency.png"))
        saved["port_frequency"] = path

    # Bandwidth by source
    bw_src = analysis.get("bandwidth_by_source", {})
    if bw_src:
        fig = create_bandwidth_chart(bw_src, title="Bandwidth by Source IP")
        path = save_figure(fig, os.path.join(output_dir, "bandwidth_by_source.png"))
        saved["bandwidth_by_source"] = path

    # Bandwidth by destination
    bw_dst = analysis.get("bandwidth_by_dest", {})
    if bw_dst:
        fig = create_bandwidth_chart(bw_dst, title="Bandwidth by Destination IP")
        path = save_figure(fig, os.path.join(output_dir, "bandwidth_by_dest.png"))
        saved["bandwidth_by_dest"] = path

    return saved
