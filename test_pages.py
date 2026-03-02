#!/usr/bin/env python3
# Quick smoke test for st_pages modules
import importlib
import sys

pages = [
    "st_pages.generate",
    "st_pages.localize",
    "st_pages.preview_schedule",
    "st_pages.history",
    "st_pages.analytics"
]

print("Testing st_pages modules...")
failed = []

for p in pages:
    try:
        m = importlib.import_module(p)
        if not hasattr(m, "page"):
            failed.append(f"{p} missing page() function")
            print(f"✗ {p} - missing page() function")
        else:
            print(f"✓ {p} - has page() function")
    except Exception as e:
        failed.append(f"{p} - {e}")
        print(f"✗ {p} - import failed: {e}")

if failed:
    print("\n❌ FAILED:")
    for f in failed:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("\n✅ All pages have page() functions!")
    sys.exit(0)
