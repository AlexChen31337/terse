#!/usr/bin/env python3
"""
Unit tests for llama-egress-proxy sanitize rules.
Run: python3 test_sanitize.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sanitize import sanitize

# Dynamically build XML close tags to survive the write-tool XML stripping.
# The write tool removes </tag> sequences from file content.
_SYS_REM_CLOSE = "</" + "system-reminder>"
_FUNC_CLOSE    = "</" + "function>"
_PARAM_CLOSE   = "</" + "parameter>"


def _sys_rem(inner):
    return "<system-reminder>" + inner + _SYS_REM_CLOSE

def _func(name, inner):
    return "<function=" + name + ">" + inner + _FUNC_CLOSE

def _param(name, inner):
    return "<parameter=" + name + ">" + inner + _PARAM_CLOSE


TESTS = [
    (
        "system-reminder basic",
        "Hello " + _sys_rem("SECRET") + " World",
        "SECRET",
        "Hello",
    ),
    (
        "system-reminder multiline",
        "Before\n" + _sys_rem("\nline1\nline2\n") + "\nAfter",
        "line1",
        "After",
    ),
    (
        "openclaw internal context",
        "A <<<BEGIN_OPENCLAW_INTERNAL_CONTEXT>>>hidden<<<END_OPENCLAW_INTERNAL_CONTEXT>>> B",
        "hidden",
        "A",
    ),
    (
        "external untrusted",
        "X <<<EXTERNAL_UNTRUSTED_CONTENT foo=bar>>>evil<<<END_EXTERNAL_UNTRUSTED_CONTENT foo=bar>>> Y",
        "evil",
        "X",
    ),
    (
        "tool_result blob",
        "text [tool_result tool_use_id=abc123] some blob\n\nnext",
        "some blob",
        "next",
    ),
    (
        "inter-session",
        "ok\n[Inter-session message] sourceSession=xyz\nafter",
        "sourceSession",
        "after",
    ),
    (
        "function xml",
        "before " + _func("bash", "echo hi") + " after",
        "echo hi",
        "before",
    ),
    (
        "parameter xml",
        "x " + _param("cmd", "ls -la") + " y",
        "ls -la",
        "x",
    ),
    (
        "clean passthrough",
        "Hello, this is normal output.",
        None,
        "Hello, this is normal output.",
    ),
]


def run_tests():
    passed = 0
    failed = 0
    for name, inp, absent, present in TESTS:
        result = sanitize(inp)
        ok = True
        if absent and absent in result:
            print("  FAIL [" + name + "]: '" + absent + "' still present in: " + repr(result))
            ok = False
        if present and present not in result:
            print("  FAIL [" + name + "]: '" + present + "' missing from: " + repr(result))
            ok = False
        if ok:
            print("  PASS: " + name)
            passed += 1
        else:
            failed += 1

    print("\n" + str(passed) + "/" + str(passed + failed) + " tests passed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
