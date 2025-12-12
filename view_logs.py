#!/usr/bin/env python3
"""
View PythonAnywhere error logs in a readable way
Shows last N lines and filters for errors

Usage:
    python3 view_logs.py [--lines N] [--errors-only]
"""

import sys
import argparse
from pathlib import Path

def view_logs(num_lines=50, errors_only=False):
    """View error logs from PythonAnywhere"""
    
    # Common log file locations
    possible_logs = [
        Path.home() / "logs" / "error.log",
        Path("/var/log/error.log"),
        Path.home() / "error.log",
    ]
    
    log_file = None
    for log_path in possible_logs:
        if log_path.exists():
            log_file = log_path
            break
    
    if not log_file:
        print("Error log file not found in common locations.")
        print("Looking for:")
        for log_path in possible_logs:
            print(f"  - {log_path}")
        print("\nTo find your log file:")
        print("1. Go to PythonAnywhere Web tab")
        print("2. Click on your web app")
        print("3. Check 'Error log' section for the file path")
        return
    
    print(f"Reading: {log_file}")
    print("=" * 70)
    print()
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
            # Get last N lines
            if len(lines) > num_lines:
                lines = lines[-num_lines:]
                print(f"Showing last {num_lines} lines (total: {len(lines)} lines in file)")
            else:
                print(f"Showing all {len(lines)} lines")
            
            print()
            
            # Filter for errors if requested
            if errors_only:
                error_lines = []
                for i, line in enumerate(lines):
                    if any(keyword in line.lower() for keyword in 
                           ['error', 'exception', 'traceback', 'failed', '✗']):
                        error_lines.append((i + len(lines) - num_lines + 1, line))
                
                if error_lines:
                    print("ERRORS FOUND:")
                    print("-" * 70)
                    for line_num, line in error_lines:
                        print(f"Line {line_num}: {line.rstrip()}")
                else:
                    print("No errors found in the selected lines.")
            else:
                # Show all lines with line numbers
                start_line = len(lines) - num_lines + 1 if len(lines) > num_lines else 1
                for i, line in enumerate(lines, start=start_line):
                    # Highlight error lines
                    if any(keyword in line.lower() for keyword in 
                           ['error', 'exception', 'traceback']):
                        print(f"⚠ {i}: {line.rstrip()}")
                    else:
                        print(f"  {i}: {line.rstrip()}")
    
    except PermissionError:
        print(f"Permission denied: Cannot read {log_file}")
        print("Try running with appropriate permissions")
    except Exception as e:
        print(f"Error reading log file: {e}")

def main():
    parser = argparse.ArgumentParser(description='View PythonAnywhere error logs')
    parser.add_argument('--lines', '-n', type=int, default=50,
                       help='Number of lines to show (default: 50)')
    parser.add_argument('--errors-only', '-e', action='store_true',
                       help='Show only error lines')
    
    args = parser.parse_args()
    
    view_logs(args.lines, args.errors_only)

if __name__ == "__main__":
    main()

