# Google Form AutoFill Integration Guide

## Overview

Your home.html has been enhanced with a **Forms** button in the top navbar that provides easy access to Google Form filling with autofill capabilities.

## Features

✅ **Easy to Use**: Click the Forms button in the navbar  
✅ **Autofill Support**: Pre-fills forms with sample data  
✅ **Manual Option**: Open form manually if preferred  
✅ **Beautiful Modal**: Modern UI for form options  
✅ **Multiple Methods**: Browser-based and Selenium-powered options  

## How to Use

### Method 1: Using the HTML Interface (Browser-Based)

1. **Click the Forms Button**
   - Look for the **📝 Forms** button in the top navbar
   - A modal will appear with two options

2. **Choose an Option**
   - **AutoFill Form with Sample Data**: Opens the form (see details below)
   - **Open Form Manually**: Opens the form in a new tab for manual filling

3. **Sample Data Being Used**
   ```
   Name: Surendra Purohit
   Email: surendra.purohit@example.com
   Address: 45, MG Road, Chennai, Tamil Nadu, India
   Phone Number: 9123456780
   College: XYZ Institute of Technology
   Department: Information Technology
   Option: Selected
   ```

### Method 2: Using Python Helper Script (Automated Filling)

For automated form filling with the Selenium library:

#### Installation

```bash
cd c:\Users\surendra purohit\Downloads\hackathon
pip install -r requirements_form_filler.txt
```

#### Usage

**Option 1: Simple (Manual Filling)**
```bash
python form_autofill_helper.py simple
```
Opens the form in your default browser for manual filling.

**Option 2: Selenium (Automated Filling)**
```bash
python form_autofill_helper.py selenium
```
Automatically fills all fields and submits the form. Browser window will be visible so you can watch it happen.

**Option 3: Get Prefilled URL**
```bash
python form_autofill_helper.py url
```
Generates a prefilled URL that you can share or use.

**Option 4: Show Help**
```bash
python form_autofill_helper.py help
```
Displays help information and usage examples.

## Files Included

| File | Purpose |
|------|---------|
| `home.html` | Main page with Forms button and autofill modal |
| `form_autofill_helper.py` | Python helper for automated form filling |
| `google_form_filler.py` | Core Selenium automation module |
| `usage_examples.py` | Example usage patterns |
| `requirements_form_filler.txt` | Python dependencies |

## Google Form URL

The target form is:
```
https://docs.google.com/forms/d/e/1FAIpQLSdNV2pI7jglx3rWn0Prq4VQuFU-nZxim9zc_y9RpX35QGEpZg/viewform
```

## How It Works

### Browser Method (HTML + JavaScript)

1. User clicks **Forms** button in navbar
2. Modal appears with options
3. User clicks **AutoFill Form with Sample Data**
4. JavaScript generates a prefilled URL and opens it
5. Form opens with some fields preloaded (Google Forms limitations)

**Note**: Google Forms restricts URL-based prefilling for security reasons. Some fields may not be pre-filled via URL.

### Selenium Method (Python Script)

1. User runs `python form_autofill_helper.py selenium`
2. Python script launches Chrome browser automatically
3. Selenium navigates to the Google Form
4. Script fills each field with the predefined data
5. Script clicks the Submit button
6. Form is submitted successfully

**Advantages**:
- ✅ Fills ALL field types (text, paragraphs, dropdowns, checkboxes, radio buttons)
- ✅ Much more reliable than URL-based prefilling
- ✅ Handles dynamic form loading
- ✅ Provides detailed logs

## Customizing the Sample Data

### To Change Data in HTML Interface

Edit **home.html**, find the `formData` object:

```javascript
const formData = {
    name: "Surendra Purohit",
    email: "surendra.purohit@example.com",
    address: "45, MG Road, Chennai, Tamil Nadu, India",
    phone: "9123456780",
    college: "XYZ Institute of Technology",
    dept: "Information Technology",
    option: "Option 1"
};
```

Update with your desired values, then save.

### To Change Data in Python Script

Edit **form_autofill_helper.py**, find the `SAMPLE_DATA` dictionary:

