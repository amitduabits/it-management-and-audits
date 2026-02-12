"""
Flask Web Dashboard - Interactive security assessment visualization.

Provides a professional web interface for exploring assessment results:
    - Risk overview with gauge charts and trend indicators
    - Findings explorer with filtering and search
    - Compliance status by framework with drill-down
    - Remediation tracker with progress visualization

ETHICAL USE NOTICE:
    This dashboard displays results from authorized security assessments only.
    Ensure all assessment data is handled according to your organization's
    data classification and handling policies.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, render_template, jsonify, request

logger = logging.getLogger(__name__)

# Base directory for the dashboard
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(DASHBOARD_DIR, "templates")
STATIC_DIR = os.path.join(DASHBOARD_DIR, "static")


def create_app(assessment_data: Optional[Dict[str, Any]] = None) -> Flask:
    """
    Create and configure the Flask dashboard application.

    Args:
        assessment_data: Pre-loaded assessment data dictionary.
            If None, uses demo data for display purposes.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(
        __name__,
        template_folder=TEMPLATE_DIR,
        static_folder=STATIC_DIR,
    )
    app.config["SECRET_KEY"] = os.urandom(32).hex()

    # Store assessment data in app config
    if assessment_data:
        app.config["ASSESSMENT_DATA"] = assessment_data
    else:
        app.config["ASSESSMENT_DATA"] = _get_demo_data()

    @app.route("/")
    def index():
        """Dashboard home - Risk overview."""
        data = app.config["ASSESSMENT_DATA"]
        return render_template(
            "index.html",
            risk_data=data.get("risk", {}),
            scan_data=data.get("scan_summary", {}),
            compliance_data=data.get("compliance", {}),
            page="home",
        )

    @app.route("/findings")
    def findings():
        """Findings explorer with filtering."""
        data = app.config["ASSESSMENT_DATA"]
        all_findings = data.get("findings", [])

        # Filter parameters
        severity = request.args.get("severity", "all")
        category = request.args.get("category", "all")
        search = request.args.get("search", "").lower()

        filtered = all_findings
        if severity != "all":
            filtered = [
                f for f in filtered
                if f.get("severity", "").lower() == severity.lower()
            ]
        if category != "all":
            filtered = [
                f for f in filtered
                if f.get("category", "").lower() == category.lower()
            ]
        if search:
            filtered = [
                f for f in filtered
                if search in f.get("title", "").lower()
                or search in f.get("description", "").lower()
            ]

        # Get unique categories for filter dropdown
        categories = sorted(set(
            f.get("category", "Other") for f in all_findings
        ))
        severities = ["critical", "high", "medium", "low", "info"]

        return render_template(
            "findings.html",
            findings=filtered,
            total_findings=len(all_findings),
            filtered_count=len(filtered),
            categories=categories,
            severities=severities,
            current_severity=severity,
            current_category=category,
            current_search=search,
            page="findings",
        )

    @app.route("/compliance")
    def compliance():
        """Compliance status by framework."""
        data = app.config["ASSESSMENT_DATA"]
        compliance_data = data.get("compliance", {})
        return render_template(
            "compliance.html",
            iso27001=compliance_data.get("iso27001", {}),
            pci_dss=compliance_data.get("pci_dss", {}),
            nist_csf=compliance_data.get("nist_csf", {}),
            page="compliance",
        )

    @app.route("/remediation")
    def remediation():
        """Remediation tracker."""
        data = app.config["ASSESSMENT_DATA"]
        roadmap = data.get("remediation", {})
        return render_template(
            "remediation.html",
            quick_wins=roadmap.get("quick_wins", []),
            short_term=roadmap.get("short_term", []),
            long_term=roadmap.get("long_term", []),
            summary=roadmap.get("summary", {}),
            page="remediation",
        )

    # API endpoints for AJAX updates
    @app.route("/api/risk-summary")
    def api_risk_summary():
        """JSON endpoint for risk summary data."""
        data = app.config["ASSESSMENT_DATA"]
        return jsonify(data.get("risk", {}))

    @app.route("/api/findings")
    def api_findings():
        """JSON endpoint for findings data."""
        data = app.config["ASSESSMENT_DATA"]
        return jsonify(data.get("findings", []))

    @app.route("/api/compliance")
    def api_compliance():
        """JSON endpoint for compliance data."""
        data = app.config["ASSESSMENT_DATA"]
        return jsonify(data.get("compliance", {}))

    return app


