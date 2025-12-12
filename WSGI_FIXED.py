# +++++++++++ DJANGO +++++++++++
# WSGI Configuration for PythonAnywhere (Python 3.13+ Compatible)
# This version works without activate_this.py

import os
import sys
import glob

# Add your project directory to the Python path
path = '/home/BackendBadminton/Backend_badmin'
if path not in sys.path:
    sys.path.insert(0, path)

# Virtual environment activation (Python 3.13+ compatible)
# Add virtual environment site-packages to path
venv_path = '/home/BackendBadminton/Backend_badmin/.venv'

# Try to find site-packages directory
site_packages_glob = f'{venv_path}/lib/python*/site-packages'
matches = glob.glob(site_packages_glob)
if matches:
    site_packages = matches[0]
    if site_packages not in sys.path:
        sys.path.insert(0, site_packages)

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings'

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

