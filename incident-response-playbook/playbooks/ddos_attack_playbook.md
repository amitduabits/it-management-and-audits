# DDoS Attack Incident Response Playbook

**Classification:** CONFIDENTIAL
**Version:** 2.2
**Last Updated:** 2025-11-15
**Owner:** Security Operations Center / Network Operations Center
**Review Cycle:** Quarterly

---

## 1. Purpose

This playbook provides response procedures for distributed denial-of-service (DDoS) attacks targeting organizational infrastructure. It covers volumetric, protocol, and application-layer attacks, and coordinates actions between the SOC, NOC, and external mitigation providers.

## 2. Scope

This playbook covers:
- Volumetric attacks (UDP floods, DNS/NTP amplification, memcached reflection)
- Protocol attacks (SYN floods, fragmented packet attacks, Ping of Death)
- Application-layer attacks (HTTP floods, slowloris, low-and-slow attacks)
- Multi-vector attacks combining multiple techniques
- Ransom DDoS (RDDoS) with extortion demands
- DDoS as a smokescreen for other malicious activity

## 3. Severity Classification

| Indicator | SEV-1 (Critical) | SEV-2 (High) | SEV-3 (Medium) |
|-----------|-------------------|---------------|-----------------|
| Service impact | Complete outage | >50% degradation | <50% degradation |
| Revenue impact | >$10K/hour | $1K-$10K/hour | <$1K/hour |
| Systems affected | Customer-facing + internal | Customer-facing only | Internal only |
| Duration | >1 hour or recurring | 30 min - 1 hour | <30 minutes |
| Attack bandwidth | >10x normal | 5-10x normal | 2-5x normal |

---

## Phase 1: Preparation

### Step 1: Upstream Protection
- Contract with a DDoS mitigation provider (cloud-based scrubbing service)
- Negotiate SLA for mitigation activation time (<5 minutes for always-on, <15 minutes for on-demand)
- Establish BGP-based traffic diversion procedures with ISP
- Maintain redundant ISP connections from different providers
- Pre-configure DNS TTLs to allow rapid failover to scrubbing service

### Step 2: Infrastructure Hardening
- Enable SYN cookies on all load balancers and web servers
- Configure rate limiting at the load balancer and WAF layers
- Deploy CDN for cacheable content to absorb volumetric attacks on static assets
- Implement GeoIP filtering capabilities (ready to activate, not necessarily active)
- Configure connection timeouts aggressively for idle connections
- Over-provision bandwidth headroom (minimum 2x peak legitimate traffic)

### Step 3: Detection Capability
- Configure network monitoring for traffic anomaly detection (NetFlow, sFlow)
- Set bandwidth thresholds and alert on deviations (>200% of baseline)
- Monitor TCP SYN/ACK ratios for SYN flood detection
- Monitor HTTP error rates (503, timeout) for application-layer attacks
- Implement real-time dashboards for NOC visibility

### Step 4: Response Resources
- Document ISP and DDoS mitigation provider emergency contact procedures
- Pre-stage runbooks with specific mitigation steps per attack type
- Maintain current network topology diagrams showing all ingress points
- Establish communication plan for customer notification during outages

---

## Phase 2: Detection & Analysis

### Step 5: Confirm DDoS Attack
**Actions:**
1. Verify the traffic spike is not legitimate (marketing campaign, viral event, new product launch)
2. Examine traffic characteristics:
   - Source IP distribution: concentrated or distributed across thousands of IPs?
   - Protocol distribution: is the flood a single protocol or mixed?
   - Packet sizes: small packets (SYN flood) or large packets (volumetric)?
   - Request patterns: random or targeting specific URLs/endpoints?
3. Check monitoring dashboards for traffic volume, error rates, and response times
4. Confirm service degradation or outage via external monitoring (synthetic monitors)
5. Rule out internal issues (misconfiguration, resource exhaustion, software bug)

### Step 6: Classify Attack Vector(s)
**Determine which attack types are present:**

| Layer | Attack Type | Indicators |
|-------|-------------|------------|
| L3/L4 Volumetric | UDP flood, amplification | Massive bandwidth consumption, spoofed source IPs |
| L4 Protocol | SYN flood | High SYN/ACK ratio, TCP state table exhaustion |
| L4 Protocol | Fragmentation | Malformed/fragmented packets consuming reassembly resources |
| L7 Application | HTTP flood | High request rate to specific endpoints, valid HTTP requests |
| L7 Application | Slowloris | Many half-open HTTP connections, low bandwidth but high connection count |
| L7 Application | Slow POST | Very slow POST request body transmission |

