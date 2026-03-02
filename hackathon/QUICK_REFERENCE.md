# Google Form Filler - Quick Reference Guide

## Installation (2 minutes)

```bash
# 1. Install dependencies
pip install -r requirements_form_filler.txt

# 2. Run setup verification
python setup_and_verify.py

# 3. You're ready!
```

## Basic Usage (5 minutes)

### Step 1: Get Your Form URL
```
https://docs.google.com/forms/d/YOUR_FORM_ID/viewform?usp=pp_url
```

### Step 2: Define Form Data
```python
form_data = {
    'full_name': {
        'type': 'text',
        'value': 'John Doe'
    },
    'email': {
        'type': 'text',
        'value': 'john@example.com'
    },
    'feedback': {
        'type': 'paragraph',
        'value': 'Great product!'
    },
    'rating': {
        'type': 'multiple_choice',
        'value': '5 Stars'
    },
    'subscribe': {
        'type': 'checkbox',
        'values': ['Yes']
    },
    'country': {
        'type': 'dropdown',
        'value': 'United States'
    }
}
```

### Step 3: Submit
```python
from google_form_filler import GoogleFormFiller, FormConfig

config = FormConfig(url="YOUR_FORM_URL", headless=False)
filler = GoogleFormFiller(config)
filler.run(form_data)
```

## Field Types Cheat Sheet

| Type | Example | Notes |
|------|---------|-------|
| **text** | `{'type': 'text', 'value': 'John'}` | Short answer |
| **paragraph** | `{'type': 'paragraph', 'value': 'Text\nwith\nlines'}` | Multi-line text |
| **multiple_choice** | `{'type': 'multiple_choice', 'value': 'Option'}` | Radio button (single) |
| **checkbox** | `{'type': 'checkbox', 'values': ['A', 'B']}` | Multiple selections |
| **dropdown** | `{'type': 'dropdown', 'value': 'Option'}` | Select menu |

## Common Commands

```bash
# Show help and examples
python usage_examples.py --help

# Run simple example
python usage_examples.py --example 1

# Run batch processing
python usage_examples.py --example 3

# Load from JSON file
python usage_examples.py --example 2

# View logs
tail -f form_submissions_*.log  # macOS/Linux
type form_submissions_*.log    # Windows PowerShell
```

## Code Examples

### Single Submission
```python
from google_form_filler import GoogleFormFiller, FormConfig

config = FormConfig(
    url="https://docs.google.com/forms/d/YOUR_ID/viewform?usp=pp_url",
    headless=False  # Show browser
)

form_data = {
    'name': {'type': 'text', 'value': 'Alice'},
    'email': {'type': 'text', 'value': 'alice@example.com'}
}

filler = GoogleFormFiller(config)
filler.run(form_data)
```

### Batch Processing
```python
from google_form_filler import BatchFormProcessor, FormConfig

batch_data = [
    {'name': {'type': 'text', 'value': 'Alice'}, ...},
    {'name': {'type': 'text', 'value': 'Bob'}, ...},
    {'name': {'type': 'text', 'value': 'Carol'}, ...}
]

config = FormConfig(url="YOUR_URL", headless=True)
processor = BatchFormProcessor(config)
results = processor.process_batch(batch_data)

print(f"Success: {results['successful']}/{results['total']}")
```

### Load from JSON
```python
import json
from google_form_filler import GoogleFormFiller, FormConfig

# Create example_form_data.json first
with open('example_form_data.json', 'r') as f:
    form_data = json.load(f)

config = FormConfig(url="YOUR_URL")
filler = GoogleFormFiller(config)
filler.run(form_data)
```

### Advanced Configuration
```python
from google_form_filler import GoogleFormFiller, FormConfig

config = FormConfig(
    url="YOUR_URL",
    headless=True,              # Background mode
    timeout=20,                 # Wait up to 20 seconds
    log_file="my_log.log",      # Custom log file
    window_size="1920x1080",    # Browser window size
    chrome_options=[            # Custom Chrome options
        "--disable-extensions",
        "--disable-plugins",
        "--incognito"
    ]
)

filler = GoogleFormFiller(config)
filler.run(form_data)
```

## Configuration Options

