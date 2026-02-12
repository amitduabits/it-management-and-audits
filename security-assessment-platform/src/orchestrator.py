"""
Assessment Orchestrator - Full security assessment pipeline.

Coordinates the entire assessment workflow:
    1. Configuration loading
    2. Network scanning
    3. Web application scanning
    4. DNS enumeration
    5. Compliance checking (ISO 27001, PCI-DSS, NIST CSF)
    6. Risk calculation
    7. Risk matrix generation
    8. Report generation (Executive, Technical, Roadmap)
    9. Results persistence

ETHICAL USE NOTICE:
    This orchestrator performs active scanning. Ensure you have explicit
    written authorization before running assessments.
"""

import os
import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Full assessment pipeline orchestrator.

    Coordinates all scanning, analysis, and reporting modules into a
    single automated workflow.

    Attributes:
        target: Primary scan target (IP/hostname).
        url: Web URL for web scanning (optional).
        domain: Domain for DNS scanning (optional).
        output_dir: Directory for reports and data.
        organization: Organization name for reports.

    Example:
        orchestrator = Orchestrator(
            target="192.168.1.1",
            url="https://example.com",
            domain="example.com",
            output_dir="./reports",
        )
        results = orchestrator.run()
    """

    def __init__(
        self,
        target: str,
        url: Optional[str] = None,
        domain: Optional[str] = None,
        output_dir: str = "./reports",
        organization: str = "Organization",
        port_range: tuple = (1, 1024),
        scan_threads: int = 50,
    ):
        """
        Initialize the Orchestrator.

        Args:
            target: Primary scan target (IP address or hostname).
            url: Optional URL for web scanning.
            domain: Optional domain for DNS scanning.
            output_dir: Output directory for reports and data.
            organization: Organization name for report branding.
            port_range: Port range for network scanning.
            scan_threads: Maximum threads for concurrent scanning.
        """
        self.target = target
        self.url = url
        self.domain = domain or target
        self.output_dir = output_dir
        self.organization = organization
        self.port_range = port_range
        self.scan_threads = scan_threads

        # Results storage
        self.network_results = {}
        self.web_results = {}
        self.dns_results = {}
        self.compliance_results = {}
        self.risk_results = {}
        self.risk_matrix_results = {}
        self.all_findings = []

        # Timing
        self.start_time = None
        self.end_time = None

    def run(self) -> Dict[str, Any]:
        """
        Execute the full assessment pipeline.

        Returns:
            Dictionary containing all assessment results.
        """
        self.start_time = time.time()
        logger.info(f"Starting full assessment for {self.target}")
        print(f"\n{'='*60}")
        print("  SECUREAUDIT PRO - Full Security Assessment")
        print(f"{'='*60}")
        print(f"  Target:       {self.target}")
        print(f"  Web URL:      {self.url or 'N/A'}")
        print(f"  Domain:       {self.domain}")
        print(f"  Output:       {self.output_dir}")
        print(f"  Started:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        os.makedirs(self.output_dir, exist_ok=True)

        # Phase 1: Scanning
        print("[Phase 1/4] Scanning...")
        self._run_network_scan()
        self._run_web_scan()
        self._run_dns_scan()
        self._aggregate_findings()

        # Phase 2: Compliance
        print("\n[Phase 2/4] Compliance Assessment...")
        self._run_compliance_checks()

        # Phase 3: Risk Assessment
        print("\n[Phase 3/4] Risk Calculation...")
        self._run_risk_assessment()

        # Phase 4: Reporting
        print("\n[Phase 4/4] Report Generation...")
        self._generate_reports()

        # Save raw data
        self._save_raw_data()

        self.end_time = time.time()
        duration = round(self.end_time - self.start_time, 2)

        print(f"\n{'='*60}")
        print("  Assessment Complete")
        print(f"{'='*60}")
        print(f"  Duration:     {duration}s")
        print(f"  Findings:     {len(self.all_findings)}")
        print(f"  Risk Score:   {self.risk_results.get('overall_risk_score', 'N/A')}/10")
        print(f"  Reports:      {self.output_dir}")
        print(f"{'='*60}\n")

        return self._compile_results()

    def _run_network_scan(self):
        """Execute network scan."""
        print(f"  [*] Network scan: {self.target} (ports {self.port_range[0]}-{self.port_range[1]})...")
        try:
            from src.scanner.network_scanner import NetworkScanner
            scanner = NetworkScanner(max_threads=self.scan_threads)
            result = scanner.scan(self.target, port_range=self.port_range)
            self.network_results = result.to_dict()
            print(f"      Found {len(result.open_ports)} open ports, {len(result.findings)} findings")
        except Exception as e:
            logger.error(f"Network scan failed: {e}")
            print(f"      [!] Network scan failed: {e}")

    def _run_web_scan(self):
        """Execute web application scan."""
        if not self.url:
            print("  [*] Web scan: Skipped (no URL provided)")
            return

        print(f"  [*] Web scan: {self.url}...")
        try:
            from src.scanner.web_scanner import WebScanner
            scanner = WebScanner()
            result = scanner.scan(self.url)
            self.web_results = result.to_dict()
            print(f"      Security score: {result.security_score}/100, {len(result.all_findings)} findings")
        except Exception as e:
            logger.error(f"Web scan failed: {e}")
            print(f"      [!] Web scan failed: {e}")

    def _run_dns_scan(self):
        """Execute DNS scan."""
        print(f"  [*] DNS scan: {self.domain}...")
        try:
            from src.scanner.dns_scanner import DNSScanner
            scanner = DNSScanner()
            result = scanner.scan(self.domain)
            self.dns_results = result.to_dict()
            record_count = sum(len(v) for v in result.records.values())
            print(f"      Found {record_count} records, {len(result.findings)} findings")
        except Exception as e:
            logger.error(f"DNS scan failed: {e}")
            print(f"      [!] DNS scan failed: {e}")

    def _aggregate_findings(self):
        """Aggregate all findings from scanners."""
        self.all_findings = []
        self.all_findings.extend(self.network_results.get("findings", []))
        self.all_findings.extend(self.web_results.get("all_findings", []))
        self.all_findings.extend(self.dns_results.get("findings", []))
        print(f"\n  [+] Total findings aggregated: {len(self.all_findings)}")

    def _run_compliance_checks(self):
        """Execute all compliance framework checks."""
        scan_data = {
            "network_scan": self.network_results,
            "web_scan": self.web_results,
            "dns_scan": self.dns_results,
        }

        try:
            from src.compliance.iso27001 import ISO27001Checker
            checker = ISO27001Checker()
            result = checker.assess(scan_data)
            self.compliance_results["iso27001"] = result.to_dict()
            print(f"  [+] ISO 27001: {result.overall_score * 100:.1f}%")
        except Exception as e:
            logger.error(f"ISO 27001 check failed: {e}")

        try:
            from src.compliance.pci_dss import PCIDSSChecker
            checker = PCIDSSChecker()
            result = checker.assess(scan_data)
            self.compliance_results["pci_dss"] = result.to_dict()
            print(f"  [+] PCI-DSS:   {result.overall_score * 100:.1f}%")
        except Exception as e:
            logger.error(f"PCI-DSS check failed: {e}")

        try:
            from src.compliance.nist_csf import NISTCSFChecker
            checker = NISTCSFChecker()
            result = checker.assess(scan_data)
            self.compliance_results["nist_csf"] = result.to_dict()
            print(f"  [+] NIST CSF:  {result.overall_score * 100:.1f}% (Tier {result.overall_tier})")
        except Exception as e:
            logger.error(f"NIST CSF check failed: {e}")

    def _run_risk_assessment(self):
        """Execute risk assessment."""
        try:
            from src.risk.risk_engine import RiskEngine
            from src.risk.risk_matrix import RiskMatrix

            scan_data = {
                "network_scan": self.network_results,
                "web_scan": self.web_results,
                "dns_scan": self.dns_results,
            }

            engine = RiskEngine()
            assessment = engine.calculate_risk(scan_data, self.compliance_results)
            self.risk_results = assessment.to_dict()

            print(f"  [+] Overall Risk: {assessment.overall_risk_score}/10 ({assessment.overall_risk_level.upper()})")
            for cat in assessment.categories:
                print(f"      {cat.display_name:<25} {cat.raw_score:>5}/10")

            # Generate risk matrix
            matrix = RiskMatrix()
            matrix_result = matrix.generate(scan_data, self.compliance_results)
            self.risk_matrix_results = matrix_result.to_dict()
            print(f"\n{matrix.render_terminal(matrix_result)}")

        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            print(f"  [!] Risk assessment failed: {e}")

    def _generate_reports(self):
        """Generate all report types."""
        try:
            from src.reporting.executive_report import ExecutiveReportGenerator
            gen = ExecutiveReportGenerator()
            html = gen.generate(
                risk_data=self.risk_results,
                compliance_data=self.compliance_results,
                organization=self.organization,
            )
            path = os.path.join(self.output_dir, "executive_summary.html")
            gen.save(html, path)
            print(f"  [+] Executive report:     {path}")
        except Exception as e:
            logger.error(f"Executive report failed: {e}")

        try:
            from src.reporting.technical_report import TechnicalReportGenerator
            gen = TechnicalReportGenerator()
            html = gen.generate(
                findings=self.all_findings,
                risk_data=self.risk_results,
                organization=self.organization,
            )
            path = os.path.join(self.output_dir, "technical_report.html")
            gen.save(html, path)
            print(f"  [+] Technical report:     {path}")
        except Exception as e:
            logger.error(f"Technical report failed: {e}")

        try:
            from src.reporting.remediation_roadmap import RemediationRoadmapGenerator
            gen = RemediationRoadmapGenerator()
            html = gen.generate(
                findings=self.all_findings,
                risk_data=self.risk_results,
                compliance_data=self.compliance_results,
                organization=self.organization,
            )
            path = os.path.join(self.output_dir, "remediation_roadmap.html")
            gen.save(html, path)
            print(f"  [+] Remediation roadmap:  {path}")
        except Exception as e:
            logger.error(f"Remediation roadmap failed: {e}")

    def _save_raw_data(self):
        """Save raw assessment data as JSON."""
        data = self._compile_results()
        path = os.path.join(self.output_dir, "assessment_data.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"  [+] Raw data:             {path}")

    def _compile_results(self) -> Dict[str, Any]:
        """Compile all results into a single dictionary."""
        return {
            "meta": {
                "target": self.target,
                "url": self.url,
                "domain": self.domain,
                "organization": self.organization,
                "assessment_date": datetime.now().isoformat(),
                "duration_seconds": (
                    round(self.end_time - self.start_time, 2)
                    if self.end_time else None
                ),
            },
            "network_scan": self.network_results,
            "web_scan": self.web_results,
            "dns_scan": self.dns_results,
            "compliance": self.compliance_results,
            "risk": self.risk_results,
            "risk_matrix": self.risk_matrix_results,
            "findings": self.all_findings,
            "scan_summary": {
                "targets": [self.target],
                "scan_types": [
                    t for t, d in [
                        ("Network", self.network_results),
                        ("Web", self.web_results),
                        ("DNS", self.dns_results),
                    ] if d
                ],
                "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            },
        }
