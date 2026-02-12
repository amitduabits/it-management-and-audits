# Screenshots Documentation

> This document describes the expected screenshots and visual documentation
> for the Web Application Security Scanner project.

---

## Screenshot Index

The following screenshots document the key interfaces and outputs of the
security scanner. Place screenshot files (PNG or JPG) in this directory
alongside this document.

---

## 1. Vulnerable Application Screenshots

### 1.1 Login Page
- **File:** `01_login_page.png`
- **Description:** The vulnerable application's login page at `http://127.0.0.1:5000/login`
- **Key Elements:**
  - Username and password input fields (no CSRF token)
  - Test credentials table displayed for convenience
  - SQL injection hint with example payload
  - Dark-themed UI with warning banner at the top

### 1.2 Search Page
- **File:** `02_search_page.png`
- **Description:** Product search page demonstrating XSS vulnerability
- **Key Elements:**
  - Search input field
  - Product results table
  - Reflected search query displayed (vulnerable to XSS)
  - SQL injection and XSS hints section

### 1.3 Profile Page (IDOR)
- **File:** `03_profile_page.png`
- **Description:** User profile page showing Insecure Direct Object Reference
- **Key Elements:**
  - User profile data including sensitive fields
  - User ID navigation buttons (demonstrating IDOR)
  - Exposed password field
  - IDOR vulnerability explanation

### 1.4 SQL Injection Demonstration
- **File:** `04_sqli_demo.png`
- **Description:** Successful SQL injection authentication bypass
- **Key Elements:**
  - Login form with `' OR '1'='1' --` as username
  - Redirect to search page (bypassed authentication)

### 1.5 XSS Demonstration
- **File:** `05_xss_demo.png`
- **Description:** Reflected XSS payload execution in search
- **Key Elements:**
  - Search field with `<script>alert('XSS')</script>` payload
  - Alert box demonstrating script execution

---

## 2. Scanner CLI Screenshots

### 2.1 Scanner Banner and Help
- **File:** `06_cli_help.png`
- **Description:** CLI help output showing available commands and options
- **Command:** `python -m scanner.cli --help`

### 2.2 Full Scan in Progress
- **File:** `07_scan_progress.png`
- **Description:** Console output during a full security scan
- **Key Elements:**
  - Ethical use disclaimer and confirmation prompt
  - Module-by-module progress output
  - Header check results
  - SQL injection test progress
  - XSS test progress

### 2.3 Scan Summary
- **File:** `08_scan_summary.png`
- **Description:** Console summary displayed after scan completion
- **Key Elements:**
  - Vulnerability count by severity
  - Risk score
  - Total requests sent
  - Scan duration

---

## 3. Report Screenshots

### 3.1 Report Header
- **File:** `09_report_header.png`
- **Description:** Top section of the generated HTML report
- **Key Elements:**
  - Report title and metadata
  - Target URL, scan timestamps, duration
  - Confidentiality banner

### 3.2 Executive Summary
- **File:** `10_report_summary.png`
- **Description:** Severity summary cards and distribution bar
- **Key Elements:**
  - Color-coded severity count cards (Critical, High, Medium, Low, Info)
  - Visual severity distribution bar
  - Risk score gauge with assessment text

### 3.3 Detailed Finding - SQL Injection
- **File:** `11_finding_sqli.png`
- **Description:** Detailed SQL injection finding in the report
- **Key Elements:**
  - Finding title with severity badge
  - Affected URL and parameter
  - Description with exploit details
  - Evidence box with SQL error
  - Remediation guidance
  - OWASP and CWE reference tags

### 3.4 Detailed Finding - Missing Headers
- **File:** `12_finding_headers.png`
- **Description:** Security header analysis findings
- **Key Elements:**
  - List of missing security headers
  - Individual header descriptions
  - Remediation recommendations

### 3.5 Recommendations Section
- **File:** `13_report_recommendations.png`
- **Description:** Prioritized recommendations at the end of the report
- **Key Elements:**
  - Ordered list of remediation priorities
  - Color-coded urgency levels

---

## 4. Test Results Screenshots

### 4.1 Passing Tests
- **File:** `14_test_results.png`
- **Description:** pytest output showing all tests passing
- **Command:** `python -m pytest tests/ -v`

### 4.2 Coverage Report
- **File:** `15_coverage_report.png`
- **Description:** Test coverage summary
- **Command:** `python -m pytest tests/ -v --cov=scanner`

---

## Capturing Screenshots

### Recommended Tools
- **Windows:** Snipping Tool (Win+Shift+S) or ShareX
- **macOS:** Screenshot utility (Cmd+Shift+4) or CleanShot X
- **Linux:** gnome-screenshot, Flameshot, or scrot
- **Terminal:** asciinema for recording terminal sessions

### Guidelines
- Use a resolution of at least 1920x1080
- Ensure the terminal font size is readable (14px+)
- Crop screenshots to show only relevant content
- Redact any real credentials or sensitive data
- Use PNG format for UI screenshots
- Use descriptive filenames matching the index above

### Automated Screenshot Script

A utility script can be created to capture screenshots automatically:

```python
#!/usr/bin/env python3
"""Screenshot capture helper for documentation."""

import subprocess
import time
import os

SCREENSHOTS_DIR = os.path.dirname(os.path.abspath(__file__))

def capture_screenshot(filename, delay=2):
    """Capture a screenshot after a delay."""
    print(f"Capturing {filename} in {delay} seconds...")
    time.sleep(delay)
    filepath = os.path.join(SCREENSHOTS_DIR, filename)

    # Windows
    # subprocess.run(['snippingtool', '/clip'])

    # Linux (requires scrot)
    # subprocess.run(['scrot', filepath])

    # macOS
    # subprocess.run(['screencapture', filepath])

    print(f"Saved to {filepath}")

if __name__ == '__main__':
    print("Position the window you want to capture.")
    capture_screenshot('screenshot.png', delay=5)
```

---

## Notes

- Screenshots should be updated whenever the UI or report format changes
- Each pull request that modifies the UI should include updated screenshots
- Store screenshots as PNG files in this directory
- Keep file sizes reasonable (under 500KB per image)
- Alternative text descriptions are provided above for accessibility
