# SecureAudit Pro - Build Automation
# ====================================
# Usage: make <target>
#
# ETHICAL USE: Only scan systems you own or have authorization to test.

.PHONY: help install scan-network scan-web scan-dns scan compliance risk report dashboard full-assessment test lint clean

# Default target
help:
	@echo "SecureAudit Pro - Available Targets"
	@echo "===================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install Python dependencies"
	@echo "  make install-dev      Install dev dependencies"
	@echo ""
	@echo "Scanning:"
	@echo "  make scan-network     Run network scan (TARGET required)"
	@echo "  make scan-web         Run web security scan (URL required)"
	@echo "  make scan-dns         Run DNS scan (DOMAIN required)"
	@echo "  make scan             Run all scans"
	@echo ""
	@echo "Analysis:"
	@echo "  make compliance       Run compliance checks"
	@echo "  make risk             Calculate risk scores"
	@echo ""
	@echo "Reporting:"
	@echo "  make report           Generate all reports"
	@echo "  make dashboard        Launch web dashboard"
	@echo ""
	@echo "Full Pipeline:"
	@echo "  make full-assessment  Run complete assessment"
	@echo ""
	@echo "Development:"
	@echo "  make test             Run all tests"
	@echo "  make lint             Run code linting"
	@echo "  make clean            Remove generated files"
	@echo ""
	@echo "Examples:"
	@echo "  make scan-network TARGET=192.168.1.1"
	@echo "  make scan-web URL=https://example.com"
	@echo "  make full-assessment TARGET=192.168.1.1 URL=https://example.com DOMAIN=example.com"

# Variables (override with make TARGET=x.x.x.x)
TARGET ?= 127.0.0.1
URL ?=
DOMAIN ?= $(TARGET)
OUTPUT ?= ./reports
ORG ?= Organization
PORTS ?= 1-1024

# Setup
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov flake8 black

# Scanning
scan-network:
	python -m src.cli scan-network --target $(TARGET) --ports $(PORTS) --output $(OUTPUT)/network_scan.json

scan-web:
ifdef URL
	python -m src.cli scan-web --url $(URL) --output $(OUTPUT)/web_scan.json
else
	@echo "ERROR: URL is required. Usage: make scan-web URL=https://example.com"
endif

scan-dns:
	python -m src.cli scan-dns --domain $(DOMAIN) --output $(OUTPUT)/dns_scan.json

scan: scan-network scan-dns
ifdef URL
	$(MAKE) scan-web URL=$(URL)
endif

# Analysis
compliance:
	python -m src.cli check-compliance --framework all --output $(OUTPUT)/compliance.json

risk:
	python -m src.cli calculate-risk --output $(OUTPUT)/risk.json

# Reporting
report:
	python -m src.cli generate-report --type all --output $(OUTPUT) --organization "$(ORG)"

# Dashboard
dashboard:
	python -m src.cli start-dashboard --port 5000

# Full pipeline
full-assessment:
	python -m src.cli full-assessment --target $(TARGET) --output $(OUTPUT) --organization "$(ORG)" \
		$(if $(URL),--url $(URL),) \
		$(if $(DOMAIN),--domain $(DOMAIN),)

# Development
test:
	python -m pytest tests/ -v --tb=short

test-coverage:
	python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint:
	flake8 src/ tests/ --max-line-length=100 --ignore=E501
	black --check src/ tests/

format:
	black src/ tests/

# Cleanup
clean:
	rm -rf reports/ output/ htmlcov/ .pytest_cache/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
