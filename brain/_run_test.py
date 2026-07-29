"""Run import test and print result."""
import subprocess, sys
r = subprocess.run([sys.executable, "brain/_import_test.py"], capture_output=True, text=True, timeout=60)
if r.stdout:
    print(r.stdout[:12000])
if r.stderr:
    print("STDERR:", r.stderr[:5000], file=sys.stderr)
print("RC:", r.returncode)
