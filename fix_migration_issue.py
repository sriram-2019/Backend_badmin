#!/usr/bin/env python3
"""
Quick fix script for migration issues on PythonAnywhere
Run this if you get "table already exists" errors during migration

Usage:
    python3 fix_migration_issue.py
"""

import subprocess
import sys
from pathlib import Path

def run_command(command, shell=True):
    """Run a shell command"""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 70)
    print("Migration Fix Script for PythonAnywhere")
    print("=" * 70)
    print()
    
    # Find manage.py
    current_dir = Path.cwd()
    manage_py = current_dir / "manage.py"
    
    if not manage_py.exists():
        print("ERROR: manage.py not found in current directory")
        print(f"Current directory: {current_dir}")
        print("\nPlease run this script from your Django project directory")
        sys.exit(1)
    
    python_exe = "python3"
    
    print("Step 1: Checking migration status...")
    success, stdout, stderr = run_command(f"{python_exe} {manage_py} showmigrations")
    print(stdout)
    
    print("\nStep 2: Attempting to fake migration 0011...")
    success, stdout, stderr = run_command(
        f"{python_exe} {manage_py} migrate registrations 0011 --fake"
    )
    if success:
        print("✓ Migration 0011 faked successfully")
    else:
        print(f"✗ Failed: {stderr}")
        print(stdout)
    
    print("\nStep 3: Running remaining migrations...")
    success, stdout, stderr = run_command(f"{python_exe} {manage_py} migrate")
    if success:
        print("✓ All migrations completed successfully")
        print(stdout)
    else:
        print(f"✗ Migration failed: {stderr}")
        print(stdout)
        print("\nIf the error persists, you may need to:")
        print("1. Check which tables exist in the database")
        print("2. Manually fake specific migrations")
        print("3. Or reset the database (WARNING: data loss)")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("Migration fix completed!")
    print("=" * 70)

if __name__ == "__main__":
    main()

