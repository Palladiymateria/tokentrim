"""Cross-platform clipboard utility using system binaries without external dependencies."""

from __future__ import annotations

import shutil
import subprocess
import sys


def copy_to_clipboard(text: str) -> bool:
    """Copy given text to system clipboard across Windows, macOS, and Linux.
    
    Returns True if successfully copied, False otherwise.
    """
    if not text:
        return False

    try:
        if sys.platform == "win32":
            # clip.exe expects text encoded in utf-16 or OEM encoding
            subprocess.run(
                ["clip.exe"],
                input=text.encode("utf-16"),
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True

        if sys.platform == "darwin":
            if shutil.which("pbcopy"):
                subprocess.run(
                    ["pbcopy"],
                    input=text.encode("utf-8"),
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True

        # Linux / Unix
        for bin_name, args in [
            ("wl-copy", ["wl-copy"]),
            ("xclip", ["xclip", "-selection", "clipboard"]),
            ("xsel", ["xsel", "--clipboard", "--input"]),
        ]:
            if shutil.which(bin_name):
                subprocess.run(
                    args,
                    input=text.encode("utf-8"),
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True

    except Exception:
        return False

    return False