def _get_demo_data() -> Dict[str, Any]:
    """
    Generate demonstration data for the dashboard.

    Returns realistic-looking assessment data when no actual scan
    results are available.
    """
    return {
        "risk": {
            "overall_risk_score": 6.4,
            "overall_risk_level": "high",
            "risk_trend": "stable",
            "total_findings": 23,
            "severity_distribution": {
                "critical": 3,
                "high": 7,
                "medium": 8,
                "low": 4,
                "info": 1,
            },
            "categories": [
                {
                    "display_name": "Network Security",
                    "raw_score": 7.5,
                    "weighted_score": 1.88,
                    "weight": 0.25,
                    "risk_level": "high",
                    "finding_count": 8,
                    "critical_count": 2,
                    "high_count": 3,
                    "medium_count": 2,
                    "low_count": 1,
                },
                {
                    "display_name": "Application Security",
                    "raw_score": 5.8,
                    "weighted_score": 1.16,
                    "weight": 0.20,
                    "risk_level": "medium",
                    "finding_count": 6,
                    "critical_count": 0,
                    "high_count": 2,
                    "medium_count": 3,
                    "low_count": 1,
                },
                {
                    "display_name": "Data Protection",
                    "raw_score": 6.2,
                    "weighted_score": 1.24,
                    "weight": 0.20,
                    "risk_level": "high",
                    "finding_count": 4,
                    "critical_count": 1,
                    "high_count": 1,
                    "medium_count": 1,
                    "low_count": 1,
                },
                {
                    "display_name": "Compliance",
                    "raw_score": 5.5,
                    "weighted_score": 0.83,
                    "weight": 0.15,
                    "risk_level": "medium",
                    "finding_count": 3,
                    "critical_count": 0,
                    "high_count": 1,
                    "medium_count": 2,
                    "low_count": 0,
                },
                {
                    "display_name": "Operational Security",
                    "raw_score": 3.2,
                    "weighted_score": 0.32,
                    "weight": 0.10,
                    "risk_level": "low",
                    "finding_count": 1,
                    "critical_count": 0,
                    "high_count": 0,
                    "medium_count": 1,
                    "low_count": 0,
                },
                {
                    "display_name": "Third-Party Risk",
                    "raw_score": 2.5,
                    "weighted_score": 0.25,
                    "weight": 0.10,
                    "risk_level": "low",
                    "finding_count": 1,
                    "critical_count": 0,
                    "high_count": 0,
                    "medium_count": 0,
                    "low_count": 1,
                },
            ],
            "recommendations": [
                {"priority": 1, "urgency": "immediate", "category": "Network Security", "recommendation": "Address critical network exposures including RDP and database services.", "timeframe": "0-30 days"},
                {"priority": 2, "urgency": "immediate", "category": "Data Protection", "recommendation": "Renew expiring SSL certificate and implement HSTS.", "timeframe": "0-30 days"},
                {"priority": 3, "urgency": "short_term", "category": "Application Security", "recommendation": "Implement Content-Security-Policy and fix CORS misconfigurations.", "timeframe": "30-90 days"},
                {"priority": 4, "urgency": "short_term", "category": "Compliance", "recommendation": "Address PCI-DSS Requirement 2.2 and ISO 27001 A.8.20 gaps.", "timeframe": "30-90 days"},
                {"priority": 5, "urgency": "long_term", "category": "Operational Security", "recommendation": "Establish configuration baselines and monitoring capabilities.", "timeframe": "90-365 days"},
            ],
        },
        "findings": [
            {"id": "NET-03389", "title": "RDP Service Exposed", "description": "Remote Desktop Protocol accessible on port 3389.", "category": "Network Security", "severity": "critical", "cvss_score": 9.0, "remediation": "Require VPN for RDP access. Enable NLA.", "evidence": "Port 3389/RDP is open"},
            {"id": "NET-06379", "title": "Redis Service Exposed", "description": "Redis accessible without authentication.", "category": "Network Security", "severity": "critical", "cvss_score": 9.8, "remediation": "Enable Redis AUTH. Bind to localhost.", "evidence": "Port 6379/Redis is open"},
            {"id": "NET-00445", "title": "SMB Service Exposed", "description": "SMB service accessible on the network.", "category": "Network Security", "severity": "high", "cvss_score": 8.0, "remediation": "Disable SMBv1. Require SMB signing.", "evidence": "Port 445/SMB is open"},
            {"id": "WEB-SSL-EXPIRING", "title": "SSL Certificate Expiring Soon", "description": "Certificate expires in 25 days.", "category": "Web Security", "severity": "high", "cvss_score": 7.0, "remediation": "Renew SSL certificate immediately.", "evidence": "Certificate expiry: 25 days"},
            {"id": "WEB-HDR-001", "title": "Missing HSTS Header", "description": "Strict-Transport-Security header not present.", "category": "Web Security", "severity": "high", "cvss_score": 7.4, "remediation": "Add HSTS header with max-age=31536000.", "evidence": "Header not set"},
            {"id": "WEB-HDR-002", "title": "Missing Content-Security-Policy", "description": "CSP header not configured.", "category": "Web Security", "severity": "high", "cvss_score": 7.1, "remediation": "Implement CSP to restrict resource loading.", "evidence": "Header not set"},
            {"id": "DNS-SPF-MISSING", "title": "Missing SPF Record", "description": "No SPF record found for the domain.", "category": "Email Security", "severity": "high", "cvss_score": 7.5, "remediation": "Create SPF TXT record.", "evidence": "No v=spf1 record found"},
            {"id": "DNS-DMARC-NONE", "title": "DMARC Policy None", "description": "DMARC set to monitoring only.", "category": "Email Security", "severity": "medium", "cvss_score": 5.5, "remediation": "Upgrade DMARC to quarantine/reject.", "evidence": "p=none"},
            {"id": "WEB-HDR-003", "title": "Missing X-Frame-Options", "description": "Clickjacking protection absent.", "category": "Web Security", "severity": "medium", "cvss_score": 5.4, "remediation": "Add X-Frame-Options: DENY.", "evidence": "Header not set"},
            {"id": "WEB-CORS-WILDCARD", "title": "CORS Allows All Origins", "description": "Access-Control-Allow-Origin set to *.", "category": "Web Security", "severity": "medium", "cvss_score": 5.3, "remediation": "Restrict to trusted origins.", "evidence": "ACAO: *"},
            {"id": "NET-EXCESS", "title": "Excessive Open Ports", "description": "15 open ports detected.", "category": "Network Security", "severity": "medium", "cvss_score": 5.0, "remediation": "Disable unnecessary services.", "evidence": "15 open ports"},
        ],
        "compliance": {
            "iso27001": {
                "framework": "ISO 27001:2022",
                "overall_percentage": 55.0,
                "passed": 7,
                "failed": 6,
                "partial": 4,
                "not_assessed": 3,
                "total_controls": 20,
                "category_scores": {
                    "Organizational Controls": 45.0,
                    "People Controls": 50.0,
                    "Physical Controls": 50.0,
                    "Technological Controls": 58.5,
                },
            },
            "pci_dss": {
                "framework": "PCI-DSS v4.0",
                "overall_percentage": 48.0,
                "passed": 5,
                "failed": 5,
                "partial": 3,
                "not_assessed": 2,
                "total_requirements": 15,
                "section_scores": {
                    "Build and Maintain a Secure Network": 40.0,
                    "Protect Account Data": 50.0,
                    "Maintain a Vulnerability Management Program": 50.0,
                    "Develop and Maintain Secure Systems": 55.0,
                    "Implement Strong Access Control": 45.0,
                    "Track and Monitor All Access": 50.0,
                    "Regularly Test Security Systems": 50.0,
                    "Maintain an Information Security Policy": 50.0,
                },
            },
            "nist_csf": {
                "framework": "NIST CSF v2.0",
                "overall_percentage": 52.0,
                "passed": 6,
                "failed": 5,
                "partial": 5,
                "not_assessed": 4,
                "total_subcategories": 20,
                "overall_tier": 2,
                "overall_tier_name": "Risk Informed",
                "function_scores": {
                    "Identify": 55.0,
                    "Protect": 50.0,
                    "Detect": 45.0,
                    "Respond": 50.0,
                    "Recover": 50.0,
                },
            },
        },
        "remediation": {
            "quick_wins": [
                {"title": "Add HSTS Header", "severity": "high", "effort": "low", "estimated_hours": 2, "responsible_team": "Web Development / DevOps", "remediation_steps": "Add Strict-Transport-Security header to web server configuration."},
                {"title": "Add X-Frame-Options Header", "severity": "medium", "effort": "low", "estimated_hours": 1, "responsible_team": "Web Development / DevOps", "remediation_steps": "Add X-Frame-Options: DENY header."},
                {"title": "Remove Server Header", "severity": "low", "effort": "low", "estimated_hours": 1, "responsible_team": "Web Development / DevOps", "remediation_steps": "Configure web server to suppress version information."},
            ],
            "short_term": [
                {"title": "Restrict RDP Access", "severity": "critical", "effort": "medium", "estimated_hours": 8, "responsible_team": "Network Engineering", "remediation_steps": "Configure VPN requirement for RDP. Enable NLA."},
                {"title": "Secure Redis Instance", "severity": "critical", "effort": "medium", "estimated_hours": 4, "responsible_team": "Infrastructure / DevOps", "remediation_steps": "Enable Redis AUTH. Bind to localhost."},
                {"title": "Renew SSL Certificate", "severity": "high", "effort": "medium", "estimated_hours": 4, "responsible_team": "Infrastructure / DevOps", "remediation_steps": "Renew and install new SSL certificate."},
                {"title": "Implement SPF Record", "severity": "high", "effort": "medium", "estimated_hours": 4, "responsible_team": "DNS / Email Administration", "remediation_steps": "Create SPF TXT record with authorized senders."},
            ],
            "long_term": [
                {"title": "Implement Network Segmentation", "severity": "high", "effort": "high", "estimated_hours": 80, "responsible_team": "Network Engineering", "remediation_steps": "Design and implement network segmentation for CDE."},
                {"title": "Deploy SIEM Solution", "severity": "medium", "effort": "high", "estimated_hours": 120, "responsible_team": "Information Security", "remediation_steps": "Select, deploy, and configure centralized logging and monitoring."},
                {"title": "Security Awareness Training", "severity": "medium", "effort": "high", "estimated_hours": 40, "responsible_team": "Security Governance / GRC", "remediation_steps": "Establish ongoing security awareness training program."},
            ],
            "summary": {
                "total_items": 10,
                "quick_wins_count": 3,
                "short_term_count": 4,
                "long_term_count": 3,
                "total_estimated_hours": 264,
                "estimated_days": 33.0,
                "phase_breakdown": {
                    "quick_wins": {"count": 3, "hours": 4, "timeframe": "0-30 days", "label": "Quick Wins"},
                    "short_term": {"count": 4, "hours": 20, "timeframe": "30-90 days", "label": "Short-Term"},
                    "long_term": {"count": 3, "hours": 240, "timeframe": "90-365 days", "label": "Long-Term"},
                },
            },
        },
        "scan_summary": {
            "targets": ["192.168.1.1"],
            "scan_types": ["Network", "Web", "DNS"],
            "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        },
    }


def run_dashboard(
    host: str = "127.0.0.1",
    port: int = 5000,
    debug: bool = False,
    assessment_data: Optional[Dict] = None,
):
    """
    Run the Flask dashboard server.

    Args:
        host: Host to bind to (default localhost).
        port: Port to listen on (default 5000).
        debug: Enable Flask debug mode.
        assessment_data: Assessment data to display.
    """
    app = create_app(assessment_data)
    logger.info(f"Starting dashboard at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_dashboard(debug=True)
