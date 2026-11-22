import sys
import os
from pathlib import Path

# Ensure backend is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.services.query_intelligence import query_intelligence
from app.services.safety_service import safety_service

def run_hard_queries_test():
    print("=" * 70)
    print("FrameFlow AI - Hard Query & Semantic Disambiguation Test Suite")
    print("=" * 70)

    test_cases = [
        {
            "category": "Homonym (Financial Bank)",
            "phrase": "The customer deposited cash into the savings bank account.",
            "expected_terms": ["financial", "bank", "corporate", "banking"],
            "forbidden_terms": ["river", "stream", "shore"]
        },
        {
            "category": "Homonym (River Shoreline)",
            "phrase": "Lush wildflowers grew along the peaceful river bank.",
            "expected_terms": ["river", "nature", "water", "stream"],
            "forbidden_terms": ["financial", "money", "deposit"]
        },
        {
            "category": "Homonym (Tech Cloud)",
            "phrase": "The company migrated critical infrastructure to the AWS cloud.",
            "expected_terms": ["server", "technology", "data", "center"],
            "forbidden_terms": ["sky", "weather", "cumulus"]
        },
        {
            "category": "Homonym (Computer Mouse)",
            "phrase": "The designer gripped the ergonomic wireless mouse to click the button.",
            "expected_terms": ["mouse", "desk", "computer", "office"],
            "forbidden_terms": ["rodent", "field", "wildlife"]
        },
        {
            "category": "Homonym (Python Code)",
            "phrase": "The engineer wrote a python programming script for data science.",
            "expected_terms": ["developer", "coding", "software", "programming"],
            "forbidden_terms": ["snake", "reptile", "canopy"]
        },
        {
            "category": "Abstract Metaphor (Inflation)",
            "phrase": "Families struggle with soaring inflation and shrinking budgets.",
            "expected_terms": ["supermarket", "prices", "grocery", "wallet", "cash"],
            "forbidden_terms": ["abstract", "inflation"]
        },
        {
            "category": "Abstract Metaphor (Midnight Oil)",
            "phrase": "The team was burning the midnight oil before the product launch.",
            "expected_terms": ["desk", "lamp", "office", "worker"],
            "forbidden_terms": ["oil", "flame", "burning"]
        },
        {
            "category": "Entity Safety Stand-in (Real Person)",
            "phrase": "Elon Musk gave a keynote speech at the tech conference.",
            "expected_terms": ["tech", "entrepreneur", "executive", "presentation"],
            "forbidden_terms": ["elon", "musk"]
        }
    ]

    all_passed = True
    for idx, tc in enumerate(test_cases, 1):
        phrase = tc["phrase"]
        if "Entity Safety" in tc["category"]:
            query = safety_service.sanitize_text_query(phrase).lower()
        else:
            query = query_intelligence.disambiguate_query(phrase).lower()

        matched_expected = [term for term in tc["expected_terms"] if term in query]
        matched_forbidden = [term for term in tc["forbidden_terms"] if term in query]

        passed = len(matched_expected) > 0 and len(matched_forbidden) == 0
        if not passed:
            all_passed = False

        status = "PASSED" if passed else "FAILED"
        print(f"[{status}] Test {idx}: {tc['category']}")
        print(f"   Input: \"{phrase}\"")
        print(f"   Generated Query: \"{query}\"")
        if matched_expected:
            print(f"   Matched Expected: {matched_expected}")
        if matched_forbidden:
            print(f"   FORBIDDEN TERM DETECTED: {matched_forbidden}")
        print("-" * 70)

    if all_passed:
        print("\nALL HARD QUERY DISAMBIGUATION TESTS PASSED (100% Accuracy)")
        return 0
    else:
        print("\nSOME HARD QUERY TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(run_hard_queries_test())
