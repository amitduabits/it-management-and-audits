"""
IT Governance Framework Mapper - Core Mapping Engine

Maps organizational IT processes to COBIT 2019 and ITIL v4 framework
controls using keyword-based matching with confidence scoring.
"""

import json
import os
import re
from collections import defaultdict


# Path to framework data files
FRAMEWORKS_DIR = os.path.join(os.path.dirname(__file__), "frameworks")


def load_framework(framework_name):
    """Load a framework definition from its JSON file.

    Args:
        framework_name: Either 'cobit' or 'itil'

    Returns:
        dict: The parsed framework data

    Raises:
        FileNotFoundError: If the framework file doesn't exist
        ValueError: If the framework name is invalid
    """
    valid = {"cobit", "itil"}
    if framework_name not in valid:
        raise ValueError(f"Unknown framework: {framework_name}. Must be one of {valid}")

    path = os.path.join(FRAMEWORKS_DIR, f"{framework_name}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_org_processes(file_path):
    """Load organizational processes from a JSON file.

    Args:
        file_path: Path to the JSON file containing organization processes

    Returns:
        list[dict]: List of process definitions
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("processes", data) if isinstance(data, dict) else data


def _tokenize(text):
    """Convert text to a set of normalized lowercase tokens."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _compute_match_score(process, control_keywords):
    """Compute a matching score between a process and a set of control keywords.

    The score is based on keyword overlap between the process description,
    name, and tags against the control's keywords.

    Args:
        process: dict with 'name', 'description', and optionally 'tags'
        control_keywords: list of keywords from the framework control

    Returns:
        float: Match score between 0.0 and 1.0
    """
    # Build process token set from name + description + tags
    process_text = " ".join([
        process.get("name", ""),
        process.get("description", ""),
        " ".join(process.get("tags", []))
    ])
    process_tokens = _tokenize(process_text)

    # Normalize control keywords
    control_tokens = set()
    for kw in control_keywords:
        control_tokens.update(_tokenize(kw))

    if not control_tokens:
        return 0.0

    # Calculate overlap ratio
    overlap = process_tokens & control_tokens
    if not overlap:
        return 0.0

    # Score is the proportion of control keywords matched, weighted by
    # how many process tokens also matched (to penalize overly broad matches)
    keyword_coverage = len(overlap) / len(control_tokens)
    process_relevance = len(overlap) / len(process_tokens) if process_tokens else 0

    # Combined score: weighted average favoring keyword coverage
    score = (keyword_coverage * 0.7) + (process_relevance * 0.3)
    return round(min(score, 1.0), 3)


def map_to_cobit(processes, threshold=0.15):
    """Map organizational processes to COBIT 2019 objectives.

    Args:
        processes: List of organization process dicts
        threshold: Minimum match score to consider a mapping (default 0.15)

    Returns:
        list[dict]: List of mappings with process, objective, and score
    """
    framework = load_framework("cobit")
    mappings = []

    for process in processes:
        process_mappings = []
        for domain in framework["domains"]:
            for objective in domain["objectives"]:
                score = _compute_match_score(process, objective["keywords"])
                if score >= threshold:
                    process_mappings.append({
                        "process_id": process.get("id", ""),
                        "process_name": process.get("name", ""),
                        "framework": "COBIT 2019",
                        "domain": domain["id"],
                        "domain_name": domain["name"],
                        "objective_id": objective["id"],
                        "objective_name": objective["name"],
                        "confidence_score": score
                    })

        # Sort by score descending, keep top matches
        process_mappings.sort(key=lambda x: x["confidence_score"], reverse=True)
        mappings.extend(process_mappings[:5])  # Top 5 matches per process

    return mappings


def map_to_itil(processes, threshold=0.15):
    """Map organizational processes to ITIL v4 practices.

    Args:
        processes: List of organization process dicts
        threshold: Minimum match score to consider a mapping (default 0.15)

    Returns:
        list[dict]: List of mappings with process, practice, and score
    """
    framework = load_framework("itil")
    mappings = []

    for process in processes:
        process_mappings = []
        for category in framework["categories"]:
            for practice in category["practices"]:
                score = _compute_match_score(process, practice["keywords"])
                if score >= threshold:
                    process_mappings.append({
                        "process_id": process.get("id", ""),
                        "process_name": process.get("name", ""),
                        "framework": "ITIL v4",
                        "category": category["name"],
                        "practice_id": practice["id"],
                        "practice_name": practice["name"],
                        "confidence_score": score
                    })

        process_mappings.sort(key=lambda x: x["confidence_score"], reverse=True)
        mappings.extend(process_mappings[:5])

    return mappings


def map_processes(processes, framework="all", threshold=0.15):
    """Map processes to one or both frameworks.

    Args:
        processes: List of organization process dicts
        framework: 'cobit', 'itil', or 'all'
        threshold: Minimum match score

    Returns:
        dict: Mapping results keyed by framework name
    """
    results = {}

    if framework in ("cobit", "all"):
        results["cobit"] = map_to_cobit(processes, threshold)

    if framework in ("itil", "all"):
        results["itil"] = map_to_itil(processes, threshold)

    return results


def get_mapped_objectives(mappings):
    """Extract unique framework objective/practice IDs from mappings.

    Args:
        mappings: List of mapping dicts

    Returns:
        set: Set of objective/practice IDs
    """
    ids = set()
    for m in mappings:
        obj_id = m.get("objective_id") or m.get("practice_id")
        if obj_id:
            ids.add(obj_id)
    return ids


def get_mapping_summary(mappings):
    """Generate a summary of mappings grouped by process.

    Args:
        mappings: List of mapping dicts

    Returns:
        dict: Summary keyed by process name
    """
    summary = defaultdict(list)
    for m in mappings:
        key = m["process_name"]
        target = m.get("objective_name") or m.get("practice_name")
        summary[key].append({
            "target": target,
            "id": m.get("objective_id") or m.get("practice_id"),
            "score": m["confidence_score"]
        })
    return dict(summary)
