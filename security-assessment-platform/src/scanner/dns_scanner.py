"""
DNS Scanner Module - DNS record enumeration and security analysis.

Performs comprehensive DNS reconnaissance including:
- Standard record types (A, AAAA, MX, NS, TXT, CNAME, SOA)
- SPF (Sender Policy Framework) record validation
- DMARC (Domain-based Message Authentication) policy analysis
- DNSSEC status verification
- Mail server security posture assessment

ETHICAL USE NOTICE:
    DNS enumeration is generally considered passive reconnaissance.
    However, always ensure your assessment scope includes DNS analysis
    for the target domain.
"""

import socket
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

try:
    import dns.resolver
    import dns.rdatatype
    import dns.exception
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class DNSRecord:
    """A single DNS record entry."""

    record_type: str
    name: str
    value: str
    ttl: int = 0
    priority: int = 0  # For MX records


@dataclass
class SPFResult:
    """SPF record analysis result."""

    exists: bool = False
    record: str = ""
    mechanisms: List[str] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    policy: str = ""  # "pass", "softfail", "fail", "neutral"
    is_valid: bool = False
    issues: List[str] = field(default_factory=list)
    findings: List[Dict] = field(default_factory=list)


@dataclass
class DMARCResult:
    """DMARC record analysis result."""

    exists: bool = False
    record: str = ""
    policy: str = ""  # "none", "quarantine", "reject"
    subdomain_policy: str = ""
    percentage: int = 100
    rua: str = ""  # Aggregate report URI
    ruf: str = ""  # Forensic report URI
    adkim: str = ""  # DKIM alignment mode
    aspf: str = ""  # SPF alignment mode
    is_valid: bool = False
    issues: List[str] = field(default_factory=list)
    findings: List[Dict] = field(default_factory=list)


@dataclass
class DNSScanResult:
    """Complete DNS scan result for a domain."""

    domain: str
    scan_timestamp: str = ""
    records: Dict[str, List[DNSRecord]] = field(default_factory=dict)
    spf: Optional[SPFResult] = None
    dmarc: Optional[DMARCResult] = None
    has_dnssec: bool = False
    nameservers: List[str] = field(default_factory=list)
    mail_servers: List[str] = field(default_factory=list)
    findings: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        records_dict = {}
        for rtype, rlist in self.records.items():
            records_dict[rtype] = [
                {
                    "type": r.record_type,
                    "name": r.name,
                    "value": r.value,
                    "ttl": r.ttl,
                    "priority": r.priority,
                }
                for r in rlist
            ]

        return {
            "domain": self.domain,
            "scan_timestamp": self.scan_timestamp,
            "records": records_dict,
            "spf": {
                "exists": self.spf.exists,
                "record": self.spf.record,
                "policy": self.spf.policy,
                "is_valid": self.spf.is_valid,
                "issues": self.spf.issues,
                "findings": self.spf.findings,
            } if self.spf else None,
            "dmarc": {
                "exists": self.dmarc.exists,
                "record": self.dmarc.record,
                "policy": self.dmarc.policy,
                "is_valid": self.dmarc.is_valid,
                "issues": self.dmarc.issues,
                "findings": self.dmarc.findings,
            } if self.dmarc else None,
            "has_dnssec": self.has_dnssec,
            "nameservers": self.nameservers,
            "mail_servers": self.mail_servers,
            "findings": self.findings,
        }


