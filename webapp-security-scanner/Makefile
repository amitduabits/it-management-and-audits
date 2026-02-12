# =============================================================================
# Web Application Security Scanner - Makefile
# =============================================================================
# Usage:
#   make setup          - Create venv and install dependencies
#   make run-target     - Start the vulnerable Flask application
#   make scan           - Run a full scan against the vulnerable app
#   make scan-quick     - Run header and directory scan only
#   make scan-sqli      - Run SQL injection scan only
#   make scan-xss       - Run XSS scan only
#   make scan-headers   - Run security header check only
#   make scan-ports     - Run port scan only
#   make scan-dirs      - Run directory enumeration only
#   make report         - Generate report from last scan
#   make test           - Run all unit tests
#   make test-cov       - Run tests with coverage report
#   make lint           - Run code linter
#   make clean          - Remove generated files
#   make help           - Show this help message
# =============================================================================

.PHONY: setup run-target scan scan-quick scan-sqli scan-xss scan-headers \
        scan-ports scan-dirs report test test-cov lint clean help

# Configuration
PYTHON       = python
PIP          = pip
PYTEST       = python -m pytest
TARGET_URL   = http://127.0.0.1:5000
REPORT_DIR   = reports
VENV_DIR     = venv
SCANNER_CLI  = python -m scanner.cli

# Default target
.DEFAULT_GOAL := help

# =============================================================================
# Setup
# =============================================================================

setup: ## Create virtual environment and install all dependencies
	@echo "============================================"
	@echo "  Setting up development environment..."
	@echo "============================================"
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Virtual environment created at $(VENV_DIR)/"
	@echo ""
	@echo "Activate the virtual environment:"
	@echo "  Windows: $(VENV_DIR)\Scripts\activate"
	@echo "  Linux/Mac: source $(VENV_DIR)/bin/activate"
	@echo ""
	@echo "Then run: pip install -r requirements.txt"

install: ## Install dependencies (run after activating venv)
	$(PIP) install -r requirements.txt
	@echo ""
	@echo "[+] Dependencies installed successfully."

install-dev: ## Install dev dependencies
	$(PIP) install -r requirements.txt
	$(PIP) install flake8 black mypy
	@echo ""
	@echo "[+] Dev dependencies installed."

# =============================================================================
# Vulnerable Target Application
# =============================================================================

run-target: ## Start the vulnerable Flask application on localhost:5000
	@echo "============================================"
	@echo "  Starting Vulnerable Web Application"
	@echo "  WARNING: Localhost use ONLY!"
	@echo "============================================"
	cd vulnerable_app && $(PYTHON) app.py

init-db: ## Initialize the vulnerable app database
	cd vulnerable_app && $(PYTHON) database.py

# =============================================================================
# Security Scanning
# =============================================================================

scan: ## Run a full security scan against the target (all modules)
	@echo "============================================"
	@echo "  Running Full Security Scan"
	@echo "  Target: $(TARGET_URL)"
	@echo "============================================"
	$(SCANNER_CLI) scan \
		--target $(TARGET_URL) \
		--output $(REPORT_DIR)/full_scan_report.html \
		--modules headers,sqli,xss,ports,dirs \
		--accept-disclaimer

scan-quick: ## Run a quick scan (headers + directories only)
	@echo "============================================"
	@echo "  Running Quick Scan (Headers + Directories)"
	@echo "============================================"
	$(SCANNER_CLI) scan \
		--target $(TARGET_URL) \
		--output $(REPORT_DIR)/quick_scan_report.html \
		--modules headers,dirs \
		--accept-disclaimer

scan-sqli: ## Run SQL injection scan only
	@echo "  Running SQL Injection Scan..."
	$(SCANNER_CLI) scan \
		--target $(TARGET_URL) \
		--output $(REPORT_DIR)/sqli_report.html \
		--modules sqli \
		--accept-disclaimer \
		--verbose

