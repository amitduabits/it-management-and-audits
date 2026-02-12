"""
IT Audit Toolkit - Professional IT Audit Management Suite

A structured toolkit for planning, executing, and reporting on Information
Technology audits. Provides pre-built control checklists, risk assessment
calculations, and professional report generation.

Modules:
    models          - Core data models for audit engagements, controls, and findings
    audit_engine    - Audit execution engine for running checklists and collecting evidence
    risk_calculator - Risk scoring using likelihood x impact matrix methodology
    reporter        - Professional report generation with Jinja2 templates
    cli             - Command-line interface built on Click
"""

__version__ = "1.0.0"
__author__ = "Dr Amit Dua"

from src.models import (
    AuditEngagement,
    AuditArea,
    Control,
    Finding,
    Evidence,
    RiskRating,
    ControlStatus,
    FindingSeverity,
    EngagementStatus,
)
