#!/usr/bin/env python3
import os
import re


def fix_whitespace_issues():
    for root, dirs, files in os.walk("jiaz"):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r") as f:
                    content = f.read()

                # Fix trailing whitespace
                lines = content.split("\n")
                fixed_lines = [line.rstrip() for line in lines]

                # Fix blank lines with whitespace
                fixed_lines = [line if line.strip() else "" for line in fixed_lines]

                # Fix multiple blank lines (max 2 consecutive)
                new_lines = []
                blank_count = 0
                for line in fixed_lines:
                    if line.strip() == "":
                        blank_count += 1
                        if blank_count <= 2:
                            new_lines.append(line)
                    else:
                        blank_count = 0
                        new_lines.append(line)

                new_content = "\n".join(new_lines)
                if new_content != content:
                    with open(filepath, "w") as f:
                        f.write(new_content)
                    print(f"Fixed whitespace in {filepath}")


if __name__ == "__main__":
    fix_whitespace_issues()
