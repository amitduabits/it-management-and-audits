# Environment Setup Guide

> Complete guide for setting up the Web Application Security Scanner
> development and testing environment.

---

## Prerequisites

Before setting up the project, ensure the following software is installed:

| Software | Minimum Version | Purpose |
|---|---|---|
| Python | 3.8+ | Runtime environment |
| pip | 21.0+ | Package management |
| Git | 2.30+ | Version control |
| Make | 3.81+ | Build automation (optional) |

### Verifying Prerequisites

```bash
# Check Python version
python --version
# Expected output: Python 3.8.x or higher

# Check pip version
pip --version
# Expected output: pip 21.x or higher

# Check Git version
git --version
# Expected output: git version 2.30.x or higher
```

---

## Installation Steps

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd webapp-security-scanner
```

### Step 2: Create a Virtual Environment

It is strongly recommended to use a Python virtual environment to isolate
project dependencies from your system Python installation.

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt, indicating the virtual
environment is active.

### Step 3: Install Dependencies

```bash
# Install all project dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

This installs:
- **Flask** - Web framework for the vulnerable application
- **requests** - HTTP library for the scanner
- **click** - CLI framework
- **Jinja2** - Template engine for reports
- **pytest** - Testing framework
- **pytest-cov** - Test coverage reporting
- **pytest-mock** - Mocking utilities for tests

### Step 4: Verify Installation

```bash
# Check that the scanner CLI is accessible
python -m scanner.cli --help

# Run the test suite
python -m pytest tests/ -v

# Check that the vulnerable app dependencies are met
cd vulnerable_app
python -c "import flask; print(f'Flask {flask.__version__} installed successfully')"
cd ..
```

---

## Running the Vulnerable Application

### Important Safety Notice

The vulnerable application is designed to run on **localhost only** (127.0.0.1).
Never expose it to any network or deploy it on a public server.

### Starting the Application

**Using Make:**
```bash
make run-target
```

**Manual start:**
```bash
cd vulnerable_app
python app.py
```

### Expected Output

```
[+] Database initialized at: vulnerable.db
[+] Created tables: users, products, orders, audit_log, sessions
[+] Inserted 10 sample users
[+] Inserted 15 sample products
[+] Inserted 10 sample orders

======================================================================
  WARNING: INTENTIONALLY VULNERABLE APPLICATION
  This application contains deliberate security vulnerabilities.
  DO NOT expose this to any network. Localhost use ONLY.
======================================================================

  Starting vulnerable web application on http://127.0.0.1:5000
  Press Ctrl+C to stop.
```

### Accessing the Application

Open a web browser and navigate to: `http://127.0.0.1:5000`

Test credentials:
| Username | Password | Role |
|---|---|---|
| admin | admin123 | Administrator |
| john_doe | password123 | User |
| jane_smith | letmein | User |

---

## Running a Security Scan

### Using the CLI

Open a **second terminal** (keep the vulnerable app running in the first):

```bash
# Activate the virtual environment
# Windows: venv\Scripts\activate
# Linux: source venv/bin/activate

# Run a full scan
python -m scanner.cli scan --target http://127.0.0.1:5000 --output reports/scan_report.html --accept-disclaimer
```

### Using Make

```bash
# Full scan
make scan

# Quick scan (headers + directories only)
make scan-quick

# SQL injection scan only
make scan-sqli

# XSS scan only
make scan-xss
```

### Viewing Reports

After a scan completes, open the generated HTML report in your browser:

```bash
# The report will be saved to the reports/ directory
# Open reports/scan_report.html in your browser
```

---

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ -v --cov=scanner --cov-report=html

# Open coverage report
# The HTML coverage report will be in htmlcov/index.html
```

---

## Project Structure Overview

```
webapp-security-scanner/
|-- vulnerable_app/       # Target app (run on localhost only)
|-- scanner/              # Security scanner modules
|-- reports/              # Generated reports + template
|-- tests/                # Test suite
|-- docs/                 # Documentation
|-- requirements.txt      # Python dependencies
|-- Makefile              # Build automation
|-- .gitignore            # Git ignore rules
|-- LICENSE               # MIT License
|-- README.md             # Project overview
```

---

## Troubleshooting

### Common Issues

**Issue: "ModuleNotFoundError: No module named 'flask'"**
- Solution: Ensure you activated the virtual environment and ran `pip install -r requirements.txt`

**Issue: "Connection refused" when scanning**
- Solution: Ensure the vulnerable app is running in a separate terminal on port 5000

**Issue: "Address already in use" when starting the app**
- Solution: Another process is using port 5000. Kill it or change the port in `app.py`

**Issue: Tests failing with import errors**
- Solution: Run tests from the project root directory, not from the tests/ directory

**Issue: Permission denied errors on Linux/macOS**
- Solution: Port scanning requires elevated privileges for some port ranges.
  Run with `sudo` if scanning privileged ports (below 1024) on remote hosts.

### Getting Help

1. Check the error message carefully for clues
2. Review the documentation in the `docs/` directory
3. Check that all prerequisites are installed and at the correct versions
4. Ensure you are running commands from the project root directory
5. Verify the virtual environment is activated

---

## Development Workflow

For contributors:

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes to scanner modules in `scanner/`
3. Add tests for new functionality in `tests/`
4. Run tests: `python -m pytest tests/ -v`
5. Run linter: `flake8 scanner/ --max-line-length=100`
6. Commit changes with descriptive messages
7. Submit a pull request

---

*Always remember: Only use this tool against systems you own or have written authorization to test.*
