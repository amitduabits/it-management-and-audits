"""
IT Governance Framework Mapper - Gap Analysis Engine

Compares mapped framework controls against total available controls
to identify coverage gaps and calculate compliance percentages.
"""

from collections import defaultdict
from .mapper import load_framework, get_mapped_objectives


def get_all_objectives(framework_name):
    """Get all objectives/practices from a framework, grouped by domain/category.

    Args:
        framework_name: 'cobit' or 'itil'

    Returns:
        dict: {domain_name: [{id, name}, ...]}
    """
    framework = load_framework(framework_name)
    result = {}

    if framework_name == "cobit":
        for domain in framework["domains"]:
            items = []
            for obj in domain["objectives"]:
                items.append({"id": obj["id"], "name": obj["name"]})
            result[domain["id"]] = {
                "name": domain["name"],
                "objectives": items
            }
    elif framework_name == "itil":
        for category in framework["categories"]:
            items = []
            for practice in category["practices"]:
                items.append({"id": practice["id"], "name": practice["name"]})
            result[category["id"]] = {
                "name": category["name"],
                "practices": items
            }

    return result


def analyze_coverage(mappings, framework_name):
    """Analyze coverage of framework controls by mapped processes.

    Args:
        mappings: List of mapping results from the mapper
        framework_name: 'cobit' or 'itil'

    Returns:
        dict: Coverage analysis with domain-level and overall statistics
    """
    all_objectives = get_all_objectives(framework_name)
    mapped_ids = get_mapped_objectives(mappings)

    analysis = {
        "framework": framework_name.upper(),
        "domains": [],
        "summary": {}
    }

    total_controls = 0
    total_covered = 0

    for domain_id, domain_data in all_objectives.items():
        items_key = "objectives" if framework_name == "cobit" else "practices"
        items = domain_data[items_key]

        covered = [item for item in items if item["id"] in mapped_ids]
        uncovered = [item for item in items if item["id"] not in mapped_ids]

        domain_total = len(items)
        domain_covered = len(covered)
        coverage_pct = (domain_covered / domain_total * 100) if domain_total > 0 else 0

        domain_analysis = {
            "domain_id": domain_id,
            "domain_name": domain_data["name"],
            "total": domain_total,
            "covered": domain_covered,
            "uncovered_count": len(uncovered),
            "coverage_percentage": round(coverage_pct, 1),
            "covered_items": [{"id": c["id"], "name": c["name"]} for c in covered],
            "uncovered_items": [{"id": u["id"], "name": u["name"]} for u in uncovered],
            "status": _coverage_status(coverage_pct)
        }

        analysis["domains"].append(domain_analysis)
        total_controls += domain_total
        total_covered += domain_covered

    # Overall summary
    overall_pct = (total_covered / total_controls * 100) if total_controls > 0 else 0
    analysis["summary"] = {
        "total_controls": total_controls,
        "covered_controls": total_covered,
        "uncovered_controls": total_controls - total_covered,
        "overall_coverage_percentage": round(overall_pct, 1),
        "status": _coverage_status(overall_pct)
    }

    return analysis


def _coverage_status(percentage):
    """Determine coverage status based on percentage.

    Args:
        percentage: Coverage percentage (0-100)

    Returns:
        str: Status label
    """
    if percentage >= 80:
        return "Strong"
    elif percentage >= 60:
        return "Moderate"
    elif percentage >= 40:
        return "Partial"
    elif percentage >= 20:
        return "Weak"
    else:
        return "Critical"


def identify_priority_gaps(analysis):
    """Identify the most critical gaps that should be addressed first.

    Prioritizes domains with the lowest coverage percentage and
    returns uncovered controls as priority action items.

    Args:
        analysis: Coverage analysis dict from analyze_coverage()

    Returns:
        list[dict]: Priority gaps sorted by urgency
    """
    gaps = []

    for domain in analysis["domains"]:
        for item in domain["uncovered_items"]:
            priority_score = 100 - domain["coverage_percentage"]
            gaps.append({
                "domain": domain["domain_name"],
                "domain_id": domain["domain_id"],
                "control_id": item["id"],
                "control_name": item["name"],
                "domain_coverage": domain["coverage_percentage"],
                "priority_score": round(priority_score, 1),
                "recommendation": f"Implement or map a process covering {item['name']}"
            })

    # Sort by priority score descending (highest priority first)
    gaps.sort(key=lambda x: x["priority_score"], reverse=True)
    return gaps


def generate_compliance_scorecard(analysis):
    """Generate a compliance scorecard suitable for display.

    Args:
        analysis: Coverage analysis dict

    Returns:
        dict: Scorecard with visual indicators
    """
    scorecard = {
        "framework": analysis["framework"],
        "overall": analysis["summary"],
        "domains": []
    }

    for domain in analysis["domains"]:
        bar_filled = int(domain["coverage_percentage"] / 10)
        bar_empty = 10 - bar_filled
        visual_bar = "█" * bar_filled + "░" * bar_empty

        scorecard["domains"].append({
            "id": domain["domain_id"],
            "name": domain["domain_name"],
            "covered": domain["covered"],
            "total": domain["total"],
            "percentage": domain["coverage_percentage"],
            "visual": visual_bar,
            "status": domain["status"]
        })

    return scorecard
