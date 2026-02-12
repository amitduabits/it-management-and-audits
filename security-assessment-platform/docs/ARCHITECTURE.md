# System Architecture

## Overview

SecureAudit Pro follows a modular, layered architecture designed for extensibility, testability, and separation of concerns. Each layer operates independently and communicates through well-defined data contracts.

## Architecture Layers

### 1. Input Layer
- **Configuration Files** (`config/`): YAML-based target and threshold configuration
- **CLI Interface** (`src/cli.py`): Click-based command-line interface
- **Orchestrator** (`src/orchestrator.py`): Pipeline coordinator

### 2. Scanning Engine (`src/scanner/`)
Three specialized scanners operate independently:
- **NetworkScanner**: TCP connect scanning with concurrent thread pools, service banner grabbing
- **WebScanner**: HTTP security header analysis, SSL/TLS inspection, cookie audit, CORS evaluation
- **DNSScanner**: DNS record enumeration, SPF/DMARC validation, DNSSEC verification

### 3. Analysis Layer
- **Compliance Mapper** (`src/compliance/`): Maps findings to framework controls
- **Risk Engine** (`src/risk/risk_engine.py`): Weighted multi-category risk scoring
- **Risk Matrix** (`src/risk/risk_matrix.py`): 5x5 likelihood/impact visualization

### 4. Reporting Layer (`src/reporting/`)
- **Executive Report**: One-page summary for leadership audiences
- **Technical Report**: Detailed findings with CVSS scoring
- **Remediation Roadmap**: Phased action plan with effort estimates

### 5. Presentation Layer
- **Web Dashboard** (`dashboard/`): Flask-based interactive visualization
- **CLI Output**: Rich terminal formatting with tables and progress bars

## Data Flow

```
Configuration --> Orchestrator --> Scanners --> Raw Findings
                                                    |
                                                    v
                                            Findings Aggregator
                                                    |
                              +--------------------+--------------------+
                              |                    |                    |
                              v                    v                    v
                        Compliance Mapper    Risk Engine          Risk Matrix
                              |                    |                    |
                              v                    v                    v
                        Compliance Results   Risk Assessment     Matrix Plot
                              |                    |                    |
                              +--------------------+--------------------+
                                                    |
                                                    v
                                            Report Generator
                                                    |
                              +--------------------+--------------------+
                              |                    |                    |
                              v                    v                    v
                        Executive HTML      Technical HTML      Roadmap HTML
                              |                    |                    |
                              +--------------------+--------------------+
                                                    |
                                    +---------------+---------------+
                                    |                               |
                                    v                               v
                              File System                    Web Dashboard
```

## Key Design Decisions

1. **No External Scanning Dependencies**: Uses Python stdlib `socket` for port scanning (no nmap dependency)
2. **Graceful Degradation**: Each module handles missing optional libraries (`requests`, `dnspython`)
3. **Dataclass Results**: All scan results use Python dataclasses with `to_dict()` serialization
4. **Template-Based Reporting**: Jinja2 templates with CSS-in-HTML for portable reports
5. **Stateless Scanners**: Scanners are stateless; all state is in result objects
6. **Weighted Risk Model**: Configurable category weights enable organizational customization

## Module Dependencies

```
cli.py --> orchestrator.py --> scanner/ (network, web, dns)
                           --> compliance/ (iso27001, pci_dss, nist_csf)
                           --> risk/ (risk_engine, risk_matrix)
                           --> reporting/ (executive, technical, roadmap)
dashboard/app.py --> assessment data (JSON)
```
