# Dashboard Screenshots

## Overview

This directory contains screenshots of the SecureAudit Pro dashboard and reports for documentation purposes.

## Expected Screenshots

When the dashboard is running, capture the following screenshots:

### Dashboard Pages
1. **Risk Overview** - Main dashboard with risk gauge, severity chart, and category breakdown
2. **Findings Explorer** - Findings table with severity badges and filtering
3. **Compliance Status** - Framework comparison with circular gauges and drill-down
4. **Remediation Tracker** - Phase timeline with effort distribution chart

### Reports
5. **Executive Summary** - One-page executive report with key metrics
6. **Technical Report** - Detailed findings with CVSS scoring
7. **Remediation Roadmap** - Three-phase action plan

### CLI Output
8. **Network Scan** - Terminal output of a network scan
9. **Full Assessment** - Complete pipeline output with risk matrix

## Capturing Screenshots

```bash
# 1. Start the dashboard
python -m src.cli start-dashboard

# 2. Open http://localhost:5000 in your browser

# 3. Navigate to each page and capture screenshots

# 4. Save screenshots to this directory with descriptive names:
#    - dashboard_home.png
#    - dashboard_findings.png
#    - dashboard_compliance.png
#    - dashboard_remediation.png
#    - report_executive.png
#    - report_technical.png
#    - report_roadmap.png
#    - cli_network_scan.png
#    - cli_full_assessment.png
```

## Notes

- Use a browser width of 1440px for consistent screenshots
- Dark mode screenshots may also be captured for portfolio use
- Ensure no sensitive data is visible in screenshots
