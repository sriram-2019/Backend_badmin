#!/usr/bin/env python3
"""
Quick status check script for PythonAnywhere deployment
Run this to check if everything is set up correctly

Usage:
    python3 check_pythonanywhere_status.py
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, shell=True):
    """Run a shell command"""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_file_exists(path):
    """Check if a file or directory exists"""
    return Path(path).exists()

def main():
    print("=" * 70)
    print("PythonAnywhere Deployment Status Check")
    print("=" * 70)
    print()
    
    # Get current directory
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    print()
    
    # Check 1: Project structure
    print("1. Checking project structure...")
    checks = {
        "manage.py": check_file_exists("manage.py"),
        "backend/": check_file_exists("backend"),
        "registrations/": check_file_exists("registrations"),
        "requirements.txt": check_file_exists("requirements.txt"),
        ".venv/": check_file_exists(".venv"),
    }
    
    all_good = True
    for item, exists in checks.items():
        status = "✓" if exists else "✗"
        print(f"   {status} {item}")
        if not exists:
            all_good = False
    
    print()
    
    # Check 2: Virtual environment
    print("2. Checking virtual environment...")
    if checks[".venv/"]:
        venv_python = Path(".venv/bin/python3")
        if venv_python.exists():
            success, stdout, stderr = run_command(f"{venv_python} --version")
            if success:
                print(f"   ✓ Python: {stdout.strip()}")
            else:
                print(f"   ✗ Python not found in venv")
                all_good = False
        else:
            print("   ✗ Python executable not found in venv")
            all_good = False
    else:
        print("   ✗ Virtual environment not found")
        all_good = False
    
    print()
    
    # Check 3: Django installation
    print("3. Checking Django installation...")
    if checks[".venv/"]:
        venv_python = Path(".venv/bin/python3")
        success, stdout, stderr = run_command(
            f"{venv_python} -c 'import django; print(django.get_version())'"
        )
        if success:
            print(f"   ✓ Django {stdout.strip()}")
        else:
            print(f"   ✗ Django not installed: {stderr}")
            all_good = False
    else:
        print("   ✗ Cannot check (venv missing)")
    
    print()
    
    # Check 4: Database
    print("4. Checking database...")
    if check_file_exists("db.sqlite3"):
        db_size = Path("db.sqlite3").stat().st_size
        print(f"   ✓ db.sqlite3 exists ({db_size:,} bytes)")
    else:
        print("   ⚠ db.sqlite3 not found (will be created on migrate)")
    
    print()
    
    # Check 5: Migrations
    print("5. Checking migrations...")
    if checks[".venv/"] and checks["manage.py"]:
        venv_python = Path(".venv/bin/python3")
        success, stdout, stderr = run_command(
            f"{venv_python} manage.py showmigrations"
        )
        if success:
            # Count applied migrations
            applied = stdout.count("[X]")
            unapplied = stdout.count("[ ]")
            print(f"   ✓ Applied: {applied}, Unapplied: {unapplied}")
            if unapplied > 0:
                print("   ⚠ Some migrations not applied")
        else:
            print(f"   ✗ Error checking migrations: {stderr}")
            all_good = False
    else:
        print("   ✗ Cannot check (missing requirements)")
    
    print()
    
    # Check 6: Test imports
    print("6. Testing imports...")
    if checks[".venv/"]:
        venv_python = Path(".venv/bin/python3")
        test_imports = [
            "from registrations.models import Registration, Event, CompletedEvent, EventResult",
            "from registrations.views import RegistrationViewSet",
            "from registrations.serializers import RegistrationSerializer",
        ]
        
        for import_stmt in test_imports:
            success, stdout, stderr = run_command(
                f"{venv_python} manage.py shell -c '{import_stmt}'"
            )
            if success:
                print(f"   ✓ {import_stmt[:50]}...")
            else:
                print(f"   ✗ {import_stmt[:50]}...")
                if "ImportError" in stderr or "ImportError" in stdout:
                    print(f"      Error: {stderr[:100]}")
                all_good = False
    
    print()
    print("=" * 70)
    
    if all_good:
        print("✓ All checks passed! Your deployment looks good.")
    else:
        print("⚠ Some issues found. Please review the errors above.")
    
    print()
    print("Quick commands:")
    print("  python3 deploy_pythonanywhere.py  # Run full deployment")
    print("  python3 fix_migration_issue.py    # Fix migration issues")
    print("  source .venv/bin/activate         # Activate virtual environment")
    print("  python3 manage.py runserver       # Test locally (if allowed)")
    print("=" * 70)

if __name__ == "__main__":
    main()

