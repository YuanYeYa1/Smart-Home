#!/usr/bin/env python3
"""Simple runner for deploy_remote.py with output logging"""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "deploy_remote.py"],
    capture_output=True,
    text=True,
    timeout=120
)

print("=== STDOUT ===")
print(result.stdout)
print("=== STDERR ===")
print(result.stderr)
print(f"=== RETURN CODE: {result.returncode} ===")
