"""
Incident Response Playbook Engine
=================================

A comprehensive incident response simulation and playbook management framework
built on NIST SP 800-61 Rev. 2 methodology.

Modules:
    models          - Core data models for incidents, alerts, evidence, and actions
    simulator       - Interactive incident response simulation engine
    timeline        - Incident timeline generation and management
    severity_calculator - CVSS-based severity scoring and business impact analysis
    evidence_tracker    - Digital evidence chain-of-custody management
    reporter        - Incident report generation engine
    cli             - Command-line interface

Scenario Modules:
    scenarios.data_breach    - Data exfiltration and breach response
    scenarios.ransomware     - Ransomware attack response
    scenarios.phishing_campaign       - Phishing campaign response
    scenarios.ddos_attack           - Distributed denial-of-service response
    scenarios.insider_threat - Insider threat response
"""

__version__ = "1.0.0"
__author__ = "Dr Amit Dua"
