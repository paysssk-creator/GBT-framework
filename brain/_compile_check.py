#!/usr/bin/env python3
"""Compile-check step_tracker.py — verifies syntax without runtime import."""
import py_compile, sys

files = [
    "brain/step_tracker.py",
    "brain/chain_kernel.py",
]
ok = True
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f"  ✅ {f} — compiles OK")
    except py_compile.PyCompileError as e:
        print(f"  ❌ {f} — {e}")
        ok = False
sys.exit(0 if ok else 1)
