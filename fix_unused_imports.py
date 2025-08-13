#!/usr/bin/env python3
"""Script to fix unused imports in the jiaz codebase."""

import os
import re
import subprocess


def remove_unused_imports():
    """Remove unused imports using autoflake."""
    cmd = [
        "python",
        "-m",
        "autoflake",
        "--remove-all-unused-imports",
        "--in-place",
        "--recursive",
        "jiaz/",
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd="/Users/shsayyed/Desktop/SS7/jiaz"
        )
        print("Autoflake output:", result.stdout)
        if result.stderr:
            print("Autoflake errors:", result.stderr)
        return result.returncode == 0
    except FileNotFoundError:
        print("autoflake not found, installing...")
        subprocess.run(["pip", "install", "autoflake"])
        return remove_unused_imports()


if __name__ == "__main__":
    remove_unused_imports()