scan-xss: ## Run XSS scan only
	@echo "  Running XSS Scan..."
	$(SCANNER_CLI) scan \
		--target $(TARGET_URL) \
		--output $(REPORT_DIR)/xss_report.html \
		--modules xss \
		--accept-disclaimer \
		--verbose

scan-headers: ## Run security header check only
	@echo "  Running Security Header Check..."
	$(SCANNER_CLI) scan \
		--target $(TARGET_URL) \
		--output $(REPORT_DIR)/headers_report.html \
		--modules headers \
		--accept-disclaimer \
		--verbose

scan-ports: ## Run TCP port scan only
	@echo "  Running Port Scan..."
	$(SCANNER_CLI) scan \
		--target $(TARGET_URL) \
		--output $(REPORT_DIR)/ports_report.html \
		--modules ports \
		--accept-disclaimer \
		--verbose

scan-dirs: ## Run directory enumeration only
	@echo "  Running Directory Enumeration..."
	$(SCANNER_CLI) scan \
		--target $(TARGET_URL) \
		--output $(REPORT_DIR)/dirs_report.html \
		--modules dirs \
		--accept-disclaimer \
		--verbose

scan-verbose: ## Run full scan with verbose output
	$(SCANNER_CLI) scan \
		--target $(TARGET_URL) \
		--output $(REPORT_DIR)/verbose_report.html \
		--modules headers,sqli,xss,ports,dirs \
		--accept-disclaimer \
		--verbose

scan-json: ## Run full scan and output JSON report
	$(SCANNER_CLI) scan \
		--target $(TARGET_URL) \
		--output $(REPORT_DIR)/scan_report.json \
		--format json \
		--accept-disclaimer

report: ## Generate both HTML and JSON reports
	$(SCANNER_CLI) scan \
		--target $(TARGET_URL) \
		--output $(REPORT_DIR)/combined_report.html \
		--format both \
		--accept-disclaimer

# =============================================================================
# Testing
# =============================================================================

test: ## Run all unit tests
	@echo "============================================"
	@echo "  Running Unit Tests"
	@echo "============================================"
	$(PYTEST) tests/ -v

test-cov: ## Run tests with coverage report
	$(PYTEST) tests/ -v --cov=scanner --cov-report=html --cov-report=term-missing

test-watch: ## Run tests in watch mode (requires pytest-watch)
	$(PYTHON) -m pytest_watch tests/ -- -v

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run flake8 linter
	flake8 scanner/ --max-line-length=100 --statistics

format: ## Format code with black
	black scanner/ tests/ --line-length=100

typecheck: ## Run mypy type checker
	mypy scanner/ --ignore-missing-imports

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Remove generated files and caches
	@echo "Cleaning up..."
	rm -rf __pycache__
	rm -rf scanner/__pycache__
	rm -rf tests/__pycache__
	rm -rf vulnerable_app/__pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	rm -f vulnerable_app/*.db
	rm -f reports/*.html reports/*.json
	@echo "  (keeping reports/template.html)"
	git checkout -- reports/template.html 2>/dev/null || true
	@echo "[+] Cleanup complete."

clean-reports: ## Remove only generated reports
	rm -f reports/scan_*.html reports/scan_*.json
	rm -f reports/full_*.html reports/quick_*.html
	rm -f reports/sqli_*.html reports/xss_*.html
	rm -f reports/headers_*.html reports/ports_*.html
	rm -f reports/dirs_*.html reports/combined_*.html
	rm -f reports/verbose_*.html
	@echo "[+] Reports cleaned."

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo ""
	@echo "  Web Application Security Scanner - Make Targets"
	@echo "  ================================================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Example workflow:"
	@echo "    1. make setup          # Set up environment"
	@echo "    2. make install        # Install dependencies"
	@echo "    3. make run-target     # Start vulnerable app (in terminal 1)"
	@echo "    4. make scan           # Run full scan (in terminal 2)"
	@echo "    5. make test           # Run tests"
	@echo ""
