"""
Google Form AutoFiller Helper for home.html
Generates prefilled URLs and submits forms with predefined data
"""

import json
import time
import webbrowser
from datetime import datetime
from google_form_filler import GoogleFormFiller, FormConfig, BatchFormProcessor

# Sample data to prefill
SAMPLE_DATA = {
    'full_name': {
        'type': 'text',
        'value': 'Surendra Purohit'
    },
    'email': {
        'type': 'text',
        'value': 'surendra.purohit@example.com'
    },
    'address': {
        'type': 'text',
        'value': '45, MG Road, Chennai, Tamil Nadu, India'
    },
    'phone_number': {
        'type': 'text',
        'value': '9123456780'
    },
    'college': {
        'type': 'text',
        'value': 'XYZ Institute of Technology'
    },
    'department': {
        'type': 'text',
        'value': 'Information Technology'
    },
    'option_1': {
        'type': 'multiple_choice',
        'value': 'Selected'
    }
}

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdNV2pI7jglx3rWn0Prq4VQuFU-nZxim9zc_y9RpX35QGEpZg/viewform"


def open_prefilled_form_simple():
    """Open the form in browser (simple method - manual prefill)"""
    print("📂 Opening Google Form in default browser...")
    webbrowser.open(FORM_URL)


def open_prefilled_form_selenium():
    """Open and prefill the form using Selenium (automated method)"""
    try:
        print("🤖 Starting automated form filling with Selenium...")
        
        config = FormConfig(
            url=FORM_URL,
            headless=False,  # Show browser so user can see
            timeout=15,
            log_file=f"autofill_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        
        filler = GoogleFormFiller(config)
        
        print("📊 Submitting form with sample data...")
        print(f"   Name: {SAMPLE_DATA['full_name']['value']}")
        print(f"   Email: {SAMPLE_DATA['email']['value']}")
        print(f"   Address: {SAMPLE_DATA['address']['value']}")
        print(f"   Phone: {SAMPLE_DATA['phone_number']['value']}")
        print(f"   College: {SAMPLE_DATA['college']['value']}")
        print(f"   Department: {SAMPLE_DATA['department']['value']}")
        
        success = filler.run(SAMPLE_DATA)
        
        if success:
            print("✅ Form submitted successfully!")
        else:
            print("⚠️  Form submission completed with some warnings - check logs")
            
        return success
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("💡 Tip: Make sure Selenium and Chrome are installed")
        return False


def generate_prefilled_url():
    """Generate a prefilled URL (limited by Google Forms restrictions)"""
    # Note: Google Forms has limitations on what can be prefilled via URL
    # This is a basic example - most fields need to be filled via form interaction
    
    url = FORM_URL + "?usp=pp_url"
    
    # Common field patterns (these may need to be customized for your form)
    try_fields = {
        'Name': 'Surendra Purohit',
        'Email': 'surendra.purohit@example.com',
        'Phone': '9123456780',
        'Address': '45, MG Road, Chennai, Tamil Nadu, India',
        'College': 'XYZ Institute of Technology',
        'Department': 'Information Technology'
    }
    
    for field_name, field_value in try_fields.items():
        url += f"&entry.{field_name}={field_value.replace(' ', '+')}"
    
    return url


def print_help():
    """Print help information"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║     GOOGLE FORM AUTOFILL HELPER                                ║
╚════════════════════════════════════════════════════════════════╝

USAGE:

    python form_autofill_helper.py [option]

OPTIONS:

    1. simple     - Opens form in browser (manual prefill)
    2. selenium   - Uses Selenium to automatically fill and submit
    3. url        - Print the prefilled URL
    4. help       - Show this help message

EXAMPLES:

    python form_autofill_helper.py simple      # Open form manually
    python form_autofill_helper.py selenium    # Auto-fill with Selenium
    python form_autofill_helper.py url         # Get prefilled URL
    python form_autofill_helper.py help        # Show this help

FEATURES:

    ✅ Opens Google Form in your default browser
    ✅ Automatically fills form fields with sample data
    ✅ Generates prefilled URL for sharing
    ✅ Logs all activities to file

DATA BEING USED:

    Name: Surendra Purohit
    Email: surendra.purohit@example.com
    Address: 45, MG Road, Chennai, Tamil Nadu, India
    Phone: 9123456780
    College: XYZ Institute of Technology
    Department: Information Technology
    Option: Selected

NOTES:

    • Simple method: Opens form, you fill manually
    • Selenium method: Automatically fills and submits
    • URL method: Limited prefilling (Google Forms restrictions)
    • Check logs for detailed information

TROUBLESHOOTING:

    If Selenium method fails:
    1. Ensure Chrome is installed
    2. Run: pip install -r requirements_form_filler.txt
    3. Try simple method instead

    """)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        option = sys.argv[1].lower()
        
        if option == 'simple':
            open_prefilled_form_simple()
        elif option == 'selenium':
            open_prefilled_form_selenium()
        elif option == 'url':
            url = generate_prefilled_url()
            print(f"📋 Prefilled URL:\n\n{url}\n")
            print("💡 Copy this URL to share the prefilled form link")
        elif option == 'help':
            print_help()
        else:
            print(f"Unknown option: {option}\n")
            print_help()
    else:
        # Default: show help
        print_help()