### Step 7: Activate IR Team and Notify Stakeholders
**Actions:**
1. Activate joint SOC/NOC response team
2. Notify Incident Commander
3. Engage DDoS mitigation provider (if not always-on)
4. Notify business stakeholders about service impact
5. Alert customer support team to prepare for increased inquiries
6. If ransom demand received: notify Legal and law enforcement (FBI, CISA)
7. **DO NOT** respond to ransom demands without legal guidance

---

## Phase 3: Containment & Mitigation

### Step 8: Upstream Mitigation
**For volumetric attacks exceeding local capacity:**
1. Activate cloud-based DDoS scrubbing service
2. Divert traffic through scrubbing center (BGP announcement or DNS change)
3. Communicate with ISP to implement upstream blackholing or filtering if needed
4. Verify scrubbed traffic is reaching origin servers
5. Monitor mitigation effectiveness: is service restoring?

### Step 9: Local Mitigation - Network Layer
**Actions:**
1. Apply rate limiting at the network perimeter per source IP
2. Enable GeoIP filtering to block traffic from countries with no business presence
3. Block known amplification source ports (NTP: 123, DNS: 53, memcached: 11211) if not needed
4. Enable strict uRPF (unicast Reverse Path Forwarding) on border routers
5. Implement ACLs to block the most abusive source IP ranges (if identifiable)
6. If using BGP: consider selective blackholing of attacked IP prefixes as last resort

### Step 10: Local Mitigation - Protocol Layer
**For SYN floods:**
1. Enable SYN cookies on all affected load balancers and servers
2. Reduce SYN-RECEIVED timeout value
3. Increase TCP backlog queue size
4. Drop connections from IPs exceeding SYN rate threshold

**For fragmentation attacks:**
1. Configure routers to drop fragmented packets exceeding reassembly thresholds
2. Enable fragment reassembly limits

### Step 11: Local Mitigation - Application Layer
**For HTTP floods:**
1. Deploy JavaScript browser challenges (CAPTCHA, proof-of-work) for suspicious traffic
2. Implement behavioral analysis to distinguish bots from legitimate users:
   - Session duration and page interaction patterns
   - JavaScript execution capability
   - Cookie support
   - Mouse movement and keyboard interaction patterns
3. Rate limit per source IP on affected endpoints
4. Cache aggressively at CDN edge nodes
5. If specific URLs are targeted: implement request queuing

**For slowloris/slow attacks:**
1. Set aggressive connection idle timeouts (10-30 seconds)
2. Limit maximum concurrent connections per source IP
3. Set minimum data transfer rate thresholds; drop connections below threshold
4. Deploy a reverse proxy that buffers complete requests before forwarding to origin

### Step 12: Verify Mitigation Effectiveness
**Actions:**
1. Monitor service availability and response times from external vantage points
2. Check error rates are returning to normal levels
3. Verify legitimate users can access the service
4. Monitor for attack adaptation (vector changes after mitigation is applied)
5. Adjust mitigation rules if the attacker changes tactics
6. Document all mitigation actions and their effects

---

## Phase 4: Eradication

### Step 13: Sustained Mitigation
**Actions:**
1. Maintain all mitigation measures for minimum 24 hours after attack subsides
2. Monitor for attack resurgence during the cooldown period
3. Gradually reduce mitigation intensity while monitoring traffic patterns
4. Keep ISP/cloud scrubbing on standby for rapid re-engagement
5. Update permanent firewall and WAF rules based on observed attack patterns

### Step 14: Check for Concurrent Attacks
**DDoS may be used as a smokescreen for other attacks:**
1. Review SIEM alerts generated during the DDoS window for non-DDoS indicators
2. Check for unauthorized access attempts that may have been masked by alert fatigue
3. Verify no data exfiltration occurred during the DDoS distraction
4. Review authentication logs for anomalous logins during the attack window
5. Conduct a brief threat hunt for indicators unrelated to the DDoS

---

## Phase 5: Recovery

