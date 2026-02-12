"""
Core data models for the IT Audit Toolkit.

Defines the primary entities used throughout the audit lifecycle:
engagements, audit areas, controls, findings, evidence, and risk ratings.
All models use Python dataclasses with JSON serialization support.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from enum import Enum
from typing import Optional
import json
import uuid


class EngagementStatus(str, Enum):
    """Lifecycle status of an audit engagement."""
    PLANNING = "planning"
    FIELDWORK = "fieldwork"
    ANALYSIS = "analysis"
    REPORTING = "reporting"
    FOLLOW_UP = "follow_up"
    CLOSED = "closed"


class ControlStatus(str, Enum):
    """Assessment status of an individual control."""
    NOT_TESTED = "not_tested"
    EFFECTIVE = "effective"
    PARTIALLY_EFFECTIVE = "partially_effective"
    INEFFECTIVE = "ineffective"
    NOT_APPLICABLE = "not_applicable"


class FindingSeverity(str, Enum):
    """Severity classification for audit findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class EvidenceType(str, Enum):
    """Type classification for audit evidence."""
    DOCUMENT = "document"
    SCREENSHOT = "screenshot"
    CONFIGURATION = "configuration"
    LOG_EXTRACT = "log_extract"
    INTERVIEW_NOTES = "interview_notes"
    OBSERVATION = "observation"
    SYSTEM_OUTPUT = "system_output"
    POLICY = "policy"
    PROCEDURE = "procedure"