```python
FormConfig(
    url: str,                           # Form URL (required)
    headless: bool = True,              # Run without showing browser
    timeout: int = 10,                  # Max wait for elements (seconds)
    implicit_wait: int = 5,             # Implicit wait (seconds)
    log_file: Optional[str] = None,     # Log file path
    chrome_options: Optional[List] = None,  # Extra Chrome args
    window_size: str = "1920,1080"     # Browser size
)
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `No module named 'selenium'` | `pip install -r requirements_form_filler.txt` |
| `Chrome not found` | Install Google Chrome or Chromium |
| `Element not clickable` | Increase `timeout` parameter |
| `Form not loading` | Check URL, increase `timeout` to 20-30 |
| `Field not filling` | Verify field value matches exactly (case-sensitive) |
| `Confirmation not detected` | Check logs, form may still have submitted |

## Files Overview

| File | Purpose |
|------|---------|
| `google_form_filler.py` | Main module (all functionality) |
| `usage_examples.py` | 6 practical examples to get started |
| `setup_and_verify.py` | Verify setup is correct |
| `example_form_data.json` | Single submission example data |
| `batch_form_data.json` | Batch submission example (3 entries) |
| `requirements_form_filler.txt` | Python dependencies |
| `FORM_FILLER_README.md` | Comprehensive documentation |

## Tips & Tricks

### 1. Finding Field Names
```
Right-click on form field → Inspect → Look for:
- <input name="entry.123456789">
- aria-label attribute
- nearby <label> text
```

### 2. Testing Before Batch
```python
# Test with headless=False first
config = FormConfig(url="YOUR_URL", headless=False)
# Watch browser to see what's happening
filler = GoogleFormFiller(config)
filler.run(single_test_data)
```

### 3. Exact Field Matching
```python
# ✅ CORRECT - exact match
{'type': 'multiple_choice', 'value': 'Very Satisfied'}

# ❌ WRONG - won't work
{'type': 'multiple_choice', 'value': 'Very satisfied'}  # Case different
{'type': 'multiple_choice', 'value': 'Satisfied'}       # Partial text
```

### 4. Multi-line Text
```python
# Use \n for line breaks
{
    'feedback': {
        'type': 'paragraph',
        'value': 'Line 1\nLine 2\nLine 3'
    }
}
```

### 5. Run in Background
```python
config = FormConfig(
    url="YOUR_URL",
    headless=True  # Won't show browser window
)
```

### 6. Add Delays Between Submissions
```python
# Batch processor automatically adds 5-second delays
# For custom delays in manual loops:
import time
time.sleep(5)  # Wait 5 seconds
```

## Performance

| Scenario | Time |
|----------|------|
| Single form | 5-15 seconds |
| 10 forms (batch) | 1-2 minutes |
| 100 forms (batch) | 10-20 minutes |

*Times vary based on form complexity and network speed*

## Logging

Logs automatically created as: `form_submissions_YYYYMMDD_HHMMSS.log`

Example log contents:
```
2024-01-15 10:30:45,123 - INFO - Loading form from URL: https://...
2024-01-15 10:30:47,456 - INFO - Form loaded successfully
2024-01-15 10:30:48,789 - INFO - Filled text field 'name' with: John Doe
2024-01-15 10:30:49,012 - INFO - Selected option by text: Option 1
2024-01-15 10:30:50,345 - INFO - Form submitted successfully
2024-01-15 10:30:52,678 - INFO - Confirmation received
```

## Python Versions

- **Minimum**: Python 3.8
- **Recommended**: Python 3.10+
- **Tested**: Python 3.9, 3.10, 3.11

## Browser Support

- **Chrome** (recommended)
- **Chromium** (compatible)
- **Edge** (with configuration)

## What's NOT Supported

- ❌ File uploads
- ❌ Image uploads
- ❌ Signature fields
- ❌ Date pickers (partially)
- ❌ Custom widgets

## Getting Help

1. **Check logs**: `form_submissions_*.log` files contain detailed error messages
2. **Set headless=False**: Watch the browser to see what's happening
3. **Read docs**: `FORM_FILLER_README.md` has comprehensive documentation
4. **Try examples**: Run `python usage_examples.py --example 5` to test all field types
5. **Increase timeout**: Set `timeout=30` for slow networks

## License & Usage

This script is provided as-is for educational and automation purposes. Use responsibly and comply with Google's Terms of Service.

---

**Last Updated**: January 2024  
**Version**: 1.0.0  
**Status**: Production Ready ✅
