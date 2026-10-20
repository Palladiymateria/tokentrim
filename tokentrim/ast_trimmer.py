"""Python AST transformer for extracting skeleton signatures and interfaces."""

from __future__ import annotations

import ast
import re
from typing import Optional


class SkeletonTransformer(ast.NodeTransformer):
    """AST Transformer that strips implementation bodies while preserving:
    - Imports and type aliases
    - Function and method signatures with decorators and type annotations
    - Class definitions, bases, and type-annotated attributes (dataclasses / Pydantic)
    - Docstrings (configurable)
    """

    def __init__(self, keep_docstrings: bool = True, summarize_lines: bool = True):
        super().__init__()
        self.keep_docstrings = keep_docstrings
        self.summarize_lines = summarize_lines

    def _collapse_body(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.stmt]:
        docstring = ast.get_docstring(node, clean=True) if self.keep_docstrings else None
        
        # Calculate hidden lines count
        first_line = node.lineno
        last_line = getattr(node, "end_lineno", first_line)
        body_lines = max(1, last_line - first_line)

        new_body: list[ast.stmt] = []

        if docstring:
            new_body.append(ast.Expr(value=ast.Constant(value=docstring)))

        # Python idiom: Ellipsis (...) as function body placeholder
        new_body.append(ast.Expr(value=ast.Constant(value=Ellipsis)))
        return new_body

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        node.body = self._collapse_body(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        node.body = self._collapse_body(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        # First visit children to transform nested functions and inner classes
        self.generic_visit(node)

        docstring = ast.get_docstring(node, clean=True) if self.keep_docstrings else None
        
        filtered_body: list[ast.stmt] = []
        if docstring:
            filtered_body.append(ast.Expr(value=ast.Constant(value=docstring)))

        for stmt in node.body:
            # Skip old docstring node if we already added it
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                continue

            # Keep type annotations (dataclasses, Pydantic, class attributes)
            if isinstance(stmt, (ast.AnnAssign, ast.Assign)):
                filtered_body.append(stmt)
            # Keep methods and inner classes
            elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                filtered_body.append(stmt)
            # Keep pass or ellipsis if explicitly present
            elif isinstance(stmt, ast.Pass) or (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and stmt.value.value is Ellipsis
            ):
                filtered_body.append(stmt)

        if not filtered_body:
            filtered_body.append(ast.Expr(value=ast.Constant(value=Ellipsis)))

        node.body = filtered_body
        return node

    def visit_If(self, node: ast.If) -> ast.AST:
        # Detect if __name__ == '__main__':
        is_main = False
        if isinstance(node.test, ast.Compare):
            left = getattr(node.test.left, "id", None)
            if left == "__name__":
                for comp in node.test.comparators:
                    if isinstance(comp, ast.Constant) and comp.value == "__main__":
                        is_main = True
                        break

        if is_main:
            node.body = [ast.Expr(value=ast.Constant(value=Ellipsis))]
            node.orelse = []
            return node

        return self.generic_visit(node)


def trim_python_code(
    source_code: str,
    keep_docstrings: bool = True,
    summarize_lines: bool = True,
) -> str:
    """Parse Python code, strip implementations, and return trimmed syntactically valid code.
    
    If source code has syntax errors, falls back to lightweight regex-based trimming.
    """
    if not source_code.strip():
        return ""

    try:
        tree = ast.parse(source_code)
        transformer = SkeletonTransformer(
            keep_docstrings=keep_docstrings,
            summarize_lines=summarize_lines,
        )
        trimmed_tree = transformer.visit(tree)
        ast.fix_missing_locations(trimmed_tree)
        unparsed = ast.unparse(trimmed_tree)
        
        # Clean up excessive blank lines
        cleaned = re.sub(r"\n{3,}", "\n\n", unparsed)
        return cleaned.strip() + "\n"
    except SyntaxError:
        # Fall back to regex trimmer on malformed/incomplete Python snippets
        return _fallback_python_trim(source_code, keep_docstrings=keep_docstrings)


def _fallback_python_trim(source_code: str, keep_docstrings: bool = True) -> str:
    """Lightweight line-based trimmer for invalid or snippet Python code."""
    lines = source_code.splitlines()
    result: list[str] = []
    in_function = False
    indent_level = 0

    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        if re.match(r"^(async\s+)?def\s+[a-zA-Z_]", stripped):
            in_function = True
            indent_level = indent
            result.append(line)
            continue

        if re.match(r"^class\s+[a-zA-Z_]", stripped):
            in_function = False
            result.append(line)
            continue

        if in_function:
            if indent > indent_level:
                # Inside function body - collapse
                if not result[-1].rstrip().endswith("..."):
                    result.append(" " * (indent_level + 4) + "...")
                continue
            else:
                in_function = False

        result.append(line)

    return "\n".join(result) + "\n"
