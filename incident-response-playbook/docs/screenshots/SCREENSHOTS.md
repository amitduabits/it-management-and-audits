# Screenshots

This directory contains screenshots demonstrating the Incident Response Playbook Engine in operation.

## Screenshot Index

### CLI Interface
- `cli_list_scenarios.png` - Output of `list-scenarios` command showing available simulations
- `cli_severity_calc.png` - Severity calculator output with composite scoring
- `cli_evidence_guide.png` - Evidence collection priority order display
- `cli_severity_matrix.png` - Severity classification matrix reference

### Simulation
- `sim_briefing.png` - Scenario briefing with affected systems and IOC table
- `sim_decision_point.png` - Decision point with multiple choice options
- `sim_feedback_correct.png` - Positive feedback for optimal choice (green)
- `sim_feedback_partial.png` - Partial credit feedback (yellow)
- `sim_feedback_incorrect.png` - Negative feedback for suboptimal choice (red)
- `sim_phase_summary.png` - Phase completion score summary
- `sim_final_results.png` - Final simulation results with breakdown

### Reports
- `report_html_header.png` - HTML report header with severity and status
- `report_timeline.png` - Incident timeline visualization
- `report_iocs.png` - Indicators of compromise table
- `report_evidence.png` - Evidence summary section
- `report_severity.png` - Severity assessment score cards

---

*To generate screenshots, run each command and capture the terminal output or open the generated HTML reports in a browser.*

## Generating Screenshots

```bash
# List scenarios
python -m src.cli list-scenarios

# Run severity calculator
python -m src.cli severity --data-class confidential --records 250000 --system-tier tier_1_critical --frameworks GDPR,HIPAA --notification

# Display evidence guide
python -m src.cli evidence-guide

# Display severity matrix
python -m src.cli severity-matrix

# Generate an HTML report and open in browser
python -m src.cli generate-report --scenario data_breach --format html --output reports/demo_report.html
```
