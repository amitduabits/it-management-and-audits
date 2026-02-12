"""Unit tests for the mapping engine."""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.mapper import (
    load_framework,
    load_org_processes,
    map_to_cobit,
    map_to_itil,
    map_processes,
    get_mapped_objectives,
    get_mapping_summary,
    _tokenize,
    _compute_match_score,
)


class TestTokenize(unittest.TestCase):
    def test_basic_tokenization(self):
        tokens = _tokenize("Hello World 123")
        self.assertEqual(tokens, {"hello", "world", "123"})

    def test_special_characters_removed(self):
        tokens = _tokenize("IT-Security & Risk Management!")
        self.assertIn("it", tokens)
        self.assertIn("security", tokens)
        self.assertIn("risk", tokens)

    def test_empty_string(self):
        self.assertEqual(_tokenize(""), set())


class TestComputeMatchScore(unittest.TestCase):
    def test_perfect_match_keywords(self):
        process = {
            "name": "Security Management",
            "description": "Manage information security policies and cybersecurity",
            "tags": ["security", "ISMS"]
        }
        keywords = ["security", "information security", "ISMS", "cybersecurity"]
        score = _compute_match_score(process, keywords)
        self.assertGreater(score, 0.3)

    def test_no_match(self):
        process = {
            "name": "Budget Planning",
            "description": "Plan and allocate financial budgets",
            "tags": ["budget", "finance"]
        }
        keywords = ["deployment", "release", "CI/CD", "pipeline"]
        score = _compute_match_score(process, keywords)
        self.assertEqual(score, 0.0)

    def test_partial_match(self):
        process = {
            "name": "Vendor Management",
            "description": "Evaluate and monitor technology vendors",
            "tags": ["vendor", "procurement"]
        }
        keywords = ["vendor", "supplier", "procurement", "contract", "third party"]
        score = _compute_match_score(process, keywords)
        self.assertGreater(score, 0.1)

    def test_empty_keywords(self):
        process = {"name": "Test", "description": "Test process"}
        score = _compute_match_score(process, [])
        self.assertEqual(score, 0.0)


class TestLoadFramework(unittest.TestCase):
    def test_load_cobit(self):
        fw = load_framework("cobit")
        self.assertEqual(fw["framework"], "COBIT 2019")
        self.assertEqual(len(fw["domains"]), 5)

    def test_load_itil(self):
        fw = load_framework("itil")
        self.assertEqual(fw["framework"], "ITIL v4")
        self.assertEqual(len(fw["categories"]), 3)

    def test_invalid_framework(self):
        with self.assertRaises(ValueError):
            load_framework("invalid")

    def test_cobit_has_objectives(self):
        fw = load_framework("cobit")
        for domain in fw["domains"]:
            self.assertGreater(len(domain["objectives"]), 0)
            for obj in domain["objectives"]:
                self.assertIn("id", obj)
                self.assertIn("name", obj)
                self.assertIn("keywords", obj)


class TestMapping(unittest.TestCase):
    def setUp(self):
        self.sample_processes = [
            {
                "id": "TEST-001",
                "name": "Information Security Program",
                "description": "Manage the ISMS, security policies, and cybersecurity operations",
                "tags": ["security", "ISMS", "cybersecurity", "policy"]
            },
            {
                "id": "TEST-002",
                "name": "Change Control Process",
                "description": "Manage all IT changes through CAB review and approval",
                "tags": ["change", "CAB", "change control", "release"]
            }
        ]

    def test_map_to_cobit_returns_results(self):
        mappings = map_to_cobit(self.sample_processes)
        self.assertIsInstance(mappings, list)
        self.assertGreater(len(mappings), 0)

    def test_map_to_itil_returns_results(self):
        mappings = map_to_itil(self.sample_processes)
        self.assertIsInstance(mappings, list)
        self.assertGreater(len(mappings), 0)

    def test_mapping_structure(self):
        mappings = map_to_cobit(self.sample_processes)
        for m in mappings:
            self.assertIn("process_name", m)
            self.assertIn("objective_id", m)
            self.assertIn("confidence_score", m)
            self.assertGreaterEqual(m["confidence_score"], 0)
            self.assertLessEqual(m["confidence_score"], 1)

    def test_map_processes_all(self):
        results = map_processes(self.sample_processes, "all")
        self.assertIn("cobit", results)
        self.assertIn("itil", results)

    def test_security_process_maps_to_security_controls(self):
        mappings = map_to_cobit(self.sample_processes)
        security_mappings = [m for m in mappings if m["process_name"] == "Information Security Program"]
        objective_ids = [m["objective_id"] for m in security_mappings]
        self.assertIn("APO13", objective_ids)


class TestMappedObjectives(unittest.TestCase):
    def test_get_mapped_objectives(self):
        mappings = [
            {"objective_id": "APO13", "process_name": "Test"},
            {"objective_id": "APO12", "process_name": "Test"},
            {"objective_id": "APO13", "process_name": "Test2"},
        ]
        ids = get_mapped_objectives(mappings)
        self.assertEqual(ids, {"APO13", "APO12"})

    def test_get_mapping_summary(self):
        mappings = [
            {"process_name": "Security", "objective_name": "Managed Security", "objective_id": "APO13", "confidence_score": 0.8},
            {"process_name": "Security", "objective_name": "Managed Risk", "objective_id": "APO12", "confidence_score": 0.5},
        ]
        summary = get_mapping_summary(mappings)
        self.assertIn("Security", summary)
        self.assertEqual(len(summary["Security"]), 2)


if __name__ == "__main__":
    unittest.main()
