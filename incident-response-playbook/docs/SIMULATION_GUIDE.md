# Simulation Guide

## Overview

The IR Playbook Engine includes an interactive simulation system for incident response training. Simulations present realistic incident scenarios with decision points at each phase of the NIST SP 800-61 lifecycle. Analysts select the best response at each decision point and receive scored feedback.

---

## Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### List Available Scenarios
```bash
python -m src.cli list-scenarios
```

### Run a Simulation
```bash
python -m src.cli simulate --scenario data_breach
```

### Generate a Report After Simulation
```bash
python -m src.cli generate-report --scenario data_breach --output report.html
```

---

## Available Scenarios

### 1. Data Breach (`data_breach`)
- **Severity:** Critical
- **Duration:** ~45 minutes
- **Focus:** Data exfiltration, scoping, regulatory notification
- **Scenario:** Compromised service account used to exfiltrate 2.3M customer records through an encrypted channel to an external staging server
- **Key Skills Tested:** Alert validation, scope assessment, evidence preservation, regulatory compliance

### 2. Ransomware (`ransomware`)
- **Severity:** Critical
- **Duration:** ~50 minutes
- **Focus:** Rapid containment, backup assessment, recovery prioritization
- **Scenario:** LockStorm ransomware deployed across Finance department via phishing, encrypting 31 workstations and 2 file servers
- **Key Skills Tested:** Speed of containment, backup evaluation, credential remediation, post-incident hardening

### 3. Phishing (`phishing`)
- **Severity:** High
- **Duration:** ~35 minutes
- **Focus:** Account compromise, BEC prevention, credential remediation
- **Scenario:** Spear-phishing campaign targeting senior staff leads to credential compromise, account takeover, and a $340K wire fraud attempt
- **Key Skills Tested:** Blast radius assessment, financial fraud prevention, mail rule auditing, MFA strategy

### 4. DDoS (`ddos`)
- **Severity:** High
- **Duration:** ~35 minutes
- **Focus:** Multi-vector mitigation, upstream coordination, service restoration
- **Scenario:** 38 Gbps multi-vector DDoS attack during a critical promotional event combining volumetric, protocol, and application-layer attacks
- **Key Skills Tested:** Attack classification, layered mitigation, ISP coordination, graceful degradation

### 5. Insider Threat (`insider_threat`)
- **Severity:** High
- **Duration:** ~40 minutes
- **Focus:** HR/Legal coordination, sabotage prevention, evidence handling
- **Scenario:** Departing DBA exfiltrates 14 GB of trade secrets and customer data, plants logic bombs on production database servers
- **Key Skills Tested:** Investigation coordination, sabotage detection, simultaneous access revocation, legal remedies

---

## Simulation Flow

Each simulation follows this structure:

```
1. SCENARIO BRIEFING
   - Incident description and context
   - Affected systems inventory
   - Initial indicators of compromise (IOCs)

2. PHASE-BY-PHASE PROGRESSION
   For each of the 6 NIST phases:
   a. Situation update (narrative)
   b. Decision point(s) presented
   c. Analyst selects best response (A/B/C/D)
   d. Immediate feedback with score and explanation
   e. Consequence of the choice (what happens next)

3. FINAL SCORING
   - Total score and percentage
   - Phase-by-phase breakdown
   - Performance rating (Expert/Proficient/Developing/Novice)
   - Areas for improvement with playbook references
```

---

## Scoring System

### Score Calculation
- Each decision point has multiple choices scored from 0 to 10
- The optimal choice earns the maximum points for that decision
- Suboptimal choices earn partial credit based on their effectiveness
- Dangerous or counterproductive choices earn 0-2 points

### Performance Ratings

| Rating | Percentage | Description |
|--------|-----------|-------------|
| **Expert** | 90-100% | Demonstrates comprehensive IR knowledge and optimal decision-making |
| **Proficient** | 70-89% | Solid IR skills with some areas for refinement |
| **Developing** | 50-69% | Foundational understanding; review playbooks for identified gaps |
| **Novice** | Below 50% | Significant gaps in IR knowledge; structured training recommended |

### Feedback Types
- **Green [+]:** Optimal or near-optimal response. Full marks.
- **Yellow [~]:** Acceptable but not optimal. Partial credit. Explanation of the better approach.
- **Red [-]:** Suboptimal or harmful response. Minimal or no credit. Detailed explanation of risks.

---

## Running Simulations for Training

### Individual Training
1. Select a scenario appropriate to the analyst's experience level
2. Run the simulation without time pressure for learning
3. Review feedback carefully at each decision point
4. After completion, review the corresponding playbook for the scenario type
5. Re-run the simulation to improve score

### Tabletop Exercise (Team)
1. Project the simulation on a shared screen
2. Assign an Incident Commander to facilitate discussion
3. At each decision point, the team discusses options before selecting
4. Use the feedback as a basis for team discussion
5. Document team observations and disagreements for post-exercise review

### Recommended Training Schedule

| Frequency | Activity |
|-----------|----------|
| Monthly | Individual simulation (rotate scenarios) |
| Quarterly | Team tabletop exercise using simulation framework |
| Semi-annually | Full scenario with report generation |
| Annually | All-hands tabletop with executive participation |

---

## Report Generation

### HTML Report
```bash
python -m src.cli generate-report --scenario data_breach --format html --output reports/breach_report.html
```

### JSON Report (Machine-Readable)
```bash
python -m src.cli generate-report --scenario ransomware --format json --output reports/ransomware.json
```

### Executive Summary (Text)
```bash
python -m src.cli generate-report --scenario phishing --format text --output reports/phishing_summary.txt
```

---

## Additional CLI Commands

### Severity Calculator
Calculate incident severity from assessment parameters:
```bash
python -m src.cli severity --data-class confidential --records 50000 \
    --system-tier tier_1_critical --frameworks GDPR,CCPA --notification
```

### Timeline Generator
Generate a sample incident timeline:
```bash
python -m src.cli timeline --scenario data_breach --output timeline.txt
```

### Evidence Collection Guide
Display evidence collection priority order:
```bash
python -m src.cli evidence-guide
```

### Severity Matrix Reference
Display the severity classification matrix:
```bash
python -m src.cli severity-matrix
```

---

## Customization

### Adding Custom Scenarios
To create a custom scenario:

1. Create a new file in `src/scenarios/` (e.g., `supply_chain.py`)
2. Define a class with the following interface:
   - `__init__` with scenario metadata (name, title, description, severity, etc.)
   - `get_phases()` returning a list of phase dictionaries
   - `get_max_score()` returning the maximum achievable score
   - `get_scoring_rubric()` returning scoring thresholds
3. Register the scenario in `src/scenarios/__init__.py`

### Modifying Scoring Weights
Edit `src/severity_calculator.py` to adjust the technical vs. business impact weighting:
```python
WEIGHTS = {
    "technical": 0.35,  # Adjust as needed
    "business": 0.65,   # Must sum to 1.0
}
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | Ensure you are running from the project root directory |
| Missing dependencies | Run `pip install -r requirements.txt` |
| Rich output garbled | Ensure terminal supports ANSI color codes; try `--no-color` if needed |
| Simulation hangs on input | Ensure stdin is available (not piped or redirected) |
| Report template errors | Verify the `templates/` directory is in the expected location |
