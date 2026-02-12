"""
Digital Evidence Tracker
=========================

Manages digital evidence collection, chain-of-custody documentation,
integrity verification, and evidence lifecycle tracking. Follows
digital forensics best practices for evidence handling.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib
import json

from src.models import Evidence, EvidenceType


class EvidenceTracker:
    """
    Tracks digital evidence with full chain-of-custody metadata.

    Provides methods for evidence registration, custody transfers,
    integrity verification, and audit trail generation.
    """

    def __init__(self):
        self.evidence_store: Dict[str, Evidence] = {}
        self.audit_log: List[Dict[str, Any]] = []

    def register_evidence(
        self,
        evidence_type: str,
        description: str,
        collected_by: str,
        source_system: str,
        file_path: Optional[str] = None,
        file_hash_md5: Optional[str] = None,
        file_hash_sha256: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        is_volatile: bool = False,
        preservation_method: str = "",
        tool_used: str = "",
        tags: Optional[List[str]] = None,
        notes: str = "",
    ) -> Evidence:
        """
        Register a new piece of evidence in the tracker.

        Args:
            evidence_type: Type classification (see EvidenceType enum).
            description: Description of the evidence item.
            collected_by: Name/ID of the collecting analyst.
            source_system: System the evidence was collected from.
            file_path: Storage path of the evidence file.
            file_hash_md5: MD5 hash for integrity verification.
            file_hash_sha256: SHA-256 hash for integrity verification.
            file_size_bytes: File size in bytes.
            is_volatile: Whether the evidence is volatile.
            preservation_method: Method used to preserve the evidence.
            tool_used: Forensic tool used for collection.
            tags: Categorization tags.
            notes: Analyst notes.

        Returns:
            The registered Evidence object with assigned ID.
        """
        evidence = Evidence(
            evidence_type=EvidenceType(evidence_type),
            description=description,
            collected_by=collected_by,
            source_system=source_system,
            file_path=file_path,
            file_hash_md5=file_hash_md5,
            file_hash_sha256=file_hash_sha256,
            file_size_bytes=file_size_bytes,
            is_volatile=is_volatile,
            preservation_method=preservation_method,
            tool_used=tool_used,
            tags=tags or [],
            notes=notes,
            integrity_verified=bool(file_hash_sha256 or file_hash_md5),
        )

        # Initial chain of custody entry
        evidence.chain_of_custody.append({
            "timestamp": evidence.collected_at.isoformat(),
            "action": "collected",
            "person": collected_by,
            "details": f"Evidence collected from {source_system} using {tool_used or 'manual collection'}",
        })

        self.evidence_store[evidence.evidence_id] = evidence
        self._log_action(evidence.evidence_id, "registered", collected_by,
                         f"New evidence registered: {description[:80]}")

        return evidence

    def transfer_custody(
        self,
        evidence_id: str,
        from_person: str,
        to_person: str,
        reason: str,
    ) -> bool:
        """
        Record a chain-of-custody transfer.

        Args:
            evidence_id: ID of the evidence being transferred.
            from_person: Current custodian.
            to_person: New custodian.
            reason: Reason for the transfer.

        Returns:
            True if transfer was recorded successfully.
        """
        evidence = self.evidence_store.get(evidence_id)
        if not evidence:
            return False

        evidence.chain_of_custody.append({
            "timestamp": datetime.now().isoformat(),
            "action": "transferred",
            "from": from_person,
            "to": to_person,
            "reason": reason,
        })

        self._log_action(evidence_id, "custody_transfer", from_person,
                         f"Custody transferred to {to_person}: {reason}")
        return True

    def verify_integrity(self, evidence_id: str, current_hash: str,
                         hash_type: str = "sha256") -> Dict[str, Any]:
        """
        Verify evidence integrity by comparing hashes.

        Args:
            evidence_id: ID of the evidence to verify.
            current_hash: Current hash of the evidence file.
            hash_type: Hash algorithm used (md5 or sha256).

        Returns:
            Verification result dictionary.
        """
        evidence = self.evidence_store.get(evidence_id)
        if not evidence:
            return {"verified": False, "error": "Evidence not found"}

        if hash_type == "sha256":
            original_hash = evidence.file_hash_sha256
        elif hash_type == "md5":
            original_hash = evidence.file_hash_md5
        else:
            return {"verified": False, "error": f"Unsupported hash type: {hash_type}"}

        if not original_hash:
            return {"verified": False, "error": f"No {hash_type} hash on record"}

        match = current_hash.lower() == original_hash.lower()
        evidence.integrity_verified = match

        result = {
            "verified": match,
            "evidence_id": evidence_id,
            "hash_type": hash_type,
            "original_hash": original_hash,
            "current_hash": current_hash,
            "timestamp": datetime.now().isoformat(),
        }

        self._log_action(evidence_id, "integrity_check",
                         "system", f"Integrity {'PASSED' if match else 'FAILED'} ({hash_type})")

        return result

    def add_note(self, evidence_id: str, analyst: str, note: str) -> bool:
        """Add an analyst note to an evidence item."""
        evidence = self.evidence_store.get(evidence_id)
        if not evidence:
            return False

        timestamp = datetime.now().isoformat()
        if evidence.notes:
            evidence.notes += f"\n[{timestamp}] {analyst}: {note}"
        else:
            evidence.notes = f"[{timestamp}] {analyst}: {note}"

        self._log_action(evidence_id, "note_added", analyst, note[:100])
        return True

    def tag_evidence(self, evidence_id: str, tags: List[str]) -> bool:
        """Add tags to an evidence item."""
        evidence = self.evidence_store.get(evidence_id)
        if not evidence:
            return False

        evidence.tags.extend(tags)
        evidence.tags = list(set(evidence.tags))  # Deduplicate
        self._log_action(evidence_id, "tagged", "system", f"Tags added: {', '.join(tags)}")
        return True

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Retrieve an evidence item by ID."""
        return self.evidence_store.get(evidence_id)

    def get_all_evidence(self) -> List[Evidence]:
        """Return all registered evidence items."""
        return list(self.evidence_store.values())

    def get_evidence_by_type(self, evidence_type: str) -> List[Evidence]:
        """Filter evidence by type."""
        return [
            e for e in self.evidence_store.values()
            if e.evidence_type.value == evidence_type
        ]

    def get_evidence_by_source(self, source_system: str) -> List[Evidence]:
        """Filter evidence by source system."""
        return [
            e for e in self.evidence_store.values()
            if source_system.lower() in e.source_system.lower()
        ]

    def get_volatile_evidence(self) -> List[Evidence]:
        """Return all volatile evidence items (should be collected first)."""
        return [e for e in self.evidence_store.values() if e.is_volatile]

    def get_chain_of_custody_report(self, evidence_id: str) -> Optional[str]:
        """Generate a formatted chain-of-custody report for an evidence item."""
        evidence = self.evidence_store.get(evidence_id)
        if not evidence:
            return None

        lines = [
            "CHAIN OF CUSTODY REPORT",
            "=" * 60,
            f"Evidence ID:   {evidence.evidence_id}",
            f"Type:          {evidence.evidence_type.value}",
            f"Description:   {evidence.description}",
            f"Source System:  {evidence.source_system}",
            f"Collected By:  {evidence.collected_by}",
            f"Collected At:  {evidence.collected_at.isoformat()}",
            f"File Path:     {evidence.file_path or 'N/A'}",
            f"MD5 Hash:      {evidence.file_hash_md5 or 'N/A'}",
            f"SHA-256 Hash:  {evidence.file_hash_sha256 or 'N/A'}",
            f"File Size:     {evidence.file_size_bytes or 'N/A'} bytes",
            f"Volatile:      {'Yes' if evidence.is_volatile else 'No'}",
            f"Preservation:  {evidence.preservation_method or 'N/A'}",
            f"Tool Used:     {evidence.tool_used or 'N/A'}",
            f"Integrity:     {'Verified' if evidence.integrity_verified else 'Not Verified'}",
            f"Tags:          {', '.join(evidence.tags) if evidence.tags else 'None'}",
            "",
            "CUSTODY CHAIN:",
            "-" * 60,
        ]

        for entry in evidence.chain_of_custody:
            lines.append(f"  [{entry.get('timestamp', 'N/A')}]")
            lines.append(f"    Action: {entry.get('action', 'N/A')}")
            if 'person' in entry:
                lines.append(f"    Person: {entry['person']}")
            if 'from' in entry:
                lines.append(f"    From: {entry['from']} -> To: {entry['to']}")
            if 'reason' in entry:
                lines.append(f"    Reason: {entry['reason']}")
            if 'details' in entry:
                lines.append(f"    Details: {entry['details']}")
            lines.append("")

        if evidence.notes:
            lines.extend([
                "ANALYST NOTES:",
                "-" * 60,
                evidence.notes,
            ])

        return "\n".join(lines)

    def generate_evidence_summary(self) -> Dict[str, Any]:
        """Generate a summary of all evidence in the tracker."""
        evidence_list = self.get_all_evidence()
        if not evidence_list:
            return {"total": 0, "by_type": {}, "by_source": {}, "volatile_count": 0}

        by_type: Dict[str, int] = {}
        by_source: Dict[str, int] = {}
        volatile_count = 0
        verified_count = 0

        for e in evidence_list:
            etype = e.evidence_type.value
            by_type[etype] = by_type.get(etype, 0) + 1
            by_source[e.source_system] = by_source.get(e.source_system, 0) + 1
            if e.is_volatile:
                volatile_count += 1
            if e.integrity_verified:
                verified_count += 1

        return {
            "total": len(evidence_list),
            "by_type": by_type,
            "by_source": by_source,
            "volatile_count": volatile_count,
            "verified_count": verified_count,
            "integrity_rate": round(verified_count / len(evidence_list) * 100, 1),
        }

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Return the complete audit log of all evidence actions."""
        return self.audit_log.copy()

    def export_evidence_manifest(self) -> str:
        """Export evidence manifest as JSON string for case documentation."""
        manifest = {
            "export_timestamp": datetime.now().isoformat(),
            "evidence_count": len(self.evidence_store),
            "evidence_items": [e.to_dict() for e in self.evidence_store.values()],
            "summary": self.generate_evidence_summary(),
        }
        return json.dumps(manifest, indent=2, default=str)

    def _log_action(self, evidence_id: str, action: str, actor: str, details: str) -> None:
        """Record an action in the internal audit log."""
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "evidence_id": evidence_id,
            "action": action,
            "actor": actor,
            "details": details,
        })

    @staticmethod
    def compute_file_hash(file_path: str, algorithm: str = "sha256") -> str:
        """
        Compute the hash of a file for integrity verification.

        Args:
            file_path: Path to the file.
            algorithm: Hash algorithm (md5, sha256).

        Returns:
            Hex digest of the file hash.
        """
        hash_func = hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    @staticmethod
    def get_collection_order_guidance() -> List[Dict[str, str]]:
        """
        Return evidence collection priority order based on volatility.

        Follows the RFC 3227 order of volatility for digital evidence.
        """
        return [
            {
                "priority": "1 (Highest)",
                "type": "CPU Registers & Cache",
                "volatility": "Nanoseconds",
                "method": "Specialized hardware/software capture",
            },
            {
                "priority": "2",
                "type": "System Memory (RAM)",
                "volatility": "Seconds to minutes",
                "method": "Memory dump tools (WinPmem, LiME, Volatility)",
            },
            {
                "priority": "3",
                "type": "Network Connections & State",
                "volatility": "Seconds to minutes",
                "method": "netstat, ss, network captures (tcpdump, Wireshark)",
            },
            {
                "priority": "4",
                "type": "Running Processes",
                "volatility": "Minutes",
                "method": "Process listing tools (ps, tasklist, Process Explorer)",
            },
            {
                "priority": "5",
                "type": "Disk / File System",
                "volatility": "Hours to days",
                "method": "Disk imaging (dd, FTK Imager, EnCase)",
            },
            {
                "priority": "6",
                "type": "Log Files",
                "volatility": "Days to weeks (may rotate)",
                "method": "Log collection and preservation, SIEM export",
            },
            {
                "priority": "7",
                "type": "Archived Data & Backups",
                "volatility": "Months to years",
                "method": "Backup retrieval, archive access",
            },
            {
                "priority": "8 (Lowest)",
                "type": "Physical Evidence",
                "volatility": "Stable",
                "method": "Physical seizure with chain-of-custody documentation",
            },
        ]
