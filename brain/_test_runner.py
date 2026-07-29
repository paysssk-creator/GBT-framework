"""Run the import test and print results cleanly."""
import subprocess, sys, json

ROOT = "C:/Users/ADMIN/GBTxiaotudouV5"
result = subprocess.run(
    [sys.executable, "brain/_import_test.py"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    timeout=60,
)
print("STDOUT:", result.stdout[:10000] if result.stdout else "(none)")
print("STDERR:", result.stderr[:5000] if result.stderr else "(none)")
print("RC:", result.returncode)
