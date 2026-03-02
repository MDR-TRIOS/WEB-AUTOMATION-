# Google Form Filler with Selenium

A production-ready Python script to automatically fill out and submit Google Forms using Selenium WebDriver.

## Features

✅ **Multiple Field Types Support**
- Short answer text fields
- Paragraph/multiline text fields
- Multiple choice (radio buttons)
- Checkboxes
- Dropdowns/select fields

✅ **Robust Design**
- WebDriverWait for proper element synchronization
- Comprehensive error handling
- Detailed logging for debugging
- Modular architecture with separate handlers for each field type
- Stale element reference handling

✅ **Advanced Capabilities**
- Headless mode option for background execution
- Batch processing for multiple submissions
- Dynamic form loading detection
- Confirmation page handling
- Chrome WebDriver customization

✅ **Production Ready**
- Clean, well-documented code
- Logging to both console and file
- Exception handling for edge cases
- Timeout configuration
- Configurable wait times

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements_form_filler.txt
```

Or manually:
```bash
pip install selenium>=4.0.0 webdriver-manager>=4.0.0
```

2. **Ensure Chrome is installed** (compatible with your OS)

## Quick Start

### 1. Get Your Prefilled Form URL

Google Forms supports prefilled URLs with this format:
```
https://docs.google.com/forms/d/{FORM_ID}/viewform?usp=pp_url&entry.{FIELD_ID}={VALUE}
```

To get field IDs, use the form in incognito mode and inspect the network requests or form HTML.

### 2. Simple Single Submission

```python
from google_form_filler import GoogleFormFiller, FormConfig

config = FormConfig(
    url="https://docs.google.com/forms/d/YOUR_FORM_ID/viewform?usp=pp_url",
    headless=False  # Set True for background execution
)

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
    'satisfaction': {
        'type': 'multiple_choice',
        'value': 'Very Satisfied'
    },
    'subscribe': {
        'type': 'checkbox',
        'values': ['Yes, subscribe me']
    }
}

filler = GoogleFormFiller(config)
success = filler.run(form_data)

if success:
    print("✓ Form submitted successfully!")
else:
    print("✗ Form submission failed")
```

### 3. Batch Processing

```python
from google_form_filler import BatchFormProcessor, FormConfig

config = FormConfig(url="YOUR_FORM_URL", headless=True)

batch_data = [
    {
        'name': {'type': 'text', 'value': 'User 1'},
        'feedback': {'type': 'paragraph', 'value': 'Great!'}
    },
    {
        'name': {'type': 'text', 'value': 'User 2'},
        'feedback': {'type': 'paragraph', 'value': 'Excellent!'}
    }
]

processor = BatchFormProcessor(config)
results = processor.process_batch(batch_data)

print(f"Successful: {results['successful']}/{results['total']}")
```

## Configuration Options

### FormConfig Parameters

```python
FormConfig(
    url: str,                          # Google Form URL (required)
    headless: bool = True,             # Run browser in headless mode
    timeout: int = 10,                 # WebDriverWait timeout in seconds
    implicit_wait: int = 5,            # Implicit wait for elements
    log_file: Optional[str] = None,    # Log file path (auto-generated if None)
    chrome_options: Optional[List[str]] = None,  # Additional Chrome options
    window_size: str = "1920,1080"     # Browser window size
)
```

## Field Types

### Text Field
```python
{
    'field_name': {
        'type': 'text',
        'value': 'Your text here'
    }
}
```

### Paragraph Field
```python
{
    'field_name': {
        'type': 'paragraph',
        'value': 'Multi-line text\nwith multiple lines\nof content'
    }
}
```

### Multiple Choice (Radio Button)
```python
{
    'field_name': {
        'type': 'multiple_choice',
        'value': 'Option Text'  # Must match exactly
    }
}
```

### Checkboxes
```python
{
    'field_name': {
        'type': 'checkbox',
        'values': ['Option 1', 'Option 3']  # List of options to check
    }
}
```

### Dropdown
```python
{
    'field_name': {
        'type': 'dropdown',
        'value': 'Selected Option'
    }
}
```

## Usage Examples

### Example 1: Load Form Data from JSON

```python
import json
from google_form_filler import GoogleFormFiller, FormConfig

# Load form data from JSON file
with open('example_form_data.json', 'r') as f:
    form_data = json.load(f)

config = FormConfig(url="YOUR_FORM_URL")
filler = GoogleFormFiller(config)
filler.run(form_data)
```

### Example 2: Batch Processing from JSON

```python
import json
from google_form_filler import BatchFormProcessor, FormConfig

with open('batch_form_data.json', 'r') as f:
    batch_data = json.load(f)

config = FormConfig(
    url="YOUR_FORM_URL",
    headless=True,
    log_file="batch_submissions.log"
)

processor = BatchFormProcessor(config)
results = processor.process_batch(batch_data)

print(json.dumps(results, indent=2))
```

### Example 3: Custom Chrome Options

```python
from google_form_filler import GoogleFormFiller, FormConfig

config = FormConfig(
    url="YOUR_FORM_URL",
    chrome_options=[
        "--disable-extensions",
        "--disable-plugins",
        "--incognito"
    ]
)

filler = GoogleFormFiller(config)
filler.run(form_data)
```

### Example 4: Extended Timeout for Slow Networks

```python
from google_form_filler import GoogleFormFiller, FormConfig