class DNSScanner:
    """
    DNS record enumerator and security analyzer.

    Performs comprehensive DNS analysis including record enumeration,
    email security policy validation (SPF/DMARC), and DNSSEC
    verification.

    Attributes:
        resolver: DNS resolver instance with configured nameservers.
        timeout: DNS query timeout in seconds.

    Example:
        scanner = DNSScanner(timeout=5)
        result = scanner.scan("example.com")
        print(f"MX Records: {len(result.records.get('MX', []))}")
        print(f"SPF Valid: {result.spf.is_valid}")
        print(f"DMARC Policy: {result.dmarc.policy}")
    """

    def __init__(
        self,
        timeout: float = 5.0,
        nameservers: Optional[List[str]] = None,
    ):
        """
        Initialize the DNSScanner.

        Args:
            timeout: DNS query timeout in seconds.
            nameservers: Optional list of DNS server IPs to use.
                Defaults to system DNS configuration.
        """
        self.timeout = timeout

        if DNS_AVAILABLE:
            self.resolver = dns.resolver.Resolver()
            self.resolver.timeout = timeout
            self.resolver.lifetime = timeout * 2
            if nameservers:
                self.resolver.nameservers = nameservers
        else:
            self.resolver = None

    def scan(self, domain: str) -> DNSScanResult:
        """
        Perform a comprehensive DNS scan of the target domain.

        Enumerates all common record types, validates email security
        policies, and checks for DNSSEC.

        Args:
            domain: The domain name to scan (e.g., "example.com").

        Returns:
            DNSScanResult with all findings.

        Raises:
            ValueError: If domain is empty or invalid.
        """
        if not domain:
            raise ValueError("Domain must be specified")

        domain = domain.strip().lower()
        if domain.startswith("http://") or domain.startswith("https://"):
            # Strip protocol if accidentally included
            from urllib.parse import urlparse
            domain = urlparse(domain).netloc or domain

        result = DNSScanResult(domain=domain)
        result.scan_timestamp = datetime.now().isoformat()

        if not DNS_AVAILABLE:
            logger.warning(
                "dnspython library not available. "
                "Install with: pip install dnspython. "
                "Falling back to basic socket resolution."
            )
            result = self._basic_dns_scan(domain, result)
            return result

        logger.info(f"Starting DNS scan for domain: {domain}")

        # Enumerate standard record types
        record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]
        for rtype in record_types:
            records = self._query_records(domain, rtype)
            if records:
                result.records[rtype] = records

        # Extract nameservers
        ns_records = result.records.get("NS", [])
        result.nameservers = [r.value.rstrip(".") for r in ns_records]

        # Extract mail servers
        mx_records = result.records.get("MX", [])
        result.mail_servers = [
            r.value.rstrip(".") for r in sorted(mx_records, key=lambda x: x.priority)
        ]

        # SPF analysis
        result.spf = self._analyze_spf(domain, result.records.get("TXT", []))

        # DMARC analysis
        result.dmarc = self._analyze_dmarc(domain)

        # DNSSEC check
        result.has_dnssec = self._check_dnssec(domain)

        # Generate findings
        result.findings = self._generate_findings(result)

        logger.info(
            f"DNS scan complete for {domain}: "
            f"{sum(len(v) for v in result.records.values())} total records, "
            f"{len(result.findings)} findings"
        )

        return result

    def _query_records(
        self, domain: str, record_type: str
    ) -> List[DNSRecord]:
        """
        Query DNS records of a specific type.

        Args:
            domain: Target domain name.
            record_type: DNS record type (A, AAAA, MX, etc.).

        Returns:
            List of DNSRecord objects.
        """
        records = []

        try:
            answers = self.resolver.resolve(domain, record_type)

            for rdata in answers:
                record = DNSRecord(
                    record_type=record_type,
                    name=domain,
                    value=str(rdata),
                    ttl=answers.rrset.ttl if answers.rrset else 0,
                )

                # Extract MX priority
                if record_type == "MX":
                    record.priority = rdata.preference
                    record.value = str(rdata.exchange)

                records.append(record)

        except dns.resolver.NXDOMAIN:
            logger.debug(f"Domain {domain} does not exist for {record_type}")
        except dns.resolver.NoAnswer:
            logger.debug(f"No {record_type} records for {domain}")
        except dns.resolver.NoNameservers:
            logger.warning(f"No nameservers available for {domain}")
        except dns.exception.Timeout:
            logger.warning(f"DNS query timeout for {domain} {record_type}")
        except Exception as e:
            logger.debug(f"DNS query error for {domain} {record_type}: {e}")

        return records

    def _analyze_spf(
        self, domain: str, txt_records: List[DNSRecord]
    ) -> SPFResult:
        """
        Analyze SPF (Sender Policy Framework) configuration.

        Validates SPF record syntax, checks for common misconfigurations,
        and evaluates the enforcement policy.

        Args:
            domain: The target domain.
            txt_records: TXT records already retrieved for the domain.

        Returns:
            SPFResult with analysis details.
        """
        spf_result = SPFResult()

        # Find SPF record in TXT records
        spf_record = None
        spf_count = 0
        for record in txt_records:
            value = record.value.strip('"').strip("'")
            if value.startswith("v=spf1"):
                spf_record = value
                spf_count += 1

        if not spf_record:
            spf_result.exists = False
            spf_result.issues.append("No SPF record found")
            spf_result.findings.append({
                "id": "DNS-SPF-MISSING",
                "category": "Email Security",
                "title": "Missing SPF Record",
                "description": (
                    f"No SPF record found for {domain}. Without SPF, "
                    "anyone can send email appearing to come from this domain."
                ),
                "severity": "high",
                "cvss_score": 7.5,
                "remediation": (
                    "Create a TXT record with SPF policy. Example: "
                    "v=spf1 include:_spf.google.com ~all"
                ),
            })
            return spf_result

        spf_result.exists = True
        spf_result.record = spf_record
        spf_result.is_valid = True

        # Multiple SPF records check
        if spf_count > 1:
            spf_result.issues.append("Multiple SPF records found (RFC violation)")
            spf_result.is_valid = False
            spf_result.findings.append({
                "id": "DNS-SPF-MULTI",
                "category": "Email Security",
                "title": "Multiple SPF Records",
                "description": (
                    f"Found {spf_count} SPF records for {domain}. "
                    "RFC 7208 requires exactly one SPF record."
                ),
                "severity": "high",
                "cvss_score": 6.5,
                "remediation": "Merge all SPF records into a single TXT record.",
            })

        # Parse mechanisms
        parts = spf_record.split()
        for part in parts[1:]:  # Skip "v=spf1"
            if part.startswith("include:"):
                spf_result.includes.append(part.split(":")[1])
            spf_result.mechanisms.append(part)

        # Check policy (last mechanism)
        if parts:
            last = parts[-1].lower()
            if last == "+all":
                spf_result.policy = "pass"
                spf_result.issues.append(
                    "SPF policy is +all (allows anyone to send)"
                )
                spf_result.findings.append({
                    "id": "DNS-SPF-PERMISSIVE",
                    "category": "Email Security",
                    "title": "SPF Policy Allows All Senders (+all)",
                    "description": (
                        "SPF record ends with +all, which effectively "
                        "allows any server to send email as this domain."
                    ),
                    "severity": "critical",
                    "cvss_score": 9.0,
                    "remediation": (
                        "Change +all to -all (hard fail) or ~all (soft fail). "
                        "Enumerate all legitimate sending sources first."
                    ),
                })
            elif last == "~all":
                spf_result.policy = "softfail"
            elif last == "-all":
                spf_result.policy = "fail"
            elif last == "?all":
                spf_result.policy = "neutral"
                spf_result.issues.append(
                    "SPF policy is ?all (neutral - no protection)"
                )

        # DNS lookup limit check
        lookup_mechanisms = ["include", "a", "mx", "ptr", "exists", "redirect"]
        lookup_count = sum(
            1 for m in spf_result.mechanisms
            if any(m.lower().startswith(lm) for lm in lookup_mechanisms)
        )
        if lookup_count > 10:
            spf_result.issues.append(
                f"SPF record requires {lookup_count} DNS lookups "
                "(max 10 per RFC 7208)"
            )
            spf_result.findings.append({
                "id": "DNS-SPF-LOOKUPS",
                "category": "Email Security",
                "title": "SPF Exceeds DNS Lookup Limit",
                "description": (
                    f"SPF record requires {lookup_count} DNS lookups. "
                    "RFC 7208 limits SPF to 10 DNS lookups."
                ),
                "severity": "medium",
                "cvss_score": 5.0,
                "remediation": (
                    "Reduce DNS lookups by flattening SPF record. "
                    "Replace include: mechanisms with direct IP ranges where possible."
                ),
            })

        return spf_result

    def _analyze_dmarc(self, domain: str) -> DMARCResult:
        """
        Analyze DMARC (Domain-based Message Authentication) policy.

        Queries _dmarc.domain for DMARC records, validates syntax,
        and evaluates policy strength.

        Args:
            domain: The target domain.

        Returns:
            DMARCResult with analysis details.
        """
        dmarc_result = DMARCResult()
        dmarc_domain = f"_dmarc.{domain}"

        # Query DMARC record
        dmarc_records = self._query_records(dmarc_domain, "TXT")

        dmarc_record = None
        for record in dmarc_records:
            value = record.value.strip('"').strip("'")
            if value.startswith("v=DMARC1"):
                dmarc_record = value
                break

        if not dmarc_record:
            dmarc_result.exists = False
            dmarc_result.findings.append({
                "id": "DNS-DMARC-MISSING",
                "category": "Email Security",
                "title": "Missing DMARC Record",
                "description": (
                    f"No DMARC record found for {domain}. "
                    "Without DMARC, email receivers cannot verify the "
                    "authenticity of messages from this domain."
                ),
                "severity": "high",
                "cvss_score": 7.5,
                "remediation": (
                    "Create a TXT record at _dmarc.{domain} with DMARC policy. "
                    "Start with: v=DMARC1; p=none; rua=mailto:dmarc@{domain} "
                    "then gradually move to p=quarantine and p=reject."
                ),
            })
            return dmarc_result

        dmarc_result.exists = True
        dmarc_result.record = dmarc_record
        dmarc_result.is_valid = True

        # Parse DMARC tags
        tags = {}
        for part in dmarc_record.split(";"):
            part = part.strip()
            if "=" in part:
                key, value = part.split("=", 1)
                tags[key.strip().lower()] = value.strip()

        dmarc_result.policy = tags.get("p", "none")
        dmarc_result.subdomain_policy = tags.get("sp", dmarc_result.policy)
        dmarc_result.rua = tags.get("rua", "")
        dmarc_result.ruf = tags.get("ruf", "")
        dmarc_result.adkim = tags.get("adkim", "r")
        dmarc_result.aspf = tags.get("aspf", "r")

        try:
            dmarc_result.percentage = int(tags.get("pct", "100"))
        except ValueError:
            dmarc_result.percentage = 100

        # Policy strength analysis
        if dmarc_result.policy == "none":
            dmarc_result.issues.append(
                "DMARC policy is 'none' (monitoring only, no enforcement)"
            )
            dmarc_result.findings.append({
                "id": "DNS-DMARC-NONE",
                "category": "Email Security",
                "title": "DMARC Policy Set to None (No Enforcement)",
                "description": (
                    "DMARC policy is set to 'none', which only monitors "
                    "but does not prevent email spoofing."
                ),
                "severity": "medium",
                "cvss_score": 5.5,
                "remediation": (
                    "After reviewing DMARC aggregate reports, upgrade "
                    "policy to 'quarantine' then 'reject' for full protection."
                ),
            })

        # No reporting configured
        if not dmarc_result.rua:
            dmarc_result.issues.append("No aggregate reporting URI (rua) configured")
            dmarc_result.findings.append({
                "id": "DNS-DMARC-NORUA",
                "category": "Email Security",
                "title": "DMARC Missing Aggregate Reporting",
                "description": (
                    "No rua (aggregate report) URI configured in DMARC. "
                    "Without reports, you cannot monitor email authentication."
                ),
                "severity": "medium",
                "cvss_score": 4.0,
                "remediation": (
                    "Add rua=mailto:dmarc-reports@yourdomain.com to receive "
                    "daily aggregate DMARC reports."
                ),
            })

        # Percentage less than 100
        if dmarc_result.percentage < 100:
            dmarc_result.issues.append(
                f"DMARC only applied to {dmarc_result.percentage}% of messages"
            )

        return dmarc_result

    def _check_dnssec(self, domain: str) -> bool:
        """
        Check if DNSSEC is enabled for the domain.

        Args:
            domain: The target domain.

        Returns:
            True if DNSSEC is enabled, False otherwise.
        """
        try:
            response = self.resolver.resolve(domain, "DNSKEY")
            return len(response) > 0
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            return False
        except dns.exception.Timeout:
            return False
        except Exception:
            return False

    def _basic_dns_scan(
        self, domain: str, result: DNSScanResult
    ) -> DNSScanResult:
        """
        Perform basic DNS resolution using socket (fallback when dnspython
        is not available).

        Args:
            domain: The target domain.
            result: The DNSScanResult to populate.

        Returns:
            Partially populated DNSScanResult.
        """
        try:
            # Basic A record resolution
            ip_addresses = socket.getaddrinfo(
                domain, None, socket.AF_INET, socket.SOCK_STREAM
            )
            a_records = []
            seen_ips = set()
            for info in ip_addresses:
                ip = info[4][0]
                if ip not in seen_ips:
                    a_records.append(DNSRecord(
                        record_type="A",
                        name=domain,
                        value=ip,
                    ))
                    seen_ips.add(ip)
            if a_records:
                result.records["A"] = a_records

            # IPv6 resolution
            try:
                ipv6_addresses = socket.getaddrinfo(
                    domain, None, socket.AF_INET6, socket.SOCK_STREAM
                )
                aaaa_records = []
                seen_ipv6 = set()
                for info in ipv6_addresses:
                    ip = info[4][0]
                    if ip not in seen_ipv6:
                        aaaa_records.append(DNSRecord(
                            record_type="AAAA",
                            name=domain,
                            value=ip,
                        ))
                        seen_ipv6.add(ip)
                if aaaa_records:
                    result.records["AAAA"] = aaaa_records
            except socket.gaierror:
                pass

        except socket.gaierror as e:
            logger.error(f"DNS resolution failed for {domain}: {e}")

        result.findings.append({
            "id": "DNS-LIMITED",
            "category": "DNS Security",
            "title": "Limited DNS Analysis (dnspython not installed)",
            "description": (
                "Full DNS analysis requires the dnspython library. "
                "Only basic A/AAAA resolution was performed."
            ),
            "severity": "info",
            "cvss_score": 0.0,
            "remediation": "Install dnspython: pip install dnspython",
        })

        return result

    def _generate_findings(self, result: DNSScanResult) -> List[Dict]:
        """
        Generate security findings from DNS scan results.

        Args:
            result: The populated DNSScanResult.

        Returns:
            List of finding dictionaries.
        """
        findings = []

        # Include SPF and DMARC findings
        if result.spf:
            findings.extend(result.spf.findings)
        if result.dmarc:
            findings.extend(result.dmarc.findings)

        # DNSSEC check
        if not result.has_dnssec:
            findings.append({
                "id": "DNS-DNSSEC-MISSING",
                "category": "DNS Security",
                "title": "DNSSEC Not Enabled",
                "description": (
                    f"DNSSEC is not configured for {result.domain}. "
                    "Without DNSSEC, DNS responses can be spoofed "
                    "through cache poisoning attacks."
                ),
                "severity": "medium",
                "cvss_score": 5.9,
                "remediation": (
                    "Enable DNSSEC with your domain registrar. "
                    "Sign your DNS zone and publish DS records."
                ),
                "compliance_refs": [
                    "NIST CSF PR.DS-2",
                    "ISO 27001 A.13.1.1",
                ],
            })

        # Single nameserver check
        if len(result.nameservers) < 2:
            findings.append({
                "id": "DNS-NS-SINGLE",
                "category": "DNS Security",
                "title": "Insufficient Nameserver Redundancy",
                "description": (
                    f"Only {len(result.nameservers)} nameserver(s) found. "
                    "Minimum of 2 is required for availability."
                ),
                "severity": "medium",
                "cvss_score": 5.0,
                "remediation": (
                    "Configure at least 2 geographically distributed "
                    "nameservers for the domain."
                ),
            })

        # Wildcard DNS check
        wildcard_records = self._query_records(
            f"nonexistent-subdomain-test.{result.domain}", "A"
        )
        if wildcard_records:
            findings.append({
                "id": "DNS-WILDCARD",
                "category": "DNS Security",
                "title": "Wildcard DNS Record Detected",
                "description": (
                    "A wildcard DNS record (*.domain) is configured. "
                    "This can mask subdomain takeover vulnerabilities."
                ),
                "severity": "low",
                "cvss_score": 3.0,
                "remediation": (
                    "Review if wildcard DNS is necessary. "
                    "If not required, remove the wildcard record."
                ),
            })

        # No MX records
        if "MX" not in result.records:
            findings.append({
                "id": "DNS-MX-MISSING",
                "category": "DNS Security",
                "title": "No MX Records Found",
                "description": (
                    f"No MX records configured for {result.domain}. "
                    "If the domain handles email, this may indicate "
                    "misconfiguration."
                ),
                "severity": "low",
                "cvss_score": 2.0,
                "remediation": (
                    "If this domain should receive email, configure "
                    "appropriate MX records."
                ),
            })

        return findings
