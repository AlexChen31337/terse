#!/usr/bin/env python3
"""One-time script: append the sanitize() function to sanitize.py"""
import re, os

target = os.path.join(os.path.dirname(__file__), "sanitize.py")

with open(target, "r") as f:
    content = f.read()

if "def sanitize" in content:
    print("sanitize() already present")
else:
    # Build p9 pattern without embedding the close tag literally
    p9 = 'r"<parameter=[a-z_]+>[\\\\s\\\\S]*?</" + r"parameter>"'
    appendix = """
# Pattern 9: built dynamically to avoid XML-stripping in tooling
_P9 = r"<parameter=[a-z_]+>[\\s\\S]*?</" + r"parameter>"
_RAW_PATTERNS.append((_P9, ""))

# Compile all patterns once at import time
_PATTERNS = [(re.compile(p, re.MULTILINE), repl) for p, repl in _RAW_PATTERNS]


def sanitize(text: str) -> str:
    \"\"\"Apply all sanitisation patterns. Returns cleaned string.\"\"\"
    if not text:
        return text
    for pattern, repl in _PATTERNS:
        text = pattern.sub(repl, text)
    text = re.sub(r"\\n{3,}", "\\n\\n", text)
    return text.strip()
"""
    with open(target, "a") as f:
        f.write(appendix)
    print("Appended sanitize() function")

print("Done")
