#!/usr/bin/env python3
"""Check Python syntax for all files"""

import ast
import os
import sys

def check_file(filename):
    """Check if a Python file has valid syntax"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        print(f"✅ {filename} - Syntax OK")
        return True
    except SyntaxError as e:
        print(f"❌ {filename} - Syntax Error: {e}")
        return False
    except Exception as e:
        print(f"⚠️ {filename} - Error reading: {e}")
        return False

def main():
    """Check all Python files in the backend directory"""
    python_files = [
        'main.py',
        'workflow.py', 
        'auth.py',
        'mcp_tools.py'
    ]
    
    print("🔍 Checking Python syntax...")
    all_good = True
    
    for filename in python_files:
        if os.path.exists(filename):
            if not check_file(filename):
                all_good = False
        else:
            print(f"⚠️ {filename} - File not found")
    
    if all_good:
        print("\n🎉 All Python files have valid syntax!")
        return 0
    else:
        print("\n❌ Some files have syntax errors!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 