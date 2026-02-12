"""
DDoS Attack Scenario
=====================

Simulates a distributed denial-of-service attack targeting the
organization's public-facing web infrastructure, combining volumetric
flooding with application-layer attacks to overwhelm services.

Attack narrative:
    A multi-vector DDoS attack combines UDP flood (volumetric), SYN flood
    (protocol), and HTTP slowloris (application-layer) to overwhelm the
    organization's e-commerce platform during a peak sales period.
    The attack is accompanied by a ransom demand threatening continued
    disruption unless payment is made.
"""

from typing import Dict, List, Any


class DDoSScenario:
    """DDoS attack incident response scenario with decision tree."""

    def __init__(self):
        self.name = "ddos"
        self.title = "Multi-Vector DDoS Attack on E-Commerce Platform"
        self.description = (
            "The NOC is reporting severe degradation of the public-facing e-commerce "
            "platform. Response times have increased from 200ms to 45 seconds, and "
            "60% of customer requests are timing out. Network monitoring shows inbound "
            "traffic has spiked from a baseline of 2 Gbps to 38 Gbps in the past 20 "
            "minutes. The traffic is originating from thousands of source IPs across "
            "multiple countries. Simultaneously, the web application firewall (WAF) is "
            "logging a surge of slowloris-style HTTP connections holding resources open. "
            "The abuse@ inbox received a ransom email 30 minutes ago demanding 5 BTC "
            "to stop the attack."
        )
        self.default_severity = "high"
        self.estimated_duration_minutes = 35
        self.category = "ddos"
        self.affected_systems = [
            "Edge routers (border-rtr-01, border-rtr-02)",
            "Load balancers (lb-prod-01, lb-prod-02)",
            "Web servers (web-prod-01 through web-prod-08)",
            "WAF appliances (waf-prod-01, waf-prod-02)",
            "DNS servers (ns1.company.com, ns2.company.com)",
            "CDN endpoints (contracted provider)",
        ]
        self.initial_iocs = [
            {"type": "traffic_pattern", "value": "UDP flood - 28 Gbps from ~15,000 source IPs", "context": "Volumetric layer"},
            {"type": "traffic_pattern", "value": "SYN flood - 6 Gbps targeting port 443", "context": "Protocol layer"},
            {"type": "traffic_pattern", "value": "HTTP slowloris - 4,000+ concurrent half-open connections", "context": "Application layer"},
            {"type": "email", "value": "ddos-ransom@protonmail.com", "context": "Ransom demand sender"},
            {"type": "botnet_c2", "value": "Multiple Mirai-variant botnet nodes identified", "context": "Attack infrastructure"},
            {"type": "amplification", "value": "NTP and DNS amplification vectors detected", "context": "Reflection sources"},
        ]
        self.attack_vector = "Multi-vector DDoS: UDP volumetric flood + SYN flood + HTTP application-layer slowloris"

    def get_phases(self) -> List[Dict[str, Any]]:
        return [
            self._phase_detection(),
            self._phase_triage(),
            self._phase_containment(),
            self._phase_eradication(),
            self._phase_recovery(),
            self._phase_post_incident(),
        ]

    def _phase_detection(self) -> Dict[str, Any]:
        return {
            "phase": "detection",
            "phase_number": 1,
            "title": "DDoS Detection & Classification",
            "narrative": (
                "At 11:42 during a major promotional event, monitoring dashboards show:\n"
                "  - Inbound bandwidth: 38 Gbps (baseline: 2 Gbps) - 19x normal\n"
                "  - HTTP 503 errors: 60% of requests\n"
                "  - Average response time: 45 seconds (baseline: 200ms)\n"
                "  - Active TCP connections on web servers: 847,000 (baseline: 12,000)\n"
                "  - Customer complaints flooding support channels\n"
                "  - Revenue loss estimated at $15,000/minute during the promotion\n\n"
                "The NOC confirmed this is not a legitimate traffic surge from the promotion."
            ),
            "decisions": [
                {
                    "id": "det_1",
                    "prompt": "What is your first action?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Classify the attack vectors by analyzing traffic patterns (NetFlow, packet captures, WAF logs), engage the upstream ISP/DDoS mitigation service, and activate the DDoS response runbook",
                            "score": 10,
                            "feedback": "Correct. Classifying attack vectors is essential for targeted mitigation. Engaging upstream providers early is critical because the volumetric component exceeds your local capacity.",
                            "next_action": "Traffic analysis identifies three attack vectors. ISP is engaged and begins upstream filtering. DDoS runbook is activated.",
                        },
                        {
                            "id": "b",
                            "text": "Begin blocking source IPs at the perimeter firewall one by one",
                            "score": 2,
                            "feedback": "Ineffective. With 15,000+ source IPs in a botnet, manual IP blocking is futile. The volumetric component also exceeds your pipe capacity, so local filtering cannot help.",
                            "next_action": "A few hundred IPs are blocked. Attack continues unabated from thousands of remaining sources.",
                        },
                        {
                            "id": "c",
                            "text": "Increase web server capacity by spinning up additional instances",
                            "score": 4,
                            "feedback": "Scaling helps with application-layer attacks but does not address the 38 Gbps volumetric flood that exceeds your network capacity. You need upstream mitigation for the volumetric component.",
                            "next_action": "Additional web servers are provisioned. They help with legitimate traffic that gets through but the volumetric flood still saturates the link.",
                        },
                        {
                            "id": "d",
                            "text": "Pay the 5 BTC ransom to stop the attack quickly and minimize revenue loss",
                            "score": 0,
                            "feedback": "Never pay DDoS ransom. Payment does not guarantee the attack stops, funds criminal operations, and marks you as a paying target for future attacks.",
                            "next_action": "5 BTC is transferred. The attack continues. A second ransom demand arrives for 10 BTC.",
                        },
                    ],
                },
            ],
        }

    def _phase_triage(self) -> Dict[str, Any]:
        return {
            "phase": "triage",
            "phase_number": 2,
            "title": "Attack Vector Analysis & Impact Assessment",
            "narrative": (
                "Traffic analysis has identified three concurrent attack vectors:\n"
                "  1. UDP volumetric flood (28 Gbps) - NTP and DNS amplification\n"
                "  2. SYN flood (6 Gbps) targeting TCP/443\n"
                "  3. HTTP slowloris - 4,000+ half-open connections exhausting web server resources\n\n"
                "Your ISP has acknowledged the request but their mitigation deployment takes 15-30 minutes. "
                "Business impact: Estimated $15,000/minute in lost revenue plus reputational damage. "
                "The promotional event is scheduled to run for 6 more hours."
            ),
            "decisions": [
                {
                    "id": "tri_1",
                    "prompt": "While waiting for ISP mitigation, what local measures do you implement?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Enable SYN cookies on load balancers to handle the SYN flood, configure WAF rules to detect and drop slowloris connections (timeout half-open connections aggressively), implement rate limiting per source IP, activate GeoIP filtering to block traffic from countries with no business presence, enable CDN caching to serve static content from edge nodes",
                            "score": 10,
                            "feedback": "Excellent layered local mitigation addressing each attack vector with appropriate countermeasures while preserving legitimate traffic access.",
                            "next_action": "SYN cookies reduce TCP state exhaustion. Slowloris connections are terminated. Rate limiting and GeoIP filtering reduce attack surface. CDN absorbs cacheable requests.",
                        },
                        {
                            "id": "b",
                            "text": "Take the site offline entirely with a maintenance page to protect backend systems",
                            "score": 5,
                            "feedback": "This protects infrastructure but concedes the attacker's goal of service disruption. Local mitigation measures can restore partial service while waiting for upstream filtering.",
                            "next_action": "Site is offline. Revenue loss continues at full rate. Backend systems are protected.",
                        },
                        {
                            "id": "c",
                            "text": "Redirect all traffic through a cloud-based DDoS scrubbing service by changing DNS",
                            "score": 7,
                            "feedback": "Good approach if you have a cloud scrubbing service. DNS propagation takes time (TTL-dependent) but this is a strong medium-term mitigation. Best combined with local measures during DNS propagation.",
                            "next_action": "DNS change is initiated. Propagation takes 15-45 minutes depending on TTL. Meanwhile, the attack continues hitting origin servers.",
                        },
                        {
                            "id": "d",
                            "text": "Focus exclusively on the volumetric component since it has the highest bandwidth",
                            "score": 3,
                            "feedback": "The volumetric component requires upstream mitigation (beyond local capacity). Focusing only on it while ignoring the slowloris and SYN flood wastes time on something you cannot solve locally.",
                            "next_action": "Local efforts on the volumetric attack are futile. Slowloris and SYN flood continue unchecked.",
                        },
                    ],
                },
            ],
        }

    def _phase_containment(self) -> Dict[str, Any]:
        return {
            "phase": "containment",
            "phase_number": 3,
            "title": "Mitigation Deployment & Traffic Scrubbing",
            "narrative": (
                "ISP upstream filtering is now active for the UDP volumetric component. Inbound "
                "bandwidth has dropped from 38 Gbps to 8 Gbps. Local mitigations are handling "
                "the SYN flood and slowloris attacks. Service is partially restored - response "
                "times are at 3 seconds (down from 45s) and 80% of requests are succeeding.\n\n"
                "However, the attacker appears to be adapting. The attack pattern is shifting - "
                "new HTTP flood requests are arriving that mimic legitimate user behavior (valid "
                "User-Agent strings, proper headers, realistic browsing patterns)."
            ),
            "decisions": [
                {
                    "id": "con_1",
                    "prompt": "How do you handle the adaptive application-layer attack?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Implement JavaScript-based browser challenges (CAPTCHA or proof-of-work) for suspicious traffic, deploy behavioral analysis to distinguish bots from real users based on session patterns, and enable request rate limiting with progressive penalties",
                            "score": 10,
                            "feedback": "Sophisticated response to application-layer attacks. Browser challenges filter out bots that cannot execute JavaScript, while behavioral analysis catches more advanced bots.",
                            "next_action": "Browser challenges filter 90% of bot traffic. Behavioral analysis catches another 8%. Legitimate users experience a brief CAPTCHA but can access the site.",
                        },
                        {
                            "id": "b",
                            "text": "Block all traffic except from known customer IP ranges",
                            "score": 2,
                            "feedback": "Impractical. You do not have a comprehensive list of customer IPs, especially for an e-commerce site serving the general public. This blocks legitimate customers.",
                            "next_action": "Allowlist is too narrow. The majority of legitimate customers are blocked.",
                        },
                        {
                            "id": "c",
                            "text": "Increase the WAF sensitivity to maximum and block anything that looks remotely suspicious",
                            "score": 4,
                            "feedback": "Maximum sensitivity creates excessive false positives, blocking legitimate users. Tuning must balance security with availability, especially during a promotional event.",
                            "next_action": "WAF false positive rate increases to 25%. Many legitimate customers are blocked and cannot complete purchases.",
                        },
                        {
                            "id": "d",
                            "text": "Accept the degraded performance and wait for the attacker to stop",
                            "score": 3,
                            "feedback": "Passive approach. DDoS attacks can persist for hours or days. Active mitigation is necessary to restore service quality, especially during a revenue-critical promotional period.",
                            "next_action": "Attack continues for another 4 hours. Revenue losses mount.",
                        },
                    ],
                },
            ],
        }

    def _phase_eradication(self) -> Dict[str, Any]:
        return {
            "phase": "eradication",
            "phase_number": 4,
            "title": "Sustained Mitigation & Attack Subsidence",
            "narrative": (
                "After 3 hours of sustained mitigation, the attack intensity is decreasing. "
                "Current inbound traffic is at 5 Gbps (down from 38 Gbps peak). The combination "
                "of upstream filtering, local mitigations, and browser challenges has been effective. "
                "Service is operating at 95% normal capacity."
            ),
            "decisions": [
                {
                    "id": "era_1",
                    "prompt": "The attack is subsiding. What do you do?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Maintain all mitigation measures in place for at least 24 hours after the attack subsides, gradually reduce restrictions while monitoring for resurgence, keep ISP scrubbing active, and document all attack characteristics for future detection rules",
                            "score": 10,
                            "feedback": "Correct. DDoS attacks frequently resurge when mitigations are removed prematurely. Maintaining defenses for a cooldown period and gradual reduction is the best practice.",
                            "next_action": "Mitigations remain active. A brief resurgence at hour +18 is handled automatically by existing rules.",
                        },
                        {
                            "id": "b",
                            "text": "Remove all mitigations now that the attack is subsiding to restore full performance",
                            "score": 2,
                            "feedback": "Premature. Removing mitigations invites resurgence. Attackers often pause to see if defenses drop before launching again.",
                            "next_action": "Mitigations are removed. The attack resurges within 2 hours at higher intensity.",
                        },
                        {
                            "id": "c",
                            "text": "Keep mitigations active and attempt to trace the attack back to its source for law enforcement",
                            "score": 6,
                            "feedback": "Maintaining mitigations is correct. Attribution is valuable but extremely difficult for DDoS attacks using botnets and amplification. ISP and law enforcement cooperation is needed for any chance of attribution.",
                            "next_action": "Mitigations remain active. Attribution analysis identifies several botnet C2 servers but operators remain anonymous.",
                        },
                        {
                            "id": "d",
                            "text": "Respond to the ransom email to gather intelligence on the attacker",
                            "score": 1,
                            "feedback": "Engaging with extortionists without law enforcement guidance is inadvisable. It confirms you received their message and may encourage further demands.",
                            "next_action": "Attacker responds with increased demands, knowing they have your attention.",
                        },
                    ],
                },
            ],
        }

    def _phase_recovery(self) -> Dict[str, Any]:
        return {
            "phase": "recovery",
            "phase_number": 5,
            "title": "Service Restoration & Monitoring",
            "narrative": (
                "The attack has fully subsided after 6 hours. ISP filtering and local mitigations "
                "handled the attack effectively. Service has been operating at near-normal levels "
                "for the past 4 hours. Total estimated revenue loss: $540,000. No data was compromised."
            ),
            "decisions": [
                {
                    "id": "rec_1",
                    "prompt": "How do you transition from incident response to normal operations?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Gradually step down mitigations over 48 hours while monitoring traffic patterns, leave ISP scrubbing on standby for rapid re-engagement, verify all systems are operating normally with performance testing, and prepare customer communication about the service disruption",
                            "score": 10,
                            "feedback": "Measured recovery approach. Gradual step-down prevents resurgence, ISP standby ensures rapid response, and customer communication maintains trust.",
                            "next_action": "Mitigations are gradually reduced. All systems pass performance testing. Customer communication is issued.",
                        },
                        {
                            "id": "b",
                            "text": "Return to full normal operations immediately and cancel the ISP mitigation service to save costs",
                            "score": 2,
                            "feedback": "Premature and penny-wise. The cost of ISP standby is minimal compared to potential re-attack impact. Cancelling mitigation capability removes your safety net.",
                            "next_action": "ISP service is cancelled. A follow-up attack weeks later requires re-engagement with deployment delays.",
                        },
                        {
                            "id": "c",
                            "text": "Keep maximum mitigations in place indefinitely",
                            "score": 4,
                            "feedback": "Over-cautious. Maximum mitigations may impact legitimate traffic and performance. Graduated reduction based on threat assessment is more appropriate.",
                            "next_action": "Aggressive rate limiting and CAPTCHA challenges remain in place, causing friction for legitimate customers.",
                        },
                        {
                            "id": "d",
                            "text": "Focus entirely on extending the promotional event to recover lost revenue",
                            "score": 3,
                            "feedback": "Business recovery is important but is a business decision, not an IR decision. The IR team should focus on ensuring technical resilience before business extends the promotion.",
                            "next_action": "Promotion is extended without technical validation. Residual mitigation rules cause checkout failures during the extended period.",
                        },
                    ],
                },
            ],
        }

    def _phase_post_incident(self) -> Dict[str, Any]:
        return {
            "phase": "post_incident",
            "phase_number": 6,
            "title": "Post-Incident Review & Resilience Improvements",
            "narrative": (
                "Incident is closed. Key metrics:\n"
                "  - Time to detect: 8 minutes\n"
                "  - Time to initial mitigation: 35 minutes\n"
                "  - Time to full service restoration: 90 minutes (partial), 3 hours (full)\n"
                "  - Total attack duration: 6 hours\n"
                "  - Revenue impact: ~$540,000\n"
                "  - Peak attack bandwidth: 38 Gbps\n"
                "  - Customer satisfaction impact: NPS dropped 12 points\n\n"
                "Identified gaps:\n"
                "  - No auto-scaling DDoS mitigation was in place\n"
                "  - ISP mitigation took 30 minutes to deploy\n"
                "  - No pre-staged DDoS response runbook existed\n"
                "  - Application layer was not designed for graceful degradation"
            ),
            "decisions": [
                {
                    "id": "post_1",
                    "prompt": "What infrastructure improvements do you recommend?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Implement always-on DDoS scrubbing (not on-demand), architect the application for graceful degradation under load, establish pre-negotiated ISP response SLAs with sub-5-minute activation, deploy auto-scaling infrastructure, create and regularly test a DDoS response runbook, and conduct quarterly DDoS simulation exercises",
                            "score": 10,
                            "feedback": "Comprehensive resilience improvement plan addressing detection speed, mitigation capacity, application architecture, and operational readiness.",
                            "next_action": "Budget is approved for always-on DDoS protection. Application team begins graceful degradation design. Quarterly DDoS drills are scheduled.",
                        },
                        {
                            "id": "b",
                            "text": "Upgrade the internet connection to higher bandwidth to absorb future attacks",
                            "score": 3,
                            "feedback": "Bandwidth upgrades provide marginal benefit. Attackers can scale beyond any reasonable pipe capacity. Cloud-based scrubbing with massive distributed capacity is more effective.",
                            "next_action": "Bandwidth is upgraded from 10 Gbps to 40 Gbps. Next attack uses 80 Gbps.",
                        },
                        {
                            "id": "c",
                            "text": "Move the entire application to a cloud provider with built-in DDoS protection",
                            "score": 7,
                            "feedback": "Cloud migration with DDoS protection is a strong long-term strategy but is a major architectural change. Shorter-term measures (always-on scrubbing, runbooks) should be implemented first.",
                            "next_action": "Cloud migration project is initiated. Full migration takes 12 months. Interim risk remains.",
                        },
                        {
                            "id": "d",
                            "text": "Track down the attackers and pursue legal action",
                            "score": 2,
                            "feedback": "Attribution of DDoS attacks is extremely difficult. Legal action requires identifying the attacker, which is rarely possible with botnet-based attacks. Focus on resilience over retaliation.",
                            "next_action": "Legal investigation is opened. No actionable attribution is possible.",
                        },
                    ],
                },
            ],
        }

    def get_max_score(self) -> int:
        total = 0
        for phase in self.get_phases():
            for decision in phase["decisions"]:
                max_choice_score = max(c["score"] for c in decision["choices"])
                total += max_choice_score
        return total

    def get_scoring_rubric(self) -> Dict[str, str]:
        max_score = self.get_max_score()
        return {
            "expert": f"{int(max_score * 0.9)}-{max_score}: Expert-level DDoS response",
            "proficient": f"{int(max_score * 0.7)}-{int(max_score * 0.9) - 1}: Proficient responder",
            "developing": f"{int(max_score * 0.5)}-{int(max_score * 0.7) - 1}: Developing skills",
            "novice": f"Below {int(max_score * 0.5)}: Significant gaps identified",
        }
