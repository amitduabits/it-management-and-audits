# Dashboard User Guide

## Overview

The SecureAudit Pro dashboard provides an interactive web interface for exploring security assessment results. Built with Flask and Chart.js, it offers real-time visualization of risk posture, findings, compliance status, and remediation progress.

## Starting the Dashboard

```bash
# Default (localhost:5000)
python -m src.cli start-dashboard

# Custom host and port
python -m src.cli start-dashboard --host 0.0.0.0 --port 8080

# With assessment data
python -m src.cli start-dashboard --input ./reports/assessment_data.json
```

Navigate to `http://localhost:5000` in your web browser.

## Pages

### Risk Overview (Home)
The main dashboard page displaying:
- **Risk Score Gauge**: Overall 0-10 risk score with severity badge
- **Key Metrics**: Total findings, critical count, high count
- **Severity Distribution Chart**: Doughnut chart of finding severities
- **Risk by Category Chart**: Horizontal bar chart of category scores
- **Category Cards**: Detailed breakdown of each risk category
- **Compliance Summary**: Circular gauges for each framework
- **Top Recommendations**: Priority-ordered action items

### Findings Explorer
An interactive table of all security findings with:
- **Severity Filtering**: Filter by critical, high, medium, low, info
- **Category Filtering**: Filter by Network Security, Web Security, etc.
- **Full-Text Search**: Search finding titles and descriptions
- **Expandable Details**: Click "View" for evidence, remediation, and compliance references
- **CVSS Score Bars**: Visual representation of finding severity

### Compliance Status
Framework-by-framework compliance assessment showing:
- **Overview Cards**: Score percentage, pass/fail/partial counts
- **Framework Comparison Chart**: Side-by-side bar chart
- **ISO 27001 Categories**: Organizational, People, Physical, Technological
- **PCI-DSS Sections**: All 6 major PCI-DSS sections
- **NIST CSF Functions**: Identify, Protect, Detect, Respond, Recover with tier indicator

### Remediation Tracker
Phase-organized action plan displaying:
- **Summary Metrics**: Total items per phase
- **Effort Distribution Chart**: Items vs. hours by phase
- **Phase 1 - Quick Wins**: Low-effort, high-impact items (0-30 days)
- **Phase 2 - Short-Term**: Moderate effort items (30-90 days)
- **Phase 3 - Long-Term**: Strategic improvements (90-365 days)
- **Item Details**: Severity, effort, hours, responsible team

## API Endpoints

The dashboard also exposes JSON API endpoints:
- `GET /api/risk-summary` - Risk assessment data
- `GET /api/findings` - All findings
- `GET /api/compliance` - Compliance data

## Demo Mode

When started without assessment data, the dashboard displays realistic demonstration data. This is useful for previewing the dashboard layout and functionality.

## Security Considerations

- The dashboard is intended for internal use only
- Do not expose to the public internet without authentication
- Assessment data may contain sensitive information
- Use HTTPS when deploying beyond localhost
