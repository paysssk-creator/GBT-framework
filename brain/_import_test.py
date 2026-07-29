"""Test importing every brain/*.py module and report errors."""
import sys, os, importlib, traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Suppress noisy logging during import test
import logging
logging.disable(logging.CRITICAL)

# Also suppress potential blocking calls by patching
import builtins
_orig_print = builtins.print
builtins.print = lambda *a, **kw: None

brain_dir = os.path.join(ROOT, "brain")

# List all .py files in brain/ except this test file and __init__.py
modules = []
for f in sorted(os.listdir(brain_dir)):
    if f == "__init__.py":
        modules.append("brain")
    elif f.endswith(".py") and f != "_import_test.py":
        modname = f"brain.{f[:-3]}"
        modules.append(modname)

errors = []
warnings = []
circular_imports = []
missing_modules = []
missing_names = []
imported_ok = []

already_loaded = set(sys.modules.keys())

for modname in modules:
    # Clear any previously loaded version
    if modname in sys.modules:
        del sys.modules[modname]
    
    try:
        importlib.import_module(modname)
        imported_ok.append(modname)
        # Record what this module added to sys.modules
    except ImportError as e:
        msg = str(e)
        if "circular import" in msg.lower() or "circular" in msg.lower():
            circular_imports.append((modname, msg))
        elif "No module named" in msg:
            missing_modules.append((modname, msg))
        elif "cannot import name" in msg:
            missing_names.append((modname, msg))
        else:
            errors.append((modname, msg, traceback.format_exc()))
    except Exception as e:
        errors.append((modname, str(e), traceback.format_exc()))

# Restore print
builtins.print = _orig_print

# Also check for circular imports by analyzing the import graph
# Report results
result = {
    "ok": len(errors) == 0 and len(circular_imports) == 0 and len(missing_modules) == 0 and len(missing_names) == 0,
    "imported_ok": imported_ok,
    "errors": [{"module": m, "error": e, "traceback": t} for m, e, t in errors],
    "circular_imports": [{"module": m, "detail": d} for m, d in circular_imports],
    "missing_modules": [{"module": m, "detail": d} for m, d in missing_modules],
    "missing_names": [{"module": m, "detail": d} for m, d in missing_names],
    "warnings": warnings,
    "total_modules": len(modules),
}

import json
print(json.dumps(result, indent=2, ensure_ascii=False))
