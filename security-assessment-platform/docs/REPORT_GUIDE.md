# Report Generation Guide

## Overview

SecureAudit Pro generates three types of HTML reports, each designed for a specific audience. All reports are standalone HTML files with embedded CSS (no external dependencies).

## Report Types

### 1. Executive Summary
**Audience**: C-level executives, board members, non-technical stakeholders

**Contents**:
- Overall risk score with color-coded gauge
- Key metrics (total findings, critical count, severity distribution)
- Compliance status across all three frameworks
- Risk category breakdown
- Top 5 prioritized recommendations

**Generation**:
```bash
python -m src.cli generate-report --type executive --output ./reports
```

### 2. Technical Report
**Audience**: Security engineers, IT administrators, development teams

**Contents**:
- All findings sorted by CVSS severity (highest first)
- CVSS-aligned scoring with visual progress bars
- Evidence for each finding (ports, headers, configurations)
- Detailed remediation steps
- Compliance framework references per finding
- Finding statistics and category breakdown

**Generation**:
```bash
python -m src.cli generate-report --type technical --output ./reports
```

### 3. Remediation Roadmap
**Audience**: Project managers, security operations, IT leadership

**Contents**:
- Three-phase timeline visualization
- Phase 1: Quick Wins (0-30 days, low effort)
- Phase 2: Short-Term Actions (30-90 days, moderate effort)
- Phase 3: Long-Term Strategy (90-365 days, high effort)
- Effort estimation in hours per item
- Responsible team assignments
- Progress tracking placeholders

**Generation**:
```bash
python -m src.cli generate-report --type roadmap --output ./reports
```

## Customization

### Template Modification
Templates are located in `src/reporting/templates/`:
- `executive.html` - Executive summary template
- `technical.html` - Technical report template
- `roadmap.html` - Remediation roadmap template

Templates use Jinja2 syntax and can be customized for branding.

### Custom Template Directory
```python
from src.reporting.executive_report import ExecutiveReportGenerator
generator = ExecutiveReportGenerator(template_dir="/path/to/custom/templates")
```

## Report Distribution

- Reports are self-contained HTML files
- Can be printed to PDF via browser print function
- Suitable for email attachment (single file, no external resources)
- Should be treated as confidential security documentation
