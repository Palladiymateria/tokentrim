"""Lightweight, zero-dependency skeleton trimmer for TypeScript, JavaScript, Go, and Rust."""

from __future__ import annotations

import re


def trim_polyglot_code(source_code: str, extension: str, keep_docstrings: bool = True) -> str:
    """Trim function and method bodies for TypeScript, JavaScript, Go, and Rust."""
    ext = extension.lower().lstrip(".")
    if ext in ("ts", "tsx", "js", "jsx", "mjs", "cjs"):
        return _trim_js_ts(source_code, keep_docstrings=keep_docstrings)
    elif ext == "go":
        return _trim_go(source_code)
    elif ext == "rs":
        return _trim_rust(source_code)
    else:
        # Default fallback: return as-is or strip empty lines
        return source_code


def _trim_js_ts(code: str, keep_docstrings: bool = True) -> str:
    """Trim JS/TS code: keeps imports, interfaces, type aliases, and signatures while collapsing bodies."""
    lines = code.splitlines()
    result: list[str] = []
    
    in_block_comment = False
    brace_depth = 0
    in_function_body = False
    func_body_start_depth = 0

    # Patterns indicating interface or type definition where body should be preserved
    interface_pattern = re.compile(r"^\s*(export\s+)?(interface|type|enum)\s+[A-Za-z0-9_]")
    # Pattern indicating function/method declaration
    func_pattern = re.compile(
        r"(function\b|\bconst\s+[A-Za-z0-9_]+\s*=\s*\(|=>\s*\{|\b(public|private|protected|async|static|\*)*\s*[A-Za-z0-9_]+\s*\([^)]*\)\s*(\:\s*[^\{]+)?\s*\{)"
    )

    is_interface_context = False

    for line in lines:
        trimmed = line.strip()

        # Handle comments
        if trimmed.startswith("/*") and not trimmed.endswith("*/"):
            in_block_comment = True
            if keep_docstrings and ("/**" in trimmed):
                result.append(line)
            continue

        if in_block_comment:
            if "*/" in trimmed:
                in_block_comment = False
            if keep_docstrings:
                result.append(line)
            continue

        if interface_pattern.match(trimmed):
            is_interface_context = True

        # Count open and close braces
        opens = line.count("{")
        closes = line.count("}")

        if not in_function_body:
            if not is_interface_context and opens > 0 and func_pattern.search(line):
                # Function declaration starting on this line
                in_function_body = True
                func_body_start_depth = brace_depth

                # Reconstruct signature line with collapsed placeholder
                prefix = line[: line.rfind("{") + 1]
                result.append(prefix + " /* ... */ }")
                brace_depth += (opens - closes)
                if brace_depth <= func_body_start_depth:
                    in_function_body = False
                continue
            else:
                result.append(line)
        else:
            # We are inside a function body being trimmed
            brace_depth += (opens - closes)
            if brace_depth <= func_body_start_depth:
                in_function_body = False
            continue

        brace_depth += (opens - closes)
        if is_interface_context and brace_depth == 0:
            is_interface_context = False

    return _clean_blank_lines("\n".join(result))


def _trim_go(code: str) -> str:
    """Trim Go code: preserves package, imports, structs, interfaces, collapses func bodies."""
    lines = code.splitlines()
    result: list[str] = []
    
    in_func = False
    brace_depth = 0
    func_start_depth = 0
    func_pattern = re.compile(r"^\s*func\s+.*\{")

    for line in lines:
        opens = line.count("{")
        closes = line.count("}")

        if not in_func:
            if func_pattern.search(line):
                in_func = True
                func_start_depth = brace_depth
                prefix = line[: line.rfind("{") + 1]
                result.append(prefix + " /* ... */ }")
                brace_depth += (opens - closes)
                if brace_depth <= func_start_depth:
                    in_func = False
                continue
            result.append(line)
        else:
            brace_depth += (opens - closes)
            if brace_depth <= func_start_depth:
                in_func = False
            continue

        brace_depth += (opens - closes)

    return _clean_blank_lines("\n".join(result))


def _trim_rust(code: str) -> str:
    """Trim Rust code: preserves traits, structs, enums, impl headers, collapses fn bodies."""
    lines = code.splitlines()
    result: list[str] = []
    
    in_fn = False
    brace_depth = 0
    fn_start_depth = 0
    fn_pattern = re.compile(r"^\s*(pub(\(crate\))?\s+)?(async\s+)?(unsafe\s+)?fn\s+.*\{")

    for line in lines:
        opens = line.count("{")
        closes = line.count("}")

        if not in_fn:
            if fn_pattern.search(line):
                in_fn = True
                fn_start_depth = brace_depth
                prefix = line[: line.rfind("{") + 1]
                result.append(prefix + " /* ... */ }")
                brace_depth += (opens - closes)
                if brace_depth <= fn_start_depth:
                    in_fn = False
                continue
            result.append(line)
        else:
            brace_depth += (opens - closes)
            if brace_depth <= fn_start_depth:
                in_fn = False
            continue

        brace_depth += (opens - closes)

    return _clean_blank_lines("\n".join(result))


def _clean_blank_lines(text: str) -> str:
    """Reduce excessive blank lines."""
    cleaned = re.sub(r"\n{3,}", "\n\n", text)
    return cleaned.strip() + "\n"
