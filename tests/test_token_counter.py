"""Unit tests for token counter heuristics and savings analytics."""

import unittest
from tokentrim.token_counter import estimate_tokens, compute_savings


class TestTokenCounter(unittest.TestCase):
    def test_estimate_empty(self):
        self.assertEqual(estimate_tokens(""), 0)
        self.assertEqual(estimate_tokens("   "), 1)

    def test_estimate_basic_code(self):
        code = "def hello_world():\n    return 'hello world'\n"
        tokens = estimate_tokens(code)
        self.assertGreater(tokens, 5)
        self.assertLess(tokens, 20)

    def test_savings_computation(self):
        original = """
def process_data(items: list[int]) -> list[int]:
    # This is a very long function implementation
    result = []
    for item in items:
        processed = item * 2 + 10
        if processed > 100:
            result.append(processed)
        else:
            result.append(0)
    return result
"""
        trimmed = """
def process_data(items: list[int]) -> list[int]:
    ...
"""
        savings = compute_savings(original, trimmed)
        self.assertGreater(savings.original_lines, savings.trimmed_lines)
        self.assertGreater(savings.original_tokens, savings.trimmed_tokens)
        self.assertGreater(savings.token_reduction_pct, 50.0)
        self.assertGreater(savings.estimated_usd_saved(), 0.0)


if __name__ == "__main__":
    unittest.main()
