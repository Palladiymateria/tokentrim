"""Unit tests for tokentrim CLI."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tokentrim.cli import main


class TestCli(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        # Create sample files
        self.py_file = self.dir_path / "sample.py"
        self.py_file.write_text(
            'def add(a: int, b: int) -> int:\n    """Add two numbers."""\n    return a + b\n',
            encoding="utf-8",
        )

        self.ts_file = self.dir_path / "sample.ts"
        self.ts_file.write_text(
            "export function multiply(a: number, b: number): number {\n  return a * b;\n}\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_single_file_json(self):
        with patch("sys.stdout.write"):
            with patch("builtins.print") as mock_print:
                code = main([str(self.py_file), "--json"])
                self.assertEqual(code, 0)
                # Find the call with valid json
                json_called = False
                for call_args in mock_print.call_args_list:
                    arg = call_args[0][0]
                    if isinstance(arg, str) and '"original_tokens"' in arg:
                        data = json.loads(arg)
                        self.assertIn("tokens_saved_percent", data)
                        self.assertIn("content", data)
                        json_called = True
                        break
                self.assertTrue(json_called)

    def test_output_file_flag(self):
        out_file = self.dir_path / "out.py"
        code = main([str(self.py_file), "-o", str(out_file)])
        self.assertEqual(code, 0)
        self.assertTrue(out_file.exists())
        content = out_file.read_text(encoding="utf-8")
        self.assertIn("def add(a: int, b: int) -> int:", content)
        self.assertIn("...", content)
        self.assertNotIn("return a + b", content)

    def test_directory_bundle_json(self):
        with patch("builtins.print") as mock_print:
            code = main([str(self.dir_path), "--json"])
            self.assertEqual(code, 0)
            json_called = False
            for call_args in mock_print.call_args_list:
                arg = call_args[0][0]
                if isinstance(arg, str) and '"bundle"' in arg:
                    data = json.loads(arg)
                    self.assertEqual(data["files_count"], 2)
                    self.assertIn("sample.py", data["bundle"])
                    self.assertIn("sample.ts", data["bundle"])
                    json_called = True
                    break
            self.assertTrue(json_called)

    def test_invalid_path(self):
        code = main(["non_existent_path_xyz_12345"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
