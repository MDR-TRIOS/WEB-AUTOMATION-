#!/usr/bin/env python
"""
Setup and Verification Script for Google Form Filler
Checks dependencies and helps configure the environment
"""

import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def check_python_version():
    """Check if Python version is compatible."""
    print_header("1. Checking Python Version")
    
    version = sys.version_info
    min_version = (3, 8)
    
    if version >= min_version:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} is too old")
        print(f"   Minimum required: Python {min_version[0]}.{min_version[1]}")
        return False


def check_dependencies():
    """Check if required packages are installed."""
    print_header("2. Checking Dependencies")
    
    required_packages = {
        'selenium': '4.0.0',
        'webdriver_manager': '4.0.0'
    }
    
    all_ok = True
    
    for package, min_version in required_packages.items():
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is NOT installed")
            print(f"   Install with: pip install {package}>={min_version}")
            all_ok = False
    
    return all_ok


def check_files():
    """Check if required files exist."""
    print_header("3. Checking Required Files")
    
    required_files = [
        'google_form_filler.py',
        'usage_examples.py',
        'example_form_data.json',
        'batch_form_data.json'
    ]
    
    all_ok = True
    
    for filename in required_files:
        if Path(filename).exists():
            file_size = Path(filename).stat().st_size
            print(f"✅ {filename} ({file_size} bytes)")
        else:
            print(f"❌ {filename} NOT FOUND")
            all_ok = False
    
    return all_ok


def check_chrome_browser():
    """Check if Chrome browser is available."""
    print_header("4. Checking Chrome Browser")
    
    try:
        result = subprocess.run(
            ['where', 'chrome'] if sys.platform == 'win32' else ['which', 'google-chrome'],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ Chrome browser is installed")
            return True
    except:
        pass
    
    print("⚠️  Chrome browser not found in PATH")
    print("   WebDriver manager will attempt to download chromedriver automatically")
    print("   Make sure Chrome/Chromium is installed on your system")
    return None


def install_dependencies():
    """Install required dependencies."""
    print_header("5. Installing Dependencies")
    
    try:
        print("📦 Installing required packages...")
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements_form_filler.txt'],
            check=True
        )
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        print("   Try running manually: pip install -r requirements_form_filler.txt")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def run_diagnostics():
    """Run diagnostic tests."""
    print_header("6. Running Diagnostics")
    
    try:
        # Test Selenium import
        from selenium import webdriver
        from selenium.webdriver.support.ui import WebDriverWait
        print("✅ Selenium module imported successfully")
        
        # Test WebDriver Manager import
        from webdriver_manager.chrome import ChromeDriverManager
        print("✅ WebDriver Manager imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        return False


def print_next_steps():
    """Print next steps for the user."""
    print_header("NEXT STEPS")
    
    print("""
1. GET YOUR GOOGLE FORM URL:
   - Open your Google Form
   - Click "Share" and get the form link
   - Format: https://docs.google.com/forms/d/{FORM_ID}/viewform

2. FIND FIELD NAMES:
   - Inspect the form with browser DevTools (F12)
   - Look for field names or entry IDs
   - Or use prefillfURL with entry parameters

3. PREPARE YOUR DATA:
   - Create form_data dictionary with field information
   - See example_form_data.json for format
   - Use correct field types: text, paragraph, multiple_choice, checkbox, dropdown

4. RUN AN EXAMPLE:
   - python usage_examples.py --help        # See all options
   - python usage_examples.py --example 1   # Try first example
   - Edit the FORM_URL in usage_examples.py with your form URL

5. CUSTOMIZE FOR YOUR FORM:
   - Update field names to match your form
   - Ensure field values match exactly
   - Test with headless=False first to see what's happening

6. BATCH PROCESSING:
   - Create batch_form_data.json with multiple entries
   - Run: python usage_examples.py --example 4
   - Check logs for results

USEFUL COMMANDS:

  # View help
  python usage_examples.py --help

  # Run example 1 (simple submission)
  python usage_examples.py --example 1

  # Run example 3 (batch processing)
  python usage_examples.py --example 3

  # Check form filler logs
  tail -f form_submissions_*.log

  # View documentation
  cat FORM_FILLER_README.md

QUICK TEST:

  1. Open your Google Form in a browser
  2. Update the FORM_URL in usage_examples.py (line ~30)
  3. Update the form_data fields to match your form
  4. Run: python usage_examples.py --example 1
  5. Watch the browser fill your form automatically!

TROUBLESHOOTING:

  ❓ "Chrome not found"
     → Install Google Chrome if not already installed
     → Or use Chromium/Edge with custom options

  ❓ "Element not found"
     → Check field names in form_data match your form
     → Set headless=False to see what's happening
     → Check the generated log file for errors

  ❓ "Form not submitting"
     → Increase timeout in FormConfig
     → Check browser console for validation errors
     → Ensure all required fields are filled

  ❓ "Stale element reference"
     → This is handled automatically
     → If persistent, increase timeout value

Need more help? See FORM_FILLER_README.md for comprehensive documentation.
""")


def main():
    """Run all checks."""
    print("\n" + "="*70)
    print("  GOOGLE FORM FILLER - SETUP & VERIFICATION")
    print("="*70)
    
    checks = [
        ("Python Version", check_python_version),
        ("Files", check_files),
        ("Chrome Browser", check_chrome_browser),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ Error during {name} check: {str(e)}")
            results[name] = False
    
    # Check and install dependencies
    print_header("2. Checking & Installing Dependencies")
    
    if not check_dependencies():
        print("\n📦 Installing missing packages...")
        install_dependencies()
    
    # Run diagnostics
    run_diagnostics()
    
    # Summary
    print_header("SUMMARY")
    
    all_ok = all(results.values())
    
    for name, result in results.items():
        status = "✅" if result else "⚠️" if result is None else "❌"
        print(f"{status} {name}: {'OK' if result else 'Warning' if result is None else 'Failed'}")
    
    if all_ok:
        print("\n✅ All checks passed! You're ready to use Google Form Filler.\n")
    else:
        print("\n⚠️  Some checks failed or showed warnings.\n")
        print("Please address any issues before proceeding.\n")
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
