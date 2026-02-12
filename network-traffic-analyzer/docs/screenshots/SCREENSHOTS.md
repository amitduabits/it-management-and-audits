# Screenshots

This directory is reserved for screenshots of the Network Traffic Analyzer's output. Screenshots are generated when you run the visualize or report commands and can be placed here for documentation purposes.

---

## Expected Screenshots

After running a full analysis pipeline, the following chart images are generated. Place them in this directory if you wish to include them in documentation.

### 1. Protocol Distribution (protocol_distribution.png)

**Description:** A pie chart showing the relative proportion of each network protocol observed in the capture. Each slice represents a protocol (TCP, UDP, DNS, ICMP, etc.) with the percentage labeled. Protocols with less than 2% share are grouped into an "Other" slice to keep the chart readable.

**How to generate:**
```bash
python -m src.cli visualize samples/demo.pcap --output-dir docs/screenshots/
```

**What to look for:**
- The dominant protocol (typically TCP in most networks)
- Unexpected protocols that may indicate tunneling or misconfiguration
- DNS proportion -- if unusually high, may suggest DNS tunneling

---

### 2. Traffic Timeline (traffic_timeline.png)

**Description:** A dual-panel line chart showing packets per time interval (top panel) and bytes per time interval (bottom panel) across the capture duration. A dashed horizontal line indicates the mean rate. The x-axis shows UTC timestamps; the y-axis shows counts/bytes. Shaded area under the line provides visual emphasis.

**How to generate:**
```bash
python -m src.cli visualize samples/demo.pcap --output-dir docs/screenshots/ --interval 30
```

**What to look for:**
- Spikes that significantly exceed the mean line (potential attacks or bursts)
- Periodic patterns (beaconing, scheduled tasks)
- Sudden drops to zero (possible network outage or filter cutoff)

---

### 3. Top Talkers (top_talkers.png)

**Description:** A horizontal bar chart ranking IP addresses by their combined packet count (packets sent + packets received). Bars are labeled with exact counts. The most active IP appears at the top.

**How to generate:**
```bash
python -m src.cli visualize samples/demo.pcap --output-dir docs/screenshots/ --top-n 15
```

**What to look for:**
- Internal IPs that dominate traffic (verify they are expected servers)
- External IPs with high activity (verify they are known services)
- Unknown IPs that warrant further investigation

---

### 4. Port Frequency (port_frequency.png)

**Description:** A vertical bar chart showing the most frequently targeted destination ports. Each bar is labeled with the port number and exact packet count. Helps identify which services are most active.

**How to generate:**
```bash
python -m src.cli visualize samples/demo.pcap --output-dir docs/screenshots/
```

**What to look for:**
- Expected service ports (80, 443, 53, 22) should be present
- Unusual ports (4444, 1337, 8888) may indicate backdoors
- Ports associated with lateral movement (445, 3389, 135)

---

### 5. Bandwidth by Source IP (bandwidth_by_source.png)

**Description:** A horizontal bar chart ranking source IP addresses by total bytes transferred. Bars are labeled with human-readable byte values (KB, MB, GB). Useful for identifying which hosts generate the most data.

**How to generate:**
```bash
python -m src.cli visualize samples/demo.pcap --output-dir docs/screenshots/
```

**What to look for:**
- Hosts sending disproportionately large amounts of data (potential exfiltration)
- Compare against the top talkers chart to distinguish high-volume from high-packet-count hosts

---

### 6. Bandwidth by Destination IP (bandwidth_by_dest.png)

**Description:** Same format as the source bandwidth chart but ranked by destination IP. Shows which endpoints are receiving the most data.

**What to look for:**
- External IPs receiving large data volumes from internal hosts
- Internal servers receiving expected inbound traffic (downloads, updates)

---

## HTML Report Screenshot

When generating an HTML report with `--include-charts`, all of the above charts are embedded directly in the report. The report also includes:

- Styled summary tables
- Color-coded severity badges for anomaly findings
- Expandable evidence sections
- A clean, responsive layout suitable for sharing

**How to generate:**
```bash
python -m src.cli report samples/demo.pcap --format html --output docs/screenshots/report.html --include-charts --chart-dir docs/screenshots/
```

---

## Terminal Output Screenshot

When running the `analyze` command with Rich installed, the terminal displays formatted tables with colored headers and aligned columns. This provides a quick-glance summary without needing to open a report file.

**How to capture a terminal screenshot:**

On Linux/macOS:
```bash
# Using script command to capture output
script -q output.txt -c "python -m src.cli analyze samples/demo.pcap"
```

On Windows:
```powershell
# Run the command and observe the formatted Rich output
python -m src.cli analyze samples/demo.pcap
# Use Snipping Tool or Win+Shift+S to capture the terminal window
```

---

## Adding Your Own Screenshots

If you generate screenshots from your own analysis, place them in this directory with descriptive filenames:

```
docs/screenshots/
  protocol_distribution.png
  traffic_timeline.png
  top_talkers.png
  port_frequency.png
  bandwidth_by_source.png
  bandwidth_by_dest.png
  report.html
  terminal_output.png
  SCREENSHOTS.md (this file)
```

Keep file sizes reasonable (< 500 KB per image) by using the default DPI of 150 or compressing PNGs after generation.