@dataclass
class RiskRating:
    """
    Quantitative risk rating based on likelihood and impact scores.

    Risk is calculated as likelihood x impact, producing a score from 1-25
    on a 5x5 matrix. The score maps to a severity classification:
        - 20-25: Critical
        - 12-19: High
        - 6-11:  Medium
        - 2-5:   Low
        - 1:     Informational

    Attributes:
        likelihood: Probability of occurrence (1=Rare, 2=Unlikely,
                    3=Possible, 4=Likely, 5=Almost Certain)
        impact: Business impact if realized (1=Negligible, 2=Minor,
                3=Moderate, 4=Major, 5=Severe)
        score: Computed risk score (likelihood x impact)
        severity: Derived severity classification
        rationale: Explanation for the assigned ratings
    """
    likelihood: int
    impact: int
    score: int = field(init=False)
    severity: str = field(init=False)
    rationale: str = ""

    def __post_init__(self):
        if not (1 <= self.likelihood <= 5):
            raise ValueError(f"Likelihood must be 1-5, got {self.likelihood}")
        if not (1 <= self.impact <= 5):
            raise ValueError(f"Impact must be 1-5, got {self.impact}")
        self.score = self.likelihood * self.impact
        self.severity = self._compute_severity()

    def _compute_severity(self) -> str:
        """Map numeric risk score to severity classification."""
        if self.score >= 20:
            return FindingSeverity.CRITICAL.value
        elif self.score >= 12:
            return FindingSeverity.HIGH.value
        elif self.score >= 6:
            return FindingSeverity.MEDIUM.value
        elif self.score >= 2:
            return FindingSeverity.LOW.value
        else:
            return FindingSeverity.INFORMATIONAL.value

    def to_dict(self) -> dict:
        return {
            "likelihood": self.likelihood,
            "impact": self.impact,
            "score": self.score,
            "severity": self.severity,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RiskRating":
        rating = cls(
            likelihood=data["likelihood"],
            impact=data["impact"],
            rationale=data.get("rationale", ""),
        )
        return rating


@dataclass
class Evidence:
    """
    Audit evidence collected during fieldwork.

    Each piece of evidence is linked to a specific control or finding
    and includes metadata about its source, type, and collection date.

    Attributes:
        evidence_id: Unique identifier for this evidence item
        title: Brief descriptive title
        evidence_type: Classification of the evidence (document, screenshot, etc.)
        description: Detailed description of what this evidence demonstrates
        source: Where the evidence was obtained (system, person, document)
        file_reference: Path or reference to the evidence file
        collected_date: Date the evidence was collected
        collected_by: Name of the auditor who collected the evidence
        control_ref: Reference ID of the related control (optional)
        finding_ref: Reference ID of the related finding (optional)
        notes: Additional auditor notes
    """
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    title: str = ""
    evidence_type: str = EvidenceType.DOCUMENT.value
    description: str = ""
    source: str = ""
    file_reference: str = ""
    collected_date: str = field(default_factory=lambda: date.today().isoformat())
    collected_by: str = ""
    control_ref: Optional[str] = None
    finding_ref: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Evidence":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Control:
    """
    An individual IT control to be tested during an audit.

    Controls are the atomic unit of audit testing. Each control has a
    defined test procedure and expected evidence, and receives an
    assessment status after testing.

    Attributes:
        control_id: Unique control identifier (e.g., AC-001)
        title: Brief control title
        description: Full description of the control objective
        test_procedure: Step-by-step procedure for testing this control
        expected_evidence: Description of evidence that should be collected
        framework_mapping: Mapping to industry framework references
        risk_weight: Relative importance weight (1-5) for scoring
        status: Current assessment status of this control
        auditor_notes: Notes recorded by the auditor during testing
        evidence_refs: List of evidence IDs linked to this control
        tested_date: Date this control was tested
        tested_by: Auditor who performed the testing
    """
    control_id: str = ""
    title: str = ""
    description: str = ""
    test_procedure: str = ""
    expected_evidence: str = ""
    framework_mapping: dict = field(default_factory=dict)
    risk_weight: int = 3
    status: str = ControlStatus.NOT_TESTED.value
    auditor_notes: str = ""
    evidence_refs: list = field(default_factory=list)
    tested_date: Optional[str] = None
    tested_by: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Control":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Finding:
    """
    An audit finding documenting a control deficiency or observation.

    Findings are the primary output of audit fieldwork. Each finding
    includes a description of the issue, its risk impact, root cause
    analysis, and recommended remediation.

    Attributes:
        finding_id: Unique finding identifier
        title: Brief descriptive title
        audit_area: The audit domain this finding relates to
        severity: Severity classification (critical/high/medium/low/informational)
        description: Detailed description of the finding
        root_cause: Identified root cause of the deficiency
        business_impact: Description of the business impact
        recommendation: Recommended remediation action
        management_response: Management's response to the finding
        remediation_deadline: Target date for remediation
        risk_rating: Quantitative risk rating (optional)
        related_controls: List of control IDs related to this finding
        evidence_refs: List of evidence IDs supporting this finding
        status: Current status (open, in_progress, remediated, closed, accepted)
        identified_date: Date the finding was identified
        identified_by: Auditor who identified the finding
    """
    finding_id: str = field(default_factory=lambda: f"FND-{str(uuid.uuid4())[:6].upper()}")
    title: str = ""
    audit_area: str = ""
    severity: str = FindingSeverity.MEDIUM.value
    description: str = ""
    root_cause: str = ""
    business_impact: str = ""
    recommendation: str = ""
    management_response: str = ""
    remediation_deadline: Optional[str] = None
    risk_rating: Optional[dict] = None
    related_controls: list = field(default_factory=list)
    evidence_refs: list = field(default_factory=list)
    status: str = "open"
    identified_date: str = field(default_factory=lambda: date.today().isoformat())
    identified_by: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Finding":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AuditArea:
    """
    A domain or category within an audit engagement.

    Audit areas group related controls and findings. Standard areas
    include Access Control, Change Management, Incident Response,
    Data Backup, Network Security, and Compliance.

    Attributes:
        name: Name of the audit area (e.g., "Access Control")
        description: Description of what this area covers
        controls: List of controls tested in this area
        findings: List of findings identified in this area
        compliance_pct: Calculated compliance percentage (0-100)
        risk_score: Aggregated risk score for this area
        status: Overall status of this audit area
        auditor_assigned: Auditor responsible for this area
        start_date: Date fieldwork began for this area
        completion_date: Date fieldwork was completed for this area
        notes: General notes about this audit area
    """
    name: str = ""
    description: str = ""
    controls: list = field(default_factory=list)
    findings: list = field(default_factory=list)
    compliance_pct: float = 0.0
    risk_score: float = 0.0
    status: str = "not_started"
    auditor_assigned: str = ""
    start_date: Optional[str] = None
    completion_date: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "AuditArea":
        area = cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            compliance_pct=data.get("compliance_pct", 0.0),
            risk_score=data.get("risk_score", 0.0),
            status=data.get("status", "not_started"),
            auditor_assigned=data.get("auditor_assigned", ""),
            start_date=data.get("start_date"),
            completion_date=data.get("completion_date"),
            notes=data.get("notes", ""),
        )
        area.controls = [
            Control.from_dict(c) if isinstance(c, dict) else c
            for c in data.get("controls", [])
        ]
        area.findings = [
            Finding.from_dict(f) if isinstance(f, dict) else f
            for f in data.get("findings", [])
        ]
        return area