### Step 15: Service Restoration
**Actions:**
1. Verify all services are fully operational with normal response times
2. Remove temporary mitigation rules that impact legitimate traffic (CAPTCHA, aggressive rate limits)
3. Restore any DNS changes or BGP routing modifications to normal
4. Verify CDN caching and edge configurations are correct
5. Run performance and load tests to confirm system capacity

### Step 16: Customer Communication
**Actions:**
1. Issue customer-facing communication about the resolved incident
2. Provide estimated timeline of when degradation occurred and when it was resolved
3. If SLA credits apply: begin the SLA credit assessment process
4. Update public status page
5. Prepare responses for media inquiries if the outage was publicly visible

### Step 17: Gradual Mitigation Reduction
**Actions:**
1. Step down mitigation measures gradually over 48-72 hours
2. Remove GeoIP restrictions if they block legitimate traffic
3. Reduce rate limiting thresholds back to normal levels
4. Keep DDoS mitigation provider on standby status (not fully disengaged)
5. Maintain enhanced monitoring for 2 weeks post-incident

---

## Phase 6: Post-Incident Activity

### Step 18: Post-Incident Review
**Conduct within 5 business days:**
1. Document the full attack timeline with bandwidth graphs
2. Analyze attack vectors and their relative effectiveness
3. Evaluate detection time: how quickly was the DDoS identified?
4. Evaluate mitigation deployment time: how quickly were countermeasures active?
5. Assess business impact: revenue loss, customer impact, reputational damage
6. Review ISP/mitigation provider SLA compliance
7. Identify what worked and what needs improvement

### Step 19: Resilience Improvements
**Actions:**
1. If on-demand mitigation: evaluate moving to always-on DDoS protection
2. Architect applications for graceful degradation under load
3. Implement auto-scaling for web and application tiers
4. Improve monitoring and alerting thresholds based on observed attack patterns
5. Establish pre-authorized mitigation actions that NOC can execute without IR team approval
6. Negotiate improved ISP SLAs for DDoS response
7. Create or update the DDoS-specific runbook with lessons learned

### Step 20: Tabletop Exercise
**Schedule within 30 days:**
1. Conduct a tabletop exercise based on the observed attack scenario
2. Include NOC, SOC, and business stakeholders
3. Validate that improvements address the identified gaps
4. Test communication procedures with ISP and mitigation provider
5. Document exercise findings and additional improvements

---

## Appendix A: DDoS Mitigation Quick Reference

| Attack Type | Primary Mitigation | Secondary Mitigation |
|-------------|-------------------|---------------------|
| UDP Volumetric | Upstream scrubbing/blackholing | Rate limiting, GeoIP filtering |
| NTP/DNS Amplification | Block source ports, upstream filtering | uRPF, rate limiting |
| SYN Flood | SYN cookies, rate limiting | Reduce SYN timeout, increase backlog |
| HTTP Flood | Browser challenges, behavioral analysis | Rate limiting, WAF rules |
| Slowloris | Connection timeouts, reverse proxy | Max connections per IP |
| DNS Flood | DNS rate limiting, Anycast DNS | Upstream DNS filtering |

## Appendix B: Key Contacts

| Role | Contact | Activation Criteria |
|------|---------|-------------------|
| ISP NOC | [ISP Emergency Line] | Volumetric attacks >10 Gbps |
| DDoS Mitigation Provider | [Provider 24/7 Line] | Any confirmed DDoS |
| CDN Provider | [CDN Support] | Application-layer attacks |
| DNS Provider | [DNS Emergency] | DNS-targeted attacks |
| Internal NOC | [NOC On-Call] | All DDoS incidents |
| SOC | [SOC On-Call] | All confirmed attacks |

## Appendix C: Monitoring Thresholds

| Metric | Warning | Alert | Critical |
|--------|---------|-------|----------|
| Inbound bandwidth | >150% baseline | >300% baseline | >500% baseline |
| HTTP error rate (5xx) | >5% | >15% | >30% |
| Response time (P95) | >2x baseline | >5x baseline | >10x baseline |
| TCP connections | >200% normal | >500% normal | >1000% normal |
| SYN/ACK ratio | <0.8 | <0.5 | <0.3 |

---

*This playbook is a living document. Report any gaps or suggested improvements to the Security Operations and Network Operations teams.*
