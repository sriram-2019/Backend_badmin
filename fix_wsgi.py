#!/usr/bin/env python3
"""
Fix WSGI configuration for PythonAnywhere
This script generates the correct WSGI configuration based on your actual setup

Usage:
    python3 fix_wsgi.py
"""

import os
import sys
from pathlib import Path

def find_project_path():
    """Find the actual project path"""
    current = Path.cwd()
    
    # Check if we're in the project
    if (current / "manage.py").exists():
        return current
    
    # Check common locations
    home = Path.home()
    possible_paths = [
        home / "Backend_badmin",
        home / "myproject" / "myproject",
        home / "myproject",
    ]
    
    for path in possible_paths:
        if (path / "manage.py").exists():
            return path
    
    return current

def find_venv_path(project_path):
    """Find virtual environment path"""
    possible_venvs = [
        project_path / ".venv",
        project_path / "venv",
        project_path.parent / ".venv",
        Path.home() / ".virtualenvs" / "Backend_badmin",
    ]
    
    for venv_path in possible_venvs:
        if venv_path.exists() and (venv_path / "bin" / "python3").exists():
            return venv_path
    
    return None

def generate_wsgi_config(project_path, venv_path, username):
    """Generate WSGI configuration"""
    
    # Python executable in venv
    if venv_path:
        python_exe = venv_path / "bin" / "python3"
    else:
        python_exe = "python3"
    
    # Check Python version
    import subprocess
    try:
        result = subprocess.run(
            [str(python_exe), "--version"],
            capture_output=True,
            text=True
        )
        python_version = result.stdout.strip()
        # Extract version number
        version_parts = python_version.split()[1].split('.')
        major, minor = int(version_parts[0]), int(version_parts[1])
        use_activate_this = (major, minor) < (3, 13)
    except:
        use_activate_this = False
    
    wsgi_content = f"""# +++++++++++ DJANGO +++++++++++
import os
import sys

# Add your project directory to the Python path
path = '{project_path}'
if path not in sys.path:
    sys.path.insert(0, path)

# Virtual environment activation
"""
    
    if venv_path and use_activate_this:
        activate_this = venv_path / "bin" / "activate_this.py"
        if activate_this.exists():
            wsgi_content += f"""activate_this = '{activate_this}'
with open(activate_this) as f:
    exec(f.read(), {{'__file__': activate_this}})
"""
        else:
            # Use site-packages method
            site_packages = venv_path / "lib" / f"python{major}.{minor}" / "site-packages"
            if site_packages.exists():
                wsgi_content += f"""# Add virtual environment site-packages to path
venv_site_packages = '{site_packages}'
if venv_site_packages not in sys.path:
    sys.path.insert(0, venv_site_packages)
"""
    elif venv_path:
        # Python 3.13+ doesn't have activate_this.py, use site-packages
        # Find Python version in venv
        try:
            result = subprocess.run(
                [str(venv_path / "bin" / "python3"), "--version"],
                capture_output=True,
                text=True
            )
            version_str = result.stdout.strip().split()[1]
            version_parts = version_str.split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            site_packages = venv_path / "lib" / f"python{major}.{minor}" / "site-packages"
            if site_packages.exists():
                wsgi_content += f"""# Add virtual environment site-packages to path (Python 3.13+)
venv_site_packages = '{site_packages}'
if venv_site_packages not in sys.path:
    sys.path.insert(0, venv_site_packages)
"""
        except:
            pass
    
    wsgi_content += f"""
# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings'

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
"""
    
    return wsgi_content

def main():
    print("=" * 70)
    print("WSGI Configuration Generator for PythonAnywhere")
    print("=" * 70)
    print()
    
    # Find project
    project_path = find_project_path()
    print(f"Project path: {project_path}")
    
    # Find venv
    venv_path = find_venv_path(project_path)
    if venv_path:
        print(f"Virtual environment: {venv_path}")
    else:
        print("⚠ Virtual environment not found")
    
    # Get username
    username = os.environ.get('USER', 'BackendBadminton')
    print(f"Username: {username}")
    print()
    
    # Generate WSGI config
    wsgi_config = generate_wsgi_config(project_path, venv_path, username)
    
    print("=" * 70)
    print("WSGI CONFIGURATION")
    print("=" * 70)
    print()
    print("Copy this into your PythonAnywhere WSGI file:")
    print()
    print("-" * 70)
    print(wsgi_config)
    print("-" * 70)
    print()
    
    # Save to file
    output_file = project_path / "wsgi_config_output.py"
    with open(output_file, 'w') as f:
        f.write(wsgi_config)
    
    print(f"✓ Configuration saved to: {output_file}")
    print()
    print("Next steps:")
    print("1. Go to PythonAnywhere Web tab")
    print("2. Click on your web app")
    print("3. Click 'WSGI configuration file'")
    print("4. Replace the entire content with the configuration above")
    print("5. Save and reload your web app")
    print("=" * 70)

if __name__ == "__main__":
    main()

