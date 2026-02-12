# Usage Guide

## Getting Started

### 1. Prepare Your Process Data

Create a JSON file describing your organization's IT processes. Each process needs:

```json
{
  "processes": [
    {
      "id": "PROC-001",
      "name": "Process Name",
      "description": "Detailed description of what the process covers",
      "tags": ["keyword1", "keyword2", "keyword3"]
    }
  ]
}
```

**Tips for better mapping accuracy:**
- Use descriptive names that match industry terminology
- Include detailed descriptions covering all aspects of the process
- Add relevant tags using standard ITSM terms
- Be specific — "Change Advisory Board Process" maps better than "Review Process"

### 2. Run Mapping

```bash
# Basic mapping against both frameworks
python src/cli.py map -i your_processes.json -f all

# Map against COBIT only with higher threshold
python src/cli.py map -i your_processes.json -f cobit -t 0.25
```

### 3. Analyze Gaps

```bash
# COBIT gap analysis with priority gaps
python src/cli.py analyze -i your_processes.json -f cobit -g

# ITIL gap analysis
python src/cli.py analyze -i your_processes.json -f itil -g
```

### 4. Generate Reports

```bash
# Terminal report
python src/cli.py report -i your_processes.json -f cobit --format terminal

# HTML report
python src/cli.py report -i your_processes.json -f cobit --format html -o my_report.html
```

---

## Understanding Match Scores

| Score Range | Meaning | Recommendation |
|-------------|---------|----------------|
| 0.70 – 1.00 | Strong match | Process clearly covers this control |
| 0.40 – 0.69 | Moderate match | Process partially covers this control |
| 0.15 – 0.39 | Weak match | Some overlap; review if truly applicable |
| Below 0.15 | No match | Not mapped (below threshold) |

---

## Understanding Coverage Status

| Status | Coverage % | Meaning |
|--------|------------|---------|
| Strong | 80%+ | Most controls are addressed |
| Moderate | 60-79% | Good coverage with some gaps |
| Partial | 40-59% | Significant gaps exist |
| Weak | 20-39% | Major coverage deficiency |
| Critical | Below 20% | Domain is largely unaddressed |

---

## Customizing the Analysis

### Adjusting the Threshold

The `--threshold` flag controls how strict the matching is:

- **Lower threshold (0.10):** More matches, includes weaker connections. Good for initial broad assessment.
- **Default threshold (0.15):** Balanced — catches meaningful connections without too much noise.
- **Higher threshold (0.25+):** Only strong matches. Good for final reporting where confidence matters.

### Adding Custom Processes

Simply add more entries to your JSON file. The mapper automatically evaluates all processes against all framework controls.

---

## Sample Walkthrough

Using the included sample data for PayFlow Digital:

```bash
# Step 1: View available processes
python -c "import json; d=json.load(open('data/sample_org_processes.json')); [print(f'{p[\"id\"]}: {p[\"name\"]}') for p in d['processes']]"

# Step 2: Map to COBIT
python src/cli.py map -i data/sample_org_processes.json -f cobit

# Step 3: Analyze COBIT coverage
python src/cli.py analyze -i data/sample_org_processes.json -f cobit -g

# Step 4: Generate HTML report
python src/cli.py report -i data/sample_org_processes.json -f cobit --format html -o reports/payflow_cobit.html
```
