"""Unit tests for the gap analysis engine."""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.mapper import map_to_cobit, map_to_itil
from src.analyzer import (
    get_all_objectives,
    analyze_coverage,
    identify_priority_gaps,
    generate_compliance_scorecard,
    _coverage_status,
)


class TestCoverageStatus(unittest.TestCase):
    def test_strong(self):
        self.assertEqual(_coverage_status(85), "Strong")

    def test_moderate(self):
        self.assertEqual(_coverage_status(65), "Moderate")

    def test_partial(self):
        self.assertEqual(_coverage_status(45), "Partial")

    def test_weak(self):
        self.assertEqual(_coverage_status(25), "Weak")

    def test_critical(self):
        self.assertEqual(_coverage_status(10), "Critical")

    def test_boundary_80(self):
        self.assertEqual(_coverage_status(80), "Strong")


class TestGetAllObjectives(unittest.TestCase):
    def test_cobit_domains(self):
        objectives = get_all_objectives("cobit")
        self.assertIn("EDM", objectives)
        self.assertIn("APO", objectives)
        self.assertIn("BAI", objectives)
        self.assertIn("DSS", objectives)
        self.assertIn("MEA", objectives)

    def test_cobit_objective_count(self):
        objectives = get_all_objectives("cobit")
        total = sum(len(d["objectives"]) for d in objectives.values())
        self.assertEqual(total, 40)

    def test_itil_categories(self):
        practices = get_all_objectives("itil")
        self.assertIn("general", practices)
        self.assertIn("service", practices)
        self.assertIn("technical", practices)

    def test_itil_practice_count(self):
        practices = get_all_objectives("itil")
        total = sum(len(c["practices"]) for c in practices.values())
        self.assertEqual(total, 34)


class TestAnalyzeCoverage(unittest.TestCase):
    def setUp(self):
        self.processes = [
            {
                "id": "T1",
                "name": "Security Management",
                "description": "ISMS and cybersecurity policy management",
                "tags": ["security", "ISMS", "cybersecurity"]
            },
            {
                "id": "T2",
                "name": "Incident Response",
                "description": "Incident detection, triage, and resolution with SLA tracking",
                "tags": ["incident", "service desk", "SLA"]
            }
        ]

    def test_cobit_analysis_structure(self):
        mappings = map_to_cobit(self.processes)
        analysis = analyze_coverage(mappings, "cobit")

        self.assertIn("framework", analysis)
        self.assertIn("domains", analysis)
        self.assertIn("summary", analysis)
        self.assertEqual(analysis["framework"], "COBIT")

    def test_coverage_percentages_valid(self):
        mappings = map_to_cobit(self.processes)
        analysis = analyze_coverage(mappings, "cobit")

        for domain in analysis["domains"]:
            self.assertGreaterEqual(domain["coverage_percentage"], 0)
            self.assertLessEqual(domain["coverage_percentage"], 100)

    def test_summary_totals(self):
        mappings = map_to_cobit(self.processes)
        analysis = analyze_coverage(mappings, "cobit")
        summary = analysis["summary"]

        self.assertEqual(
            summary["covered_controls"] + summary["uncovered_controls"],
            summary["total_controls"]
        )

    def test_itil_analysis(self):
        mappings = map_to_itil(self.processes)
        analysis = analyze_coverage(mappings, "itil")
        self.assertEqual(analysis["framework"], "ITIL")


class TestPriorityGaps(unittest.TestCase):
    def test_gaps_sorted_by_priority(self):
        processes = [
            {
                "id": "T1",
                "name": "Security",
                "description": "Security management",
                "tags": ["security"]
            }
        ]
        mappings = map_to_cobit(processes)
        analysis = analyze_coverage(mappings, "cobit")
        gaps = identify_priority_gaps(analysis)

        self.assertGreater(len(gaps), 0)
        # Verify sorted descending by priority score
        for i in range(len(gaps) - 1):
            self.assertGreaterEqual(gaps[i]["priority_score"], gaps[i + 1]["priority_score"])

    def test_gap_structure(self):
        processes = [{"id": "T1", "name": "Test", "description": "Test", "tags": []}]
        mappings = map_to_cobit(processes)
        analysis = analyze_coverage(mappings, "cobit")
        gaps = identify_priority_gaps(analysis)

        if gaps:
            gap = gaps[0]
            self.assertIn("domain", gap)
            self.assertIn("control_id", gap)
            self.assertIn("control_name", gap)
            self.assertIn("priority_score", gap)
            self.assertIn("recommendation", gap)


class TestComplianceScorecard(unittest.TestCase):
    def test_scorecard_structure(self):
        processes = [
            {"id": "T1", "name": "Security", "description": "Security ISMS", "tags": ["security"]}
        ]
        mappings = map_to_cobit(processes)
        analysis = analyze_coverage(mappings, "cobit")
        scorecard = generate_compliance_scorecard(analysis)

        self.assertIn("framework", scorecard)
        self.assertIn("overall", scorecard)
        self.assertIn("domains", scorecard)

    def test_scorecard_visual_bars(self):
        processes = [
            {"id": "T1", "name": "Security", "description": "Security ISMS", "tags": ["security"]}
        ]
        mappings = map_to_cobit(processes)
        analysis = analyze_coverage(mappings, "cobit")
        scorecard = generate_compliance_scorecard(analysis)

        for domain in scorecard["domains"]:
            self.assertEqual(len(domain["visual"]), 10)
            self.assertIn("status", domain)


if __name__ == "__main__":
    unittest.main()
