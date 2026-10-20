"""Unit tests for Python AST trimmer."""

import ast
import unittest
from tokentrim.ast_trimmer import trim_python_code


class TestAstTrimmer(unittest.TestCase):
    def test_basic_function_collapse(self):
        source = """
def calculate_metrics(data: list[int], factor: float = 1.0) -> dict[str, float]:
    total = sum(data)
    mean = total / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    return {"mean": mean * factor, "variance": variance}
"""
        trimmed = trim_python_code(source)
        self.assertIn("def calculate_metrics(data: list[int], factor: float=1.0) -> dict[str, float]:", trimmed)
        self.assertIn("...", trimmed)
        self.assertNotIn("variance = sum", trimmed)
        # Check that output is valid Python code!
        parsed = ast.parse(trimmed)
        self.assertIsNotNone(parsed)

    def test_docstring_preservation(self):
        source = '''
def process_user(user_id: int) -> bool:
    """Fetch user from database and check permissions."""
    print("doing heavy work")
    return True
'''
        trimmed = trim_python_code(source, keep_docstrings=True)
        self.assertIn('"""Fetch user from database and check permissions."""', trimmed)
        self.assertIn("...", trimmed)
        self.assertNotIn('print("doing heavy work")', trimmed)

        trimmed_no_doc = trim_python_code(source, keep_docstrings=False)
        self.assertNotIn("Fetch user from database", trimmed_no_doc)
        self.assertIn("...", trimmed_no_doc)

    def test_class_and_dataclass_annotations(self):
        source = """
from dataclasses import dataclass

@dataclass
class UserProfile:
    \"\"\"User profile model.\"\"\"
    user_id: int
    username: str
    is_active: bool = True

    def validate(self) -> bool:
        if len(self.username) < 3:
            raise ValueError("Username too short")
        return True
"""
        trimmed = trim_python_code(source)
        self.assertIn("class UserProfile:", trimmed)
        self.assertIn("user_id: int", trimmed)
        self.assertIn("username: str", trimmed)
        self.assertIn("is_active: bool = True", trimmed)
        self.assertIn("def validate(self) -> bool:", trimmed)
        self.assertNotIn("raise ValueError", trimmed)
        # Syntactic validity
        self.assertIsNotNone(ast.parse(trimmed))

    def test_async_functions(self):
        source = """
async def fetch_remote_data(url: str, timeout: int = 30) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=timeout) as resp:
            return await resp.read()
"""
        trimmed = trim_python_code(source)
        self.assertIn("async def fetch_remote_data(url: str, timeout: int=30) -> bytes:", trimmed)
        self.assertIn("...", trimmed)
        self.assertNotIn("aiohttp.ClientSession", trimmed)
        self.assertIsNotNone(ast.parse(trimmed))

    def test_main_block_collapse(self):
        source = """
def main():
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main()
"""
        trimmed = trim_python_code(source)
        self.assertIn("if __name__ == '__main__':", trimmed)
        self.assertNotIn("argparse.ArgumentParser", trimmed)
        self.assertIsNotNone(ast.parse(trimmed))

    def test_syntax_error_fallback(self):
        # Incomplete snippet with syntax error
        source = "def broken(x):\n    print('test'\n"
        trimmed = trim_python_code(source)
        self.assertIn("def broken(x):", trimmed)


if __name__ == "__main__":
    unittest.main()
