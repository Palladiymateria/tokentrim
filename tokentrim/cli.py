"""Command-line interface for tokentrim."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys
from pathlib import Path

from tokentrim import __version__
from tokentrim.ast_trimmer import trim_python_code
from tokentrim.clipboard import copy_to_clipboard
from tokentrim.polyglot_trimmer import trim_polyglot_code
from tokentrim.token_counter import compute_savings, TokenSavings

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".go": "go",
    ".rs": "rust",
}

DEFAULT_EXCLUDES = [
    ".git*",
    "__pycache__",
    "*.pyc",
    "node_modules",
    ".venv*",
    "venv*",
    "dist",
    "build",
    "*.egg-info",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".idea",
    ".vscode",
]


def is_color_enabled() -> bool:
    """Check if ANSI color output should be enabled."""
    return sys.stdout.isatty() and not os.getenv("NO_COLOR")


def colorize(text: str, color_code: str) -> str:
    if not is_color_enabled():
        return text
    return f"\033[{color_code}m{text}\033[0m"


def bold(text: str) -> str:
    return colorize(text, "1")


def green(text: str) -> str:
    return colorize(text, "32")


def cyan(text: str) -> str:
    return colorize(text, "36")


def yellow(text: str) -> str:
    return colorize(text, "33")


def dim(text: str) -> str:
    return colorize(text, "2")


def trim_file_content(content: str, file_path: Path, keep_docstrings: bool = True) -> str:
    """Trim a given file content based on its extension."""
    ext = file_path.suffix.lower()
    if ext == ".py":
        return trim_python_code(content, keep_docstrings=keep_docstrings)
    elif ext in SUPPORTED_EXTENSIONS:
        return trim_polyglot_code(content, ext, keep_docstrings=keep_docstrings)
    return content


def is_excluded(path: Path, root: Path, excludes: list[str]) -> bool:
    """Check whether a path matches any exclude pattern."""
    rel = path.relative_to(root).as_posix()
    name = path.name
    for pat in excludes:
        if fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(f"*/{name}", pat):
            return True
    return False


def build_markdown_bundle(results: list[tuple[Path, str]]) -> str:
    """Combine multiple trimmed files into a markdown code block bundle for LLMs."""
    blocks: list[str] = []
    for rel_path, code in results:
        ext = rel_path.suffix.lower().lstrip(".")
        lang = SUPPORTED_EXTENSIONS.get(rel_path.suffix.lower(), ext)
        blocks.append(f"### {rel_path.as_posix()}\n```{lang}\n{code.strip()}\n```")
    return "\n\n".join(blocks) + "\n"


def can_encode(text: str) -> bool:
    """Check if stdout can encode the given characters."""
    try:
        text.encode(sys.stdout.encoding or "utf-8")
        return True
    except Exception:
        return False


def get_box_style() -> dict[str, str]:
    if can_encode("┌─┐│└┘├┤✓"):
        return {
            "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
            "h": "─", "v": "│", "ml": "├", "mr": "┤",
            "check": "✓",
        }
    return {
        "tl": "+", "tr": "+", "bl": "+", "br": "+",
        "h": "-", "v": "|", "ml": "+", "mr": "+",
        "check": "[OK]",
    }


def print_stats_table(savings: TokenSavings, label: str = "Total") -> None:
    """Print an aesthetic terminal table of savings."""
    b = get_box_style()
    pct_color = green if savings.token_reduction_pct >= 50 else yellow
    savings_str = pct_color(f"-{savings.token_reduction_pct}%")
    cost_str = green(f"${savings.estimated_usd_saved():.4f}")

    print(dim(b["tl"] + b["h"] * 46 + b["tr"]))
    print(dim(b["v"] + " ") + bold(f"tokentrim summary: {label}".ljust(44)) + dim(b["v"]))
    print(dim(b["ml"] + b["h"] * 46 + b["mr"]))
    print(dim(b["v"] + " ") + f"Original lines:   {savings.original_lines:,}".ljust(44) + dim(b["v"]))
    print(dim(b["v"] + " ") + f"Trimmed lines:    {savings.trimmed_lines:,} ({dim(f'-{savings.line_reduction_pct}%')})".ljust(53) + dim(b["v"]))
    print(dim(b["v"] + " ") + f"Original tokens:  ~{savings.original_tokens:,}".ljust(44) + dim(b["v"]))
    print(dim(b["v"] + " ") + f"Trimmed tokens:   ~{savings.trimmed_tokens:,}".ljust(44) + dim(b["v"]))
    print(dim(b["v"] + " ") + f"Token reduction:  {savings_str}".ljust(53) + dim(b["v"]))
    print(dim(b["v"] + " ") + f"Est. cost saved:  {cost_str} / prompt".ljust(53) + dim(b["v"]))
    print(dim(b["bl"] + b["h"] * 46 + b["br"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tokentrim",
        description="Shrink your codebase by 60-80% for LLM context prompts. Zero dependencies, 100% local.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Path to file or directory to trim (default: current directory)",
    )
    parser.add_argument(
        "-c", "--clip",
        action="store_true",
        help="Copy trimmed output directly to system clipboard",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        metavar="FILE",
        help="Write trimmed output to destination file",
    )
    parser.add_argument(
        "-s", "--stats",
        action="store_true",
        help="Display detailed token and line reduction statistics",
    )
    parser.add_argument(
        "--no-docstrings",
        action="store_true",
        help="Strip docstrings for maximum token reduction",
    )
    parser.add_argument(
        "-e", "--exclude",
        action="append",
        default=[],
        help="Glob pattern to exclude (can be repeated)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as machine-readable JSON",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"tokentrim {__version__}",
    )

    args = parser.parse_args(argv)
    target_path = Path(args.target).resolve()

    if not target_path.exists():
        print(f"Error: Target path '{args.target}' does not exist.", file=sys.stderr)
        return 1

    excludes = list(DEFAULT_EXCLUDES) + args.exclude
    keep_docstrings = not args.no_docstrings

    if target_path.is_file():
        try:
            raw_content = target_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"Error reading file '{target_path}': {e}", file=sys.stderr)
            return 1

        trimmed = trim_file_content(raw_content, target_path, keep_docstrings=keep_docstrings)
        savings = compute_savings(raw_content, trimmed)

        if args.json:
            payload = {
                "file": target_path.as_posix(),
                "original_lines": savings.original_lines,
                "trimmed_lines": savings.trimmed_lines,
                "original_tokens": savings.original_tokens,
                "trimmed_tokens": savings.trimmed_tokens,
                "tokens_saved_percent": savings.token_reduction_pct,
                "estimated_usd_saved": savings.estimated_usd_saved(),
                "content": trimmed,
            }
            print(json.dumps(payload, indent=2))
            return 0

        # Handle file output
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(trimmed, encoding="utf-8")
            if not args.clip and not args.stats:
                print(f"Wrote trimmed code to {args.output}")

        # Handle clipboard
        b = get_box_style()
        if args.clip:
            copied = copy_to_clipboard(trimmed)
            if copied:
                print(green(f"{b['check']} Trimmed code copied to clipboard!"))
            else:
                print(yellow("Warning: Could not access system clipboard."), file=sys.stderr)

        # Handle stats
        if args.stats or args.clip or args.output:
            print_stats_table(savings, label=target_path.name)
        else:
            # Default stdout output if no action flag given
            sys.stdout.write(trimmed)

        return 0

    # Directory scanning
    files_to_process: list[Path] = []
    for root_dir, dirs, files in os.walk(target_path):
        root_p = Path(root_dir)
        # Filter directories in-place for faster walk
        dirs[:] = [d for d in dirs if not is_excluded(root_p / d, target_path, excludes)]

        for f in files:
            fp = root_p / f
            if fp.suffix.lower() in SUPPORTED_EXTENSIONS and not is_excluded(fp, target_path, excludes):
                files_to_process.append(fp)

    files_to_process.sort()

    if not files_to_process:
        print(f"No supported code files found in '{args.target}'.", file=sys.stderr)
        return 0

    total_orig_text: list[str] = []
    total_trim_text: list[str] = []
    results: list[tuple[Path, str]] = []

    for file_path in files_to_process:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        trimmed = trim_file_content(content, file_path, keep_docstrings=keep_docstrings)
        rel_path = file_path.relative_to(target_path)
        results.append((rel_path, trimmed))
        total_orig_text.append(content)
        total_trim_text.append(trimmed)

    bundled_output = build_markdown_bundle(results)
    combined_orig = "\n".join(total_orig_text)
    combined_trim = "\n".join(total_trim_text)
    savings = compute_savings(combined_orig, combined_trim)

    if args.json:
        payload = {
            "directory": target_path.as_posix(),
            "files_count": len(results),
            "original_lines": savings.original_lines,
            "trimmed_lines": savings.trimmed_lines,
            "original_tokens": savings.original_tokens,
            "trimmed_tokens": savings.trimmed_tokens,
            "tokens_saved_percent": savings.token_reduction_pct,
            "estimated_usd_saved": savings.estimated_usd_saved(),
            "bundle": bundled_output,
        }
        print(json.dumps(payload, indent=2))
        return 0

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(bundled_output, encoding="utf-8")
        if not args.clip:
            print(f"Wrote context bundle ({len(results)} files) to {args.output}")

    b = get_box_style()
    if args.clip:
        copied = copy_to_clipboard(bundled_output)
        if copied:
            print(green(f"{b['check']} Bundled & trimmed {len(results)} files copied to clipboard!"))
        else:
            print(yellow("Warning: Could not access system clipboard."), file=sys.stderr)

    if args.stats or args.clip or args.output:
        print_stats_table(savings, label=f"{len(results)} files in {target_path.name}/")
    else:
        sys.stdout.write(bundled_output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
