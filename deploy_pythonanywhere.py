#!/usr/bin/env python3
"""
Automated Deployment Script for PythonAnywhere
This script automates the entire deployment process for Django on PythonAnywhere.

Usage:
1. Upload this file to PythonAnywhere (via Files tab or Git)
2. Open a Bash console on PythonAnywhere
3. Run: python3 deploy_pythonanywhere.py

The script will:
- Clone/pull from GitHub repository
- Install dependencies
- Run migrations
- Configure settings for production
- Set up static files
- Provide instructions for web app configuration
"""

import os
import sys
import subprocess
import getpass
from pathlib import Path

# Configuration
GITHUB_REPO = "https://github.com/sriram-2019/Backend_badmin.git"
PROJECT_NAME = "Backend_badmin"
DJANGO_PROJECT_DIR = "."  # Django project files are at the root of the repo

# Colors for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_step(step_num, text):
    print(f"{Colors.OKBLUE}[Step {step_num}] {text}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def run_command(command, check=True, shell=False):
    """Run a shell command and return the result"""
    try:
        if shell:
            result = subprocess.run(command, shell=True, check=check, 
                                  capture_output=True, text=True)
        else:
            result = subprocess.run(command.split(), check=check,
                                  capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr
    except Exception as e:
        return False, "", str(e)

def get_username():
    """Get PythonAnywhere username"""
    username = getpass.getuser()
    print_success(f"Detected username: {username}")
    return username

def check_python_version():
    """Check Python version"""
    print_step(1, "Checking Python version...")
    success, stdout, stderr = run_command("python3 --version")
    if success:
        print_success(f"Python version: {stdout.strip()}")
        return True
    else:
        print_error("Python3 not found!")
        return False

def setup_project_directory(username):
    """Set up project directory"""
    print_step(2, "Setting up project directory...")
    
    home_dir = Path.home()
    project_path = home_dir / PROJECT_NAME
    
    # Check if project already exists
    if project_path.exists():
        print_warning(f"Project directory {project_path} already exists")
        response = input("Do you want to update it from GitHub? (y/n): ").strip().lower()
        if response == 'y':
            print(f"Changing to {project_path}...")
            os.chdir(project_path)
            success, stdout, stderr = run_command("git pull origin main", shell=True)
            if success:
                print_success("Repository updated from GitHub")
            else:
                print_error(f"Failed to pull: {stderr}")
                return False, None
        else:
            print(f"Using existing project at {project_path}")
    else:
        # Clone repository
        print(f"Cloning repository to {project_path}...")
        os.chdir(home_dir)
        success, stdout, stderr = run_command(f"git clone {GITHUB_REPO} {PROJECT_NAME}", shell=True)
        if success:
            print_success("Repository cloned successfully")
        else:
            print_error(f"Failed to clone: {stderr}")
            return False, None
    
    return True, project_path

def setup_virtual_environment(project_path):
    """Set up virtual environment"""
    print_step(3, "Setting up virtual environment...")
    
    venv_path = project_path / ".venv"
    
    if venv_path.exists():
        print_warning("Virtual environment already exists")
        response = input("Do you want to recreate it? (y/n): ").strip().lower()
        if response == 'y':
            import shutil
            shutil.rmtree(venv_path)
        else:
            print_success("Using existing virtual environment")
            return True, venv_path
    
    # Create virtual environment
    print("Creating virtual environment...")
    success, stdout, stderr = run_command(f"python3 -m venv {venv_path}", shell=True)
    if success:
        print_success("Virtual environment created")
    else:
        print_error(f"Failed to create venv: {stderr}")
        return False, None
    
    return True, venv_path

def install_dependencies(venv_path, project_path):
    """Install Python dependencies"""
    print_step(4, "Installing dependencies...")
    
    # Get the Python executable in venv
    python_exe = venv_path / "bin" / "python3"
    pip_exe = venv_path / "bin" / "pip3"
    
    # Upgrade pip
    print("Upgrading pip...")
    success, stdout, stderr = run_command(f"{pip_exe} install --upgrade pip", shell=True)
    if not success:
        print_warning(f"Failed to upgrade pip: {stderr}")
    
    # Install requirements
    if DJANGO_PROJECT_DIR == ".":
        requirements_file = project_path / "requirements.txt"
    else:
        requirements_file = project_path / DJANGO_PROJECT_DIR / "requirements.txt"
    
    if not requirements_file.exists():
        print_error(f"Requirements file not found at {requirements_file}")
        return False
    
    print(f"Installing packages from {requirements_file}...")
    success, stdout, stderr = run_command(
        f"{pip_exe} install -r {requirements_file}", shell=True
    )
    if success:
        print_success("Dependencies installed successfully")
        return True
    else:
        print_error(f"Failed to install dependencies: {stderr}")
        return False

def configure_settings(project_path):
    """Configure Django settings for production"""
    print_step(5, "Configuring Django settings...")
    
    if DJANGO_PROJECT_DIR == ".":
        settings_file = project_path / "backend" / "settings.py"
    else:
        settings_file = project_path / DJANGO_PROJECT_DIR / "backend" / "settings.py"
    
    if not settings_file.exists():
        print_error(f"Settings file not found at {settings_file}")
        return False
    
    # Read current settings
    with open(settings_file, 'r') as f:
        settings_content = f.read()
    
    # Check if already configured
    if "pythonanywhere.com" in settings_content:
        print_warning("Settings appear to be already configured for PythonAnywhere")
        return True
    
    # Get username for ALLOWED_HOSTS
    username = getpass.getuser()
    domain = f"{username}.pythonanywhere.com"
    
    # Add production settings
    production_settings = f"""
# PythonAnywhere Production Settings
import os

DEBUG = False
ALLOWED_HOSTS = ['{domain}', 'www.{domain}']

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
"""
    
    # Append to settings file
    with open(settings_file, 'a') as f:
        f.write(production_settings)
    
    print_success("Settings configured for production")
    return True

def run_migrations(venv_path, project_path):
    """Run Django migrations"""
    print_step(6, "Running database migrations...")
    
    python_exe = venv_path / "bin" / "python3"
    if DJANGO_PROJECT_DIR == ".":
        manage_py = project_path / "manage.py"
        project_dir = project_path
    else:
        manage_py = project_path / DJANGO_PROJECT_DIR / "manage.py"
        project_dir = project_path / DJANGO_PROJECT_DIR
    
    if not manage_py.exists():
        print_error(f"manage.py not found at {manage_py}")
        return False
    
    os.chdir(project_dir)
    
    # Run migrations
    print("Running migrations...")
    success, stdout, stderr = run_command(
        f"{python_exe} {manage_py} migrate", shell=True
    )
    if success:
        print_success("Migrations completed successfully")
        print(stdout)
        return True
    else:
        print_error(f"Migration failed: {stderr}")
        print(stdout)
        return False

def collect_static_files(venv_path, project_path):
    """Collect static files"""
    print_step(7, "Collecting static files...")
    
    python_exe = venv_path / "bin" / "python3"
    if DJANGO_PROJECT_DIR == ".":
        manage_py = project_path / "manage.py"
        project_dir = project_path
        static_dir = project_path / "static"
    else:
        manage_py = project_path / DJANGO_PROJECT_DIR / "manage.py"
        project_dir = project_path / DJANGO_PROJECT_DIR
        static_dir = project_path / DJANGO_PROJECT_DIR / "static"
    
    os.chdir(project_dir)
    
    # Create static directory if it doesn't exist
    static_dir.mkdir(exist_ok=True)
    
    # Collect static files
    print("Collecting static files...")
    success, stdout, stderr = run_command(
        f"{python_exe} {manage_py} collectstatic --noinput", shell=True
    )
    if success:
        print_success("Static files collected")
        return True
    else:
        print_warning(f"Static files collection had issues: {stderr}")
        print(stdout)
        return True  # Not critical

def create_superuser(venv_path, project_path):
    """Optionally create superuser"""
    print_step(8, "Superuser creation (optional)...")
    
    response = input("Do you want to create a superuser now? (y/n): ").strip().lower()
    if response == 'y':
    python_exe = venv_path / "bin" / "python3"
    if DJANGO_PROJECT_DIR == ".":
        manage_py = project_path / "manage.py"
        project_dir = project_path
    else:
        manage_py = project_path / DJANGO_PROJECT_DIR / "manage.py"
        project_dir = project_path / DJANGO_PROJECT_DIR
    
    os.chdir(project_dir)
        
        print("Running createsuperuser...")
        # This will be interactive
        success, stdout, stderr = run_command(
            f"{python_exe} {manage_py} createsuperuser", shell=True, check=False
        )
        if success:
            print_success("Superuser created")
        else:
            print_warning("Superuser creation skipped or failed")
    else:
        print("Skipping superuser creation")

def print_web_app_config(username, project_path):
    """Print instructions for web app configuration"""
    print_header("WEB APP CONFIGURATION REQUIRED")
    
    venv_path = project_path / ".venv"
    wsgi_file = venv_path / "bin" / "activate_this.py"
    project_wsgi = project_path / DJANGO_PROJECT_DIR / "backend" / "wsgi.py"
    
    print(f"""
{Colors.BOLD}Next Steps:{Colors.ENDC}

1. {Colors.OKCYAN}Go to PythonAnywhere Web Tab{Colors.ENDC}
   https://www.pythonanywhere.com/web_app_setup/

2. {Colors.OKCYAN}Configure WSGI file:{Colors.ENDC}
   - Click on your web app
   - Edit the WSGI file
   - Replace the content with:

{Colors.WARNING}# +++++++++++ DJANGO +++++++++++
import os
import sys

# Add your project directory to the Python path
path = '/home/{username}/{PROJECT_NAME}'
if path not in sys.path:
    sys.path.insert(0, path)

# Activate virtual environment
activate_this = '/home/{username}/{PROJECT_NAME}/.venv/bin/activate_this.py'
with open(activate_this) as f:
    exec(f.read(), {{'__file__': activate_this}})

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings'

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
{Colors.ENDC}

3. {Colors.OKCYAN}Configure Static Files:{Colors.ENDC}
   - In the Web tab, go to "Static files"
   - Add mapping:
     URL: /static/
     Directory: /home/{username}/{PROJECT_NAME}/staticfiles

4. {Colors.OKCYAN}Configure Media Files (if needed):{Colors.ENDC}
   - Add mapping:
     URL: /media/
     Directory: /home/{username}/{PROJECT_NAME}/media

5. {Colors.OKCYAN}Reload Web App:{Colors.ENDC}
   - Click the green "Reload" button in the Web tab

6. {Colors.OKCYAN}Your API will be available at:{Colors.ENDC}
   https://{username}.pythonanywhere.com/api/
   https://{username}.pythonanywhere.com/api/registrations/
   https://{username}.pythonanywhere.com/api/events/
   https://{username}.pythonanywhere.com/api/completed-events/
   https://{username}.pythonanywhere.com/api/event-results/

{Colors.WARNING}Important:{Colors.ENDC}
- Make sure CORS is configured in settings.py for your frontend domain
- Check that ALLOWED_HOSTS includes your domain
- Database will be SQLite by default (db.sqlite3)
""")

def main():
    """Main deployment function"""
    print_header("PythonAnywhere Django Deployment Script")
    
    print(f"Repository: {GITHUB_REPO}")
    print(f"Project: {PROJECT_NAME}\n")
    
    # Get username
    username = get_username()
    
    # Step 1: Check Python
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Setup project directory
    success, project_path = setup_project_directory(username)
    if not success:
        print_error("Failed to set up project directory")
        sys.exit(1)
    
    # Step 3: Setup virtual environment
    success, venv_path = setup_virtual_environment(project_path)
    if not success:
        print_error("Failed to set up virtual environment")
        sys.exit(1)
    
    # Step 4: Install dependencies
    if not install_dependencies(venv_path, project_path):
        print_error("Failed to install dependencies")
        sys.exit(1)
    
    # Step 5: Configure settings
    if not configure_settings(project_path):
        print_warning("Settings configuration had issues, but continuing...")
    
    # Step 6: Run migrations
    if not run_migrations(venv_path, project_path):
        print_error("Failed to run migrations")
        sys.exit(1)
    
    # Step 7: Collect static files
    collect_static_files(venv_path, project_path)
    
    # Step 8: Create superuser (optional)
    create_superuser(venv_path, project_path)
    
    # Final instructions
    print_header("DEPLOYMENT COMPLETE!")
    print_success("Django project is ready!")
    print_web_app_config(username, project_path)
    
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}Deployment script completed successfully!{Colors.ENDC}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Deployment cancelled by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