```python
SAMPLE_DATA = {
    'full_name': {
        'type': 'text',
        'value': 'Your Name Here'
    },
    'email': {
        'type': 'text',
        'value': 'your.email@example.com'
    },
    # ... more fields
}
```

Then run: `python form_autofill_helper.py selenium`

## Supported Field Types

The automation supports the following Google Form field types:

- ✅ **Short Answer (Text)**: Single-line text input
- ✅ **Paragraph**: Multi-line text input
- ✅ **Multiple Choice**: Radio buttons
- ✅ **Checkboxes**: Multi-select options
- ✅ **Dropdown**: Select from list
- ✅ **Linear Scale**: Rating scale (1-5)

## Troubleshooting

### Issue: Form opens but fields are not prefilled

**Solution**: This is a Google Forms limitation for URL-based prefilling. Use the Selenium method instead:
```bash
python form_autofill_helper.py selenium
```

### Issue: "Chrome not found" error with Selenium method

**Solution**:
1. Install Google Chrome from https://www.google.com/chrome/
2. Or install Chromium: `pip install chromium`
3. Then try: `python form_autofill_helper.py selenium`

### Issue: Python script says "module not found"

**Solution**:
```bash
pip install -r requirements_form_filler.txt
```

### Issue: Form doesn't submit automatically

**Solution**:
1. Ensure all required fields are filled (form will reject submission if required fields are empty)
2. Check the log file for details
3. Verify field names match your form's actual field names

## Advanced: Using the Google Form Filler Module Directly

For custom automation scenarios:

```python
from google_form_filler import GoogleFormFiller, FormConfig

config = FormConfig(
    url="https://docs.google.com/forms/d/e/1FAIpQLSdNV2pI7jglx3rWn0Prq4VQuFU-nZxim9zc_y9RpX35QGEpZg/viewform",
    headless=False
)

form_data = {
    'field_name': {
        'type': 'text',  # or 'paragraph', 'multiple_choice', 'checkbox', 'dropdown'
        'value': 'Your value'
    }
}

filler = GoogleFormFiller(config)
filler.run(form_data)
```

## Quick Reference

**Opening form from HTML:**
1. Open home.html in browser
2. Click **📝 Forms** button
3. Choose **AutoFill Form** or **Open Form Manually**

**Opening form from Python:**
```bash
# Quick open (manual fill)
python form_autofill_helper.py simple

# Auto-fill (Selenium)
python form_autofill_helper.py selenium

# Get URL for sharing
python form_autofill_helper.py url
```

## Tips & Best Practices

1. **Test First**: Try with simple form before complex ones
2. **Use Correct Data**: Ensure field values match form expectations
3. **Check Logs**: Always review log files if something fails
4. **Multi-fill**: Batch processing available for multiple forms
5. **Headless Mode**: Set `headless=True` in config for background execution

## Performance

| Method | Speed | Reliability | 
|--------|-------|-------------|
| HTML Browser Method | Very Fast (instant) | Medium (limited prefilling) |
| Python Simple | Very Fast (1-2 sec) | Medium (manual filling needed) |
| Python Selenium | Medium (10-20 sec) | High (automated) |

## Data Privacy

- ✅ All data processing happens locally on your machine
- ✅ No data is stored or sent anywhere (except to Google Forms)
- ✅ You control what data is used
- ✅ Logs are saved locally for review

## Need More Help?

Check these resources:

1. **QUICK_REFERENCE.md** - Quick start guide
2. **FORM_FILLER_README.md** - Comprehensive documentation
3. **usage_examples.py** - Working code examples
4. **form_autofill_helper.py --help** - Command help

## License & Usage

This integration is provided as-is for educational and personal automation purposes. Always respect Google's Terms of Service and form owners' wishes.

---

**Last Updated**: March 3, 2026  
**Status**: Ready to Use ✅

**Quick Start Checklist**:
- [ ] Opened home.html in browser
- [ ] Saw the Forms button in navbar
- [ ] Clicked Forms and saw the modal
- [ ] Tested opening form manually
- [ ] (Optional) Installed Python dependencies
- [ ] (Optional) Tested Python autofill script