@dataclass
class AuditEngagement:
    """
    Top-level entity representing a complete audit engagement.

    An engagement encompasses the full audit lifecycle from planning
    through follow-up. It contains all audit areas, findings, evidence,
    and metadata for the engagement.

    Attributes:
        engagement_id: Unique engagement identifier
        name: Descriptive name for the engagement
        client: Name of the client organization being audited
        lead_auditor: Name and credentials of the lead auditor
        audit_team: List of audit team member names
        status: Current engagement lifecycle status
        audit_areas: List of audit areas included in scope
        evidence_inventory: Master list of all evidence collected
        scope_description: Description of the audit scope
        objectives: List of audit objectives
        methodology: Description of the audit methodology employed
        start_date: Engagement start date
        end_date: Engagement end date (planned or actual)
        report_date: Date the audit report was issued
        created_at: Timestamp when this engagement was created
        updated_at: Timestamp of the last update
        overall_risk_score: Aggregated risk score across all areas
        overall_compliance_pct: Overall compliance percentage
        executive_summary: Executive summary text for reporting
        notes: General engagement notes
    """
    engagement_id: str = field(default_factory=lambda: f"ENG-{str(uuid.uuid4())[:8].upper()}")
    name: str = ""
    client: str = ""
    lead_auditor: str = ""
    audit_team: list = field(default_factory=list)
    status: str = EngagementStatus.PLANNING.value
    audit_areas: list = field(default_factory=list)
    evidence_inventory: list = field(default_factory=list)
    scope_description: str = ""
    objectives: list = field(default_factory=list)
    methodology: str = "Risk-based audit approach aligned with ISACA IT Audit Framework"
    start_date: str = field(default_factory=lambda: date.today().isoformat())
    end_date: Optional[str] = None
    report_date: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    overall_risk_score: float = 0.0
    overall_compliance_pct: float = 0.0
    executive_summary: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        """Serialize the full engagement to a dictionary."""
        data = {
            "engagement_id": self.engagement_id,
            "name": self.name,
            "client": self.client,
            "lead_auditor": self.lead_auditor,
            "audit_team": self.audit_team,
            "status": self.status,
            "scope_description": self.scope_description,
            "objectives": self.objectives,
            "methodology": self.methodology,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "report_date": self.report_date,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "overall_risk_score": self.overall_risk_score,
            "overall_compliance_pct": self.overall_compliance_pct,
            "executive_summary": self.executive_summary,
            "notes": self.notes,
            "audit_areas": [
                a.to_dict() if hasattr(a, "to_dict") else a
                for a in self.audit_areas
            ],
            "evidence_inventory": [
                e.to_dict() if hasattr(e, "to_dict") else e
                for e in self.evidence_inventory
            ],
        }
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEngagement":
        """Deserialize an engagement from a dictionary."""
        eng = cls(
            engagement_id=data.get("engagement_id", ""),
            name=data.get("name", ""),
            client=data.get("client", ""),
            lead_auditor=data.get("lead_auditor", ""),
            audit_team=data.get("audit_team", []),
            status=data.get("status", EngagementStatus.PLANNING.value),
            scope_description=data.get("scope_description", ""),
            objectives=data.get("objectives", []),
            methodology=data.get("methodology", ""),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date"),
            report_date=data.get("report_date"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            overall_risk_score=data.get("overall_risk_score", 0.0),
            overall_compliance_pct=data.get("overall_compliance_pct", 0.0),
            executive_summary=data.get("executive_summary", ""),
            notes=data.get("notes", ""),
        )
        eng.audit_areas = [
            AuditArea.from_dict(a) if isinstance(a, dict) else a
            for a in data.get("audit_areas", [])
        ]
        eng.evidence_inventory = [
            Evidence.from_dict(e) if isinstance(e, dict) else e
            for e in data.get("evidence_inventory", [])
        ]
        return eng

    def save(self, filepath: str) -> None:
        """Persist the engagement to a JSON file."""
        self.updated_at = datetime.now().isoformat()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    @classmethod
    def load(cls, filepath: str) -> "AuditEngagement":
        """Load an engagement from a JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def get_area(self, name: str) -> Optional[AuditArea]:
        """Retrieve an audit area by name (case-insensitive)."""
        for area in self.audit_areas:
            area_name = area.name if hasattr(area, "name") else area.get("name", "")
            if area_name.lower() == name.lower():
                return area
        return None

    def get_all_findings(self) -> list:
        """Collect all findings across all audit areas."""
        findings = []
        for area in self.audit_areas:
            area_findings = area.findings if hasattr(area, "findings") else area.get("findings", [])
            findings.extend(area_findings)
        return findings

    def get_all_controls(self) -> list:
        """Collect all controls across all audit areas."""
        controls = []
        for area in self.audit_areas:
            area_controls = area.controls if hasattr(area, "controls") else area.get("controls", [])
            controls.extend(area_controls)
        return controls
