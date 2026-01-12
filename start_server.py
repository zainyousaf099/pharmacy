#!/usr/bin/env python
"""
Wrapper script to start Django server with correct paths.
This is used by the Electron app in production mode.
"""
import sys
import os

# Get the directory where this script is located (django-app folder)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add the django-app directory to Python path so Django can find all modules
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Set environment variables
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

def main():
    """Run administrative tasks."""
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    
    # If no arguments provided, default to runserver
    if len(sys.argv) == 1:
        sys.argv = ['start_server.py', 'runserver', '0.0.0.0:8000', '--noreload']
    
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