config = FormConfig(
    url="YOUR_FORM_URL",
    timeout=30,           # Wait up to 30 seconds for elements
    implicit_wait=10      # 10 second implicit wait
)

filler = GoogleFormFiller(config)
filler.run(form_data)
```

## Logging

Logs are automatically saved to `form_submissions_YYYYMMDD_HHMMSS.log` by default.

Log files contain:
- Timestamp of each operation
- Field fill attempts and results
- Error messages with stack traces
- Form submission status
- Confirmation page detection

Example log output:
```
2024-01-15 10:30:45 - INFO - Loading form from URL: https://docs.google.com/forms/...
2024-01-15 10:30:48 - INFO - Form loaded successfully
2024-01-15 10:30:49 - INFO - Starting to fill form with 5 fields
2024-01-15 10:30:49 - INFO - Filled text field 'full_name' with: John Doe
2024-01-15 10:30:49 - INFO - Selecting dropdown 'country': United States
2024-01-15 10:30:51 - INFO - Form submitted successfully
2024-01-15 10:30:53 - INFO - Confirmation received: Your response has been recorded
```

## Advanced Topics

### How to Find Google Form Field IDs

1. Open the form in **Incognito Mode** (Ctrl+Shift+N)
2. Right-click on a field → **Inspect**
3. Look for the `name` attribute or `entry.XXXXX` in the HTML
4. Build your prefilled URL with these IDs:
   ```
   https://docs.google.com/forms/d/FORM_ID/viewform?usp=pp_url&entry.123456789=value1&entry.987654321=value2
   ```

### Handling Dynamic Fields

For forms that load fields dynamically:
1. Increase the `timeout` parameter in FormConfig
2. The script automatically waits for form loading

### Dealing with Required Fields

The script includes error handling for required fields. If a field fails to fill, it logs the failure and continues. Check the log file to identify which fields need attention.

### Debugging Failed Submissions

1. Set `headless=False` to see the browser in action
2. Check the generated log file for detailed error messages
3. Inspect the form HTML to verify field selectors
4. Test with a single field first before batch processing

## Troubleshooting

### Issue: "ChromeDriver version mismatch"
**Solution:** webdriver-manager automatically handles this, or manually download matching ChromeDriver from https://chromedriver.chromium.org/

### Issue: "Element not clickable" or "Stale element reference"
**Solution:** The script handles these automatically with retries and proper waits. If persistent, increase the `timeout` parameter.

### Issue: "Form not loaded" timeout
**Solution:** 
- Increase `timeout` parameter to 20-30 seconds
- Check your internet connection
- Verify the URL is correct

### Issue: Fields not filling correctly
**Solution:**
- Ensure field values in form_data match exactly (case-sensitive for dropdowns)
- Use `headless=False` to see what's happening
- Check the generated log file for specific field failures

### Issue: Form not submitting
**Solution:**
- Verify there's a Submit button visible
- Check if form validation is preventing submission
- Look at the log file for submission errors

## Performance Tips

1. **Use headless mode** for faster execution:
   ```python
   config = FormConfig(url="...", headless=True)
   ```

2. **Batch processing** is efficient for multiple submissions - they're queued sequentially with delays

3. **Reduce waits** if your network is fast:
   ```python
   config = FormConfig(url="...", timeout=5, implicit_wait=2)
   ```

4. **Run in background** with `headless=True` to free up your desktop

## Architecture

### Class Hierarchy

```
GoogleFormFiller (Main class)
├── FormConfig (Configuration dataclass)
├── GoogleFormLogger (Logging setup)
└── Field Handlers:
    ├── TextFieldHandler
    ├── ParagraphFieldHandler
    ├── MultipleChoiceHandler
    ├── CheckboxHandler
    └── DropdownHandler

BatchFormProcessor (For batch operations)
└── Uses GoogleFormFiller internally
```

### Module Design

- **Modular handlers**: Each field type has a dedicated handler class
- **Separation of concerns**: Logging, config, and filling are separate
- **Extensible**: Easy to add new field types by creating new handler classes
- **Error resilience**: Each field fills independently with error handling

## Contributing & Extending

To add support for a new field type:

```python
class CustomFieldHandler(FieldHandler):
    """Handle custom field type."""
    
    def fill_field(self, field_data: Dict[str, Any]) -> bool:
        """Fill the custom field."""
        try:
            # Implementation
            return True
        except Exception as e:
            self.logger.error(f"Error: {str(e)}")
            return False
```

Then register in `GoogleFormFiller._setup_field_handlers()`:
```python
self.field_handlers['custom'] = CustomFieldHandler(...)
```

## Limitations

1. **Dynamic JavaScript-heavy forms**: May require additional waits
2. **Custom field types**: Requires creating custom handlers
3. **File uploads**: Not supported (can be added with `send_keys()` to file inputs)
4. **Signature fields**: Not supported
5. **Linear forms**: Better suited for standard forms than complex branching logic

## Security Considerations

- **Don't hardcode credentials**: Use environment variables or secure vaults
- **Be cautious with sensitive data**: Forms filled with PII should use secure logging
- **Verify form URLs**: Ensure you're submitting to legitimate forms
- **Use HTTPS**: Always use secure connections

## License

This script is provided as-is for educational and automation purposes.

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Review the troubleshooting section
3. Verify your form URL and field configurations
4. Test with `headless=False` to observe behavior

---

**Last Updated:** January 2024  
**Selenium Version:** 4.0+  
**Python Version:** 3.8+
