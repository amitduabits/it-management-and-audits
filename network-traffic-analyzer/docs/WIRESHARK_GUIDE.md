# Capturing Traffic with Wireshark and Exporting PCAP

This guide covers how to capture live network traffic using Wireshark and export it in a format compatible with the Network Traffic Analyzer.

> **Legal Warning:** Never capture network traffic on a network you do not own or do not have explicit written authorization to monitor. Unauthorized packet capture is illegal in most jurisdictions.

---

## Prerequisites

- **Wireshark** installed on your system. Download from [wireshark.org](https://www.wireshark.org/download.html).
- **Administrative / root privileges** -- packet capture requires elevated permissions on most operating systems.
- On Linux, you may need to add your user to the `wireshark` group:
  ```bash
  sudo usermod -aG wireshark $USER
  ```
  Then log out and back in.

---

## Step 1: Select the Capture Interface

1. Launch Wireshark.
2. On the welcome screen you will see a list of available network interfaces with small traffic-activity sparklines.
3. Choose the interface you want to monitor:
   - **Ethernet** -- wired LAN connections (e.g., `eth0`, `enp3s0`, `Ethernet`).
   - **Wi-Fi** -- wireless adapter (e.g., `wlan0`, `Wi-Fi`).
   - **Loopback** -- traffic between processes on the same machine (`lo`, `Loopback`).
   - **Any** (Linux only) -- captures on all interfaces simultaneously.

### Tips for Interface Selection

- If you are unsure which interface carries the traffic you want, look at the sparklines -- the active interface will show movement.
- On Windows, interface names may be long GUIDs. Wireshark shows the friendly name next to them.

---

## Step 2: Apply a Capture Filter (Optional but Recommended)

Capture filters reduce the volume of data written to disk by filtering at the capture engine level (BPF syntax). Set them **before** starting the capture.

Click the text field next to the interface name (labeled "Enter a capture filter...") and type a BPF expression.

### Common Capture Filter Examples

| Filter | Description |
|--------|-------------|
| `host 192.168.1.10` | Only traffic to/from a specific IP |
| `net 192.168.1.0/24` | Only traffic on a specific subnet |
| `port 80` | Only HTTP traffic |
| `port 53` | Only DNS traffic |
| `tcp` | Only TCP packets |
| `udp` | Only UDP packets |
| `not port 22` | Exclude SSH traffic |
| `host 10.0.0.1 and port 443` | HTTPS traffic to/from a specific host |
| `ether host aa:bb:cc:dd:ee:ff` | Traffic to/from a specific MAC address |

### BPF Syntax Quick Reference

- `and` / `&&` -- logical AND
- `or` / `||` -- logical OR
- `not` / `!` -- logical NOT
- Parentheses for grouping: `(host 10.0.0.1) and (port 80 or port 443)`

---

## Step 3: Start the Capture

1. Double-click the interface name, **or** select it and click the blue shark-fin icon in the toolbar.
2. Wireshark begins capturing packets immediately. You will see packets populating the main packet list in real time.

### Capture Duration

- **Short captures** (30-60 seconds) are usually sufficient for quick analysis.
- **Long captures** can generate very large files. For extended monitoring, consider:
  - Using ring buffers (Capture > Options > Output tab > "Create a new file automatically after...").
  - Setting a file size limit (e.g., 100 MB per file).

---

## Step 4: Stop the Capture

Click the red square **Stop** button in the toolbar, or press `Ctrl+E`.

---

## Step 5: Apply a Display Filter (Optional)

Display filters let you narrow down what you see **after** capture without discarding data. Type in the filter bar at the top of the packet list.

### Common Display Filter Examples

| Filter | Description |
|--------|-------------|
| `ip.addr == 192.168.1.10` | Packets involving a specific IP |
| `tcp.port == 443` | HTTPS traffic |
| `dns` | All DNS packets |
| `http.request` | HTTP requests only |
| `tcp.flags.syn == 1 && tcp.flags.ack == 0` | SYN-only (potential scan) |
| `icmp` | ICMP traffic |
| `tcp.analysis.retransmission` | TCP retransmissions |
| `frame.len > 1400` | Large packets |
| `ip.src == 10.0.0.0/8` | Source in 10.0.0.0/8 range |

Display filter syntax differs from capture filter syntax. Display filters use Wireshark's own expression language with field names like `ip.addr`, `tcp.port`, etc.

---

## Step 6: Export as PCAP

The Network Traffic Analyzer requires **pcap** or **pcapng** format.

### Export the Full Capture

1. Go to **File > Save As...** (or `Ctrl+Shift+S`).
2. Choose a location and filename (e.g., `capture_2025.pcap`).
3. Under "Save as type," select one of:
   - **Wireshark/tcpdump/... - pcap** (`.pcap`) -- recommended for maximum compatibility.
   - **Wireshark/... - pcapng** (`.pcapng`) -- default Wireshark format, richer metadata.
4. Click **Save**.

### Export Only Displayed (Filtered) Packets

If you applied a display filter and want to export only the matching packets:

1. Go to **File > Export Specified Packets...**
2. Under "Packet Range," select **Displayed**.
3. Choose **pcap** format.
4. Click **Save**.

### Export Selected Packets

1. Select packets in the list (use `Ctrl+Click` or `Shift+Click`).
2. **File > Export Specified Packets...**
3. Under "Packet Range," select **Selected packets only**.
4. Save as pcap.

---

## Step 7: Feed the PCAP to the Analyzer

```bash
# Basic analysis
python -m src.cli analyze capture_2025.pcap

# Full report with charts
python -m src.cli report capture_2025.pcap --format html --output report.html --include-charts

# Anomaly detection with custom thresholds
python -m src.cli detect capture_2025.pcap --port-threshold 20 --spike-factor 2.5
```

---

## Capturing with tshark (Command Line)

For headless or scripted captures, use `tshark` (Wireshark's CLI tool):

```bash
# Capture 1000 packets on eth0, save as PCAP
tshark -i eth0 -c 1000 -w capture.pcap

# Capture for 60 seconds
tshark -i eth0 -a duration:60 -w capture.pcap

# Capture only DNS traffic
tshark -i eth0 -f "port 53" -w dns_capture.pcap

# Capture with a ring buffer (5 files, 50MB each)
tshark -i eth0 -b filesize:50000 -b files:5 -w ring_capture.pcap
```

---

## Capturing with tcpdump (Linux/macOS)

```bash
# Capture 500 packets on eth0
sudo tcpdump -i eth0 -c 500 -w capture.pcap

# Capture HTTP and HTTPS traffic for 30 seconds
sudo tcpdump -i eth0 -G 30 -W 1 'port 80 or port 443' -w web_traffic.pcap

# Capture from a specific host
sudo tcpdump -i eth0 host 192.168.1.10 -w host_traffic.pcap
```

---

## Troubleshooting

### "No interfaces found"

- Run Wireshark as administrator / root.
- On Windows, ensure the Npcap driver is installed (bundled with the Wireshark installer).
- On Linux, check group membership: `groups $USER` should include `wireshark`.

### Capture file is very large

- Use capture filters to limit what is recorded.
- Use ring buffers for long-running captures.
- Compress after capture: `gzip capture.pcap` (the analyzer can read `.pcap` but not `.pcap.gz` directly).

### "Permission denied" on Linux

```bash
sudo setcap 'cap_net_raw,cap_net_admin=eip' /usr/bin/dumpcap
```

### Wireshark shows only encrypted data

This is expected for HTTPS, SSH, etc. The analyzer still extracts useful metadata (IPs, ports, sizes, timing) even from encrypted traffic. Payload inspection requires the session keys, which is outside the scope of this tool.

---

## Security Best Practices for Packet Captures

1. **Minimize capture scope.** Apply capture filters to avoid recording traffic you do not need.
2. **Store captures securely.** PCAP files may contain sensitive data (passwords in cleartext protocols, internal IP addresses, hostnames).
3. **Delete captures promptly** once analysis is complete.
4. **Never share captures** without sanitizing them first. Tools like `tcprewrite` can anonymize IP addresses.
5. **Document authorization.** Keep a written record of who authorized the capture, on what network, and for what purpose.
