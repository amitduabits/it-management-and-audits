"""
Audit Engine - Core execution engine for running IT audit checklists.

Provides functionality to:
- Load and validate audit checklists
- Iterate through controls interactively, recording responses
- Collect evidence references during control testing
- Persist audit state to JSON for continuity across sessions
- Track audit area progress and completion status
"""

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from src.models import (
    AuditEngagement,
    AuditArea,
    Control,
    Evidence,
    Finding,
    ControlStatus,
    EngagementStatus,
)


# Directory containing the built-in checklists
CHECKLISTS_DIR = Path(__file__).parent / "checklists"

# Map of checklist names to filenames
AVAILABLE_CHECKLISTS = {
    "access_control": "access_control.json",
    "change_management": "change_management.json",
    "incident_response": "incident_response.json",
    "data_backup": "data_backup.json",
    "network_security": "network_security.json",
    "compliance": "compliance.json",
}

# Friendly display names for each checklist domain
CHECKLIST_DISPLAY_NAMES = {
    "access_control": "Access Control",
    "change_management": "Change Management",
    "incident_response": "Incident Response",
    "data_backup": "Data Backup and Recovery",
    "network_security": "Network Security",
    "compliance": "Regulatory Compliance",
}


class AuditEngine:
    """
    Core engine for managing and executing audit engagements.

    The AuditEngine handles the lifecycle of an audit engagement including
    creating new engagements, loading and running checklists, recording
    control assessment results, and managing findings and evidence.
    """

    def __init__(self, engagement: Optional[AuditEngagement] = None):
        """
        Initialize the audit engine.

        Args:
            engagement: An existing AuditEngagement to work with, or None
                       to create a new one later.
        """
        self.engagement = engagement

    @staticmethod
    def list_available_checklists() -> dict:
        """
        Return a dictionary of available checklist names and their descriptions.

        Returns:
            Dict mapping checklist keys to display names.
        """
        available = {}
        for key, filename in AVAILABLE_CHECKLISTS.items():
            filepath = CHECKLISTS_DIR / filename
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                available[key] = {
                    "display_name": data.get("domain", CHECKLIST_DISPLAY_NAMES.get(key, key)),
                    "description": data.get("description", ""),
                    "control_count": len(data.get("controls", [])),
                    "version": data.get("version", "1.0"),
                    "framework_references": data.get("framework_references", []),
                }
        return available

    @staticmethod
    def load_checklist(checklist_name: str) -> dict:
        """
        Load a checklist by name from the checklists directory.

        Args:
            checklist_name: Key name of the checklist (e.g., 'access_control').

        Returns:
            Parsed checklist data as a dictionary.

        Raises:
            FileNotFoundError: If the checklist file does not exist.
            ValueError: If the checklist name is not recognized.
        """
        if checklist_name not in AVAILABLE_CHECKLISTS:
            raise ValueError(
                f"Unknown checklist: '{checklist_name}'. "
                f"Available checklists: {', '.join(AVAILABLE_CHECKLISTS.keys())}"
            )

        filepath = CHECKLISTS_DIR / AVAILABLE_CHECKLISTS[checklist_name]
        if not filepath.exists():
            raise FileNotFoundError(f"Checklist file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def create_engagement(
        self,
        name: str,
        client: str,
        lead_auditor: str,
        scope_description: str = "",
        objectives: Optional[list] = None,
        audit_team: Optional[list] = None,
    ) -> AuditEngagement:
        """
        Create a new audit engagement.

        Args:
            name: Descriptive name for the engagement.
            client: Name of the client organization.
            lead_auditor: Name and credentials of the lead auditor.
            scope_description: Description of the audit scope.
            objectives: List of audit objectives.
            audit_team: List of audit team members.

        Returns:
            The newly created AuditEngagement.
        """
        self.engagement = AuditEngagement(
            name=name,
            client=client,
            lead_auditor=lead_auditor,
            scope_description=scope_description,
            objectives=objectives or [
                "Evaluate the design and operating effectiveness of IT controls",
                "Identify control deficiencies and areas of risk",
                "Assess compliance with applicable regulatory requirements",
                "Provide recommendations for control improvements",
            ],
            audit_team=audit_team or [lead_auditor],
            status=EngagementStatus.PLANNING.value,
        )
        return self.engagement

    def initialize_audit_area(self, checklist_name: str) -> AuditArea:
        """
        Initialize an audit area by loading a checklist and creating
        Control objects for each item.

        Args:
            checklist_name: Key name of the checklist to load.

        Returns:
            The initialized AuditArea with controls ready for testing.

        Raises:
            RuntimeError: If no engagement is loaded.
        """
        if self.engagement is None:
            raise RuntimeError("No engagement loaded. Create or load an engagement first.")

        checklist_data = self.load_checklist(checklist_name)
        domain_name = checklist_data.get("domain", CHECKLIST_DISPLAY_NAMES.get(checklist_name, checklist_name))

        # Check if this area already exists in the engagement
        existing_area = self.engagement.get_area(domain_name)
        if existing_area is not None:
            return existing_area

        # Create Control objects from the checklist
        controls = []
        for ctrl_data in checklist_data.get("controls", []):
            control = Control(
                control_id=ctrl_data["id"],
                title=ctrl_data["title"],
                description=ctrl_data["description"],
                test_procedure=ctrl_data.get("test_procedure", ""),
                expected_evidence=ctrl_data.get("expected_evidence", ""),
                framework_mapping=ctrl_data.get("framework_mapping", {}),
                risk_weight=ctrl_data.get("risk_weight", 3),
                status=ControlStatus.NOT_TESTED.value,
            )
            controls.append(control)

        # Create the audit area
        area = AuditArea(
            name=domain_name,
            description=checklist_data.get("description", ""),
            controls=controls,
            status="in_progress",
            start_date=date.today().isoformat(),
        )

        self.engagement.audit_areas.append(area)
        self.engagement.status = EngagementStatus.FIELDWORK.value
        return area

    def assess_control(
        self,
        area_name: str,
        control_id: str,
        status: str,
        auditor_notes: str = "",
        tested_by: str = "",
        evidence_refs: Optional[list] = None,
    ) -> Control:
        """
        Record the assessment result for a specific control.

        Args:
            area_name: Name of the audit area containing the control.
            control_id: ID of the control to assess.
            status: Assessment status (effective, partially_effective,
                    ineffective, not_applicable).
            auditor_notes: Notes recorded by the auditor.
            tested_by: Name of the auditor who performed testing.
            evidence_refs: List of evidence reference IDs.

        Returns:
            The updated Control object.

        Raises:
            ValueError: If the area or control is not found.
        """
        if self.engagement is None:
            raise RuntimeError("No engagement loaded.")

        area = self.engagement.get_area(area_name)
        if area is None:
            raise ValueError(f"Audit area not found: '{area_name}'")

        # Find the control
        target_control = None
        controls = area.controls if hasattr(area, "controls") else area.get("controls", [])
        for ctrl in controls:
            ctrl_id = ctrl.control_id if hasattr(ctrl, "control_id") else ctrl.get("control_id", "")
            if ctrl_id == control_id:
                target_control = ctrl
                break

        if target_control is None:
            raise ValueError(f"Control not found: '{control_id}' in area '{area_name}'")

        # Update the control
        if hasattr(target_control, "status"):
            target_control.status = status
            target_control.auditor_notes = auditor_notes
            target_control.tested_by = tested_by or self.engagement.lead_auditor
            target_control.tested_date = date.today().isoformat()
            target_control.evidence_refs = evidence_refs or []
        else:
            target_control["status"] = status
            target_control["auditor_notes"] = auditor_notes
            target_control["tested_by"] = tested_by or self.engagement.lead_auditor
            target_control["tested_date"] = date.today().isoformat()
            target_control["evidence_refs"] = evidence_refs or []

        return target_control

    def add_evidence(
        self,
        title: str,
        evidence_type: str,
        description: str,
        source: str,
        collected_by: str = "",
        file_reference: str = "",
        control_ref: Optional[str] = None,
        finding_ref: Optional[str] = None,
        notes: str = "",
    ) -> Evidence:
        """
        Add an evidence item to the engagement's evidence inventory.

        Args:
            title: Brief descriptive title for the evidence.
            evidence_type: Type classification (document, screenshot, etc.).
            description: Detailed description of the evidence.
            source: Where the evidence was obtained.
            collected_by: Name of the collecting auditor.
            file_reference: Path or reference to the evidence file.
            control_ref: Related control ID.
            finding_ref: Related finding ID.
            notes: Additional notes.

        Returns:
            The created Evidence object.
        """
        if self.engagement is None:
            raise RuntimeError("No engagement loaded.")

        evidence = Evidence(
            title=title,
            evidence_type=evidence_type,
            description=description,
            source=source,
            collected_by=collected_by or self.engagement.lead_auditor,
            file_reference=file_reference,
            control_ref=control_ref,
            finding_ref=finding_ref,
            notes=notes,
        )

        self.engagement.evidence_inventory.append(evidence)
        return evidence

    def add_finding(
        self,
        title: str,
        audit_area: str,
        severity: str,
        description: str,
        root_cause: str = "",
        business_impact: str = "",
        recommendation: str = "",
        related_controls: Optional[list] = None,
        identified_by: str = "",
    ) -> Finding:
        """
        Record an audit finding and associate it with an audit area.

        Args:
            title: Brief descriptive title of the finding.
            audit_area: Name of the audit area this finding relates to.
            severity: Severity classification (critical, high, medium, low, informational).
            description: Detailed description of the finding.
            root_cause: Identified root cause.
            business_impact: Description of business impact.
            recommendation: Recommended remediation.
            related_controls: List of related control IDs.
            identified_by: Name of the identifying auditor.

        Returns:
            The created Finding object.

        Raises:
            ValueError: If the specified audit area is not found.
        """
        if self.engagement is None:
            raise RuntimeError("No engagement loaded.")

        finding = Finding(
            title=title,
            audit_area=audit_area,
            severity=severity,
            description=description,
            root_cause=root_cause,
            business_impact=business_impact,
            recommendation=recommendation,
            related_controls=related_controls or [],
            identified_by=identified_by or self.engagement.lead_auditor,
        )

        # Add finding to the appropriate audit area
        area = self.engagement.get_area(audit_area)
        if area is not None:
            if hasattr(area, "findings"):
                area.findings.append(finding)
            else:
                area["findings"].append(finding.to_dict())
        else:
            # If the area does not exist yet, create a minimal one
            new_area = AuditArea(
                name=audit_area,
                findings=[finding],
            )
            self.engagement.audit_areas.append(new_area)

        return finding

    def get_area_progress(self, area_name: str) -> dict:
        """
        Calculate testing progress for a specific audit area.

        Args:
            area_name: Name of the audit area.

        Returns:
            Dictionary with progress metrics.
        """
        if self.engagement is None:
            raise RuntimeError("No engagement loaded.")

        area = self.engagement.get_area(area_name)
        if area is None:
            raise ValueError(f"Audit area not found: '{area_name}'")

        controls = area.controls if hasattr(area, "controls") else area.get("controls", [])
        total = len(controls)
        if total == 0:
            return {
                "total_controls": 0,
                "tested": 0,
                "not_tested": 0,
                "effective": 0,
                "partially_effective": 0,
                "ineffective": 0,
                "not_applicable": 0,
                "completion_pct": 0.0,
            }

        counts = {
            "effective": 0,
            "partially_effective": 0,
            "ineffective": 0,
            "not_applicable": 0,
            "not_tested": 0,
        }

        for ctrl in controls:
            status = ctrl.status if hasattr(ctrl, "status") else ctrl.get("status", "not_tested")
            if status in counts:
                counts[status] += 1
            else:
                counts["not_tested"] += 1

        tested = total - counts["not_tested"]
        completion_pct = (tested / total * 100) if total > 0 else 0.0

        return {
            "total_controls": total,
            "tested": tested,
            "not_tested": counts["not_tested"],
            "effective": counts["effective"],
            "partially_effective": counts["partially_effective"],
            "ineffective": counts["ineffective"],
            "not_applicable": counts["not_applicable"],
            "completion_pct": round(completion_pct, 1),
        }

    def get_engagement_summary(self) -> dict:
        """
        Generate a high-level summary of the entire engagement.

        Returns:
            Dictionary with engagement-level summary metrics.
        """
        if self.engagement is None:
            raise RuntimeError("No engagement loaded.")

        all_findings = self.engagement.get_all_findings()
        all_controls = self.engagement.get_all_controls()

        # Count findings by severity
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "informational": 0,
        }
        for f in all_findings:
            sev = f.severity if hasattr(f, "severity") else f.get("severity", "medium")
            if sev in severity_counts:
                severity_counts[sev] += 1

        # Count controls by status
        control_counts = {
            "effective": 0,
            "partially_effective": 0,
            "ineffective": 0,
            "not_applicable": 0,
            "not_tested": 0,
        }
        for c in all_controls:
            status = c.status if hasattr(c, "status") else c.get("status", "not_tested")
            if status in control_counts:
                control_counts[status] += 1

        # Area summaries
        area_summaries = []
        for area in self.engagement.audit_areas:
            area_name = area.name if hasattr(area, "name") else area.get("name", "Unknown")
            progress = self.get_area_progress(area_name)
            area_summaries.append({
                "name": area_name,
                **progress,
            })

        return {
            "engagement_id": self.engagement.engagement_id,
            "name": self.engagement.name,
            "client": self.engagement.client,
            "status": self.engagement.status,
            "total_areas": len(self.engagement.audit_areas),
            "total_controls": len(all_controls),
            "total_findings": len(all_findings),
            "total_evidence": len(self.engagement.evidence_inventory),
            "findings_by_severity": severity_counts,
            "controls_by_status": control_counts,
            "area_summaries": area_summaries,
        }

    def run_checklist_interactive(self, checklist_name: str, auditor_name: str = "") -> AuditArea:
        """
        Run a checklist interactively, prompting the user for each control.

        This method initializes the audit area and then iterates through
        each control, displaying the control information and prompting
        the user for assessment status and notes.

        Args:
            checklist_name: Key name of the checklist to run.
            auditor_name: Name of the auditor performing the testing.

        Returns:
            The completed AuditArea with all assessment results.
        """
        area = self.initialize_audit_area(checklist_name)
        auditor = auditor_name or (self.engagement.lead_auditor if self.engagement else "Auditor")

        controls = area.controls if hasattr(area, "controls") else area.get("controls", [])

        status_options = {
            "1": ControlStatus.EFFECTIVE.value,
            "2": ControlStatus.PARTIALLY_EFFECTIVE.value,
            "3": ControlStatus.INEFFECTIVE.value,
            "4": ControlStatus.NOT_APPLICABLE.value,
            "5": ControlStatus.NOT_TESTED.value,
        }

        for i, ctrl in enumerate(controls, 1):
            ctrl_id = ctrl.control_id if hasattr(ctrl, "control_id") else ctrl.get("control_id", "")
            ctrl_title = ctrl.title if hasattr(ctrl, "title") else ctrl.get("title", "")
            ctrl_desc = ctrl.description if hasattr(ctrl, "description") else ctrl.get("description", "")
            ctrl_proc = ctrl.test_procedure if hasattr(ctrl, "test_procedure") else ctrl.get("test_procedure", "")
            ctrl_evidence = ctrl.expected_evidence if hasattr(ctrl, "expected_evidence") else ctrl.get("expected_evidence", "")

            print(f"\n{'='*70}")
            print(f"  Control {i}/{len(controls)}: [{ctrl_id}] {ctrl_title}")
            print(f"{'='*70}")
            print(f"\n  Description:")
            print(f"  {ctrl_desc}")
            print(f"\n  Test Procedure:")
            print(f"  {ctrl_proc}")
            print(f"\n  Expected Evidence:")
            print(f"  {ctrl_evidence}")
            print(f"\n  Assessment Status:")
            print(f"    1 = Effective")
            print(f"    2 = Partially Effective")
            print(f"    3 = Ineffective")
            print(f"    4 = Not Applicable")
            print(f"    5 = Not Tested (skip)")

            while True:
                choice = input(f"\n  Enter status [1-5]: ").strip()
                if choice in status_options:
                    break
                print("  Invalid choice. Please enter 1-5.")

            status = status_options[choice]

            notes = ""
            if status != ControlStatus.NOT_TESTED.value:
                notes = input("  Auditor notes (press Enter to skip): ").strip()

            evidence_ref = ""
            if status in (ControlStatus.EFFECTIVE.value, ControlStatus.PARTIALLY_EFFECTIVE.value, ControlStatus.INEFFECTIVE.value):
                evidence_ref = input("  Evidence reference (press Enter to skip): ").strip()

            area_name = area.name if hasattr(area, "name") else area.get("name", "")
            self.assess_control(
                area_name=area_name,
                control_id=ctrl_id,
                status=status,
                auditor_notes=notes,
                tested_by=auditor,
                evidence_refs=[evidence_ref] if evidence_ref else [],
            )

            # If evidence reference was provided, add to inventory
            if evidence_ref:
                self.add_evidence(
                    title=f"Evidence for {ctrl_id}: {ctrl_title}",
                    evidence_type="document",
                    description=f"Evidence collected during testing of control {ctrl_id}",
                    source=evidence_ref,
                    collected_by=auditor,
                    file_reference=evidence_ref,
                    control_ref=ctrl_id,
                )

        # Mark area as completed
        if hasattr(area, "completion_date"):
            area.completion_date = date.today().isoformat()
            area.status = "completed"
        else:
            area["completion_date"] = date.today().isoformat()
            area["status"] = "completed"

        return area

    def save_engagement(self, filepath: str) -> None:
        """
        Save the current engagement state to a JSON file.

        Args:
            filepath: Path to save the engagement JSON.
        """
        if self.engagement is None:
            raise RuntimeError("No engagement loaded.")

        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        self.engagement.save(filepath)

    def load_engagement(self, filepath: str) -> AuditEngagement:
        """
        Load an engagement from a JSON file.

        Args:
            filepath: Path to the engagement JSON file.

        Returns:
            The loaded AuditEngagement.
        """
        self.engagement = AuditEngagement.load(filepath)
        return self.engagement
