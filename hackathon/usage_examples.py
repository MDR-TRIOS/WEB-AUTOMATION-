"""
Practical usage examples for Google Form Filler
Demonstrates different ways to use the google_form_filler module
"""

import json
import sys
from pathlib import Path
from google_form_filler import (
    GoogleFormFiller,
    BatchFormProcessor,
    FormConfig,
    load_form_data_from_json
)


def example_1_simple_submission():
    """Example 1: Simple single form submission."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Simple Single Form Submission")
    print("="*60)
    
    # You MUST update this URL with your actual Google Form URL
    FORM_URL = "https://docs.google.com/forms/d/YOUR_FORM_ID/viewform?usp=pp_url"
    
    if "YOUR_FORM_ID" in FORM_URL:
        print("⚠️  Please update FORM_URL with your actual Google Form URL!")
        return
    
    form_data = {
        'full_name': {
            'type': 'text',
            'value': 'John Doe'
        },
        'email': {
            'type': 'text',
            'value': 'john.doe@example.com'
        },
        'message': {
            'type': 'paragraph',
            'value': 'This is a test submission.\nMultiple lines work too!'
        },
        'satisfaction': {
            'type': 'multiple_choice',
            'value': 'Very Satisfied'
        }
    }
    
    config = FormConfig(
        url=FORM_URL,
        headless=False,  # Set True to run in background
        timeout=15
    )
    
    print("\n📝 Submitting form with single entry...")
    filler = GoogleFormFiller(config)
    
    if filler.run(form_data):
        print("✅ Form submitted successfully!")
    else:
        print("❌ Form submission failed - check logs for details")


def example_2_load_from_json():
    """Example 2: Load form data from JSON file."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Load Form Data from JSON")
    print("="*60)
    
    FORM_URL = "https://docs.google.com/forms/d/YOUR_FORM_ID/viewform?usp=pp_url"
    json_file = "example_form_data.json"
    
    if "YOUR_FORM_ID" in FORM_URL:
        print("⚠️  Please update FORM_URL with your actual Google Form URL!")
        return
    
    if not Path(json_file).exists():
        print(f"⚠️  File '{json_file}' not found!")
        return
    
    form_data = load_form_data_from_json(json_file)
    if not form_data:
        return
    
    config = FormConfig(url=FORM_URL, headless=False)
    
    print(f"\n📋 Loaded form data from '{json_file}'")
    print(f"📝 Submitting form with {len(form_data)} fields...")
    
    filler = GoogleFormFiller(config)
    if filler.run(form_data):
        print("✅ Form submitted successfully!")
    else:
        print("❌ Form submission failed")


def example_3_batch_processing():
    """Example 3: Batch processing multiple form submissions."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Batch Processing Multiple Submissions")
    print("="*60)
    
    FORM_URL = "https://docs.google.com/forms/d/YOUR_FORM_ID/viewform?usp=pp_url"
    
    if "YOUR_FORM_ID" in FORM_URL:
        print("⚠️  Please update FORM_URL with your actual Google Form URL!")
        return
    
    # Create sample batch data (3 submissions)
    batch_data = [
        {
            'name': {'type': 'text', 'value': 'Alice Johnson'},
            'email': {'type': 'text', 'value': 'alice@example.com'},
            'feedback': {'type': 'paragraph', 'value': 'Excellent service!'}
        },
        {
            'name': {'type': 'text', 'value': 'Bob Wilson'},
            'email': {'type': 'text', 'value': 'bob@example.com'},
            'feedback': {'type': 'paragraph', 'value': 'Very good experience.'}
        },
        {
            'name': {'type': 'text', 'value': 'Carol Davis'},
            'email': {'type': 'text', 'value': 'carol@example.com'},
            'feedback': {'type': 'paragraph', 'value': 'Great product overall!'}
        }
    ]
    
    config = FormConfig(
        url=FORM_URL,
        headless=True,  # Background execution for batch
        log_file="batch_submissions.log"
    )
    
    print(f"\n📊 Starting batch processing with {len(batch_data)} submissions...")
    processor = BatchFormProcessor(config)
    results = processor.process_batch(batch_data)
    
    print(f"\n✅ Batch completed:")
    print(f"   Total: {results['total']}")
    print(f"   Successful: {results['successful']}")
    print(f"   Failed: {results['failed']}")
    print(f"\n📋 Detailed results saved to: {config.log_file}")


def example_4_batch_from_json():
    """Example 4: Batch processing from JSON file."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Batch Processing from JSON File")
    print("="*60)
    
    FORM_URL = "https://docs.google.com/forms/d/YOUR_FORM_ID/viewform?usp=pp_url"
    json_file = "batch_form_data.json"
    
    if "YOUR_FORM_ID" in FORM_URL:
        print("⚠️  Please update FORM_URL with your actual Google Form URL!")
        return
    
    if not Path(json_file).exists():
        print(f"⚠️  File '{json_file}' not found!")
        return
    
    with open(json_file, 'r') as f:
        batch_data = json.load(f)
    
    config = FormConfig(
        url=FORM_URL,
        headless=True,
        log_file="batch_from_json.log"
    )
    
    print(f"\n📋 Loaded {len(batch_data)} entries from '{json_file}'")
    print("📝 Starting batch submissions...")
    
    processor = BatchFormProcessor(config)
    results = processor.process_batch(batch_data)
    
    print(f"\n✅ Batch completed: {results['successful']}/{results['total']} successful")


def example_5_all_field_types():
    """Example 5: Demonstrate all supported field types."""
    print("\n" + "="*60)
    print("EXAMPLE 5: All Field Types Demonstration")
    print("="*60)
    
    FORM_URL = "https://docs.google.com/forms/d/YOUR_FORM_ID/viewform?usp=pp_url"
    
    if "YOUR_FORM_ID" in FORM_URL:
        print("⚠️  Please update FORM_URL with your actual Google Form URL!")
        return
    
    # Demo of all field types
    complete_form_data = {
        # Text field
        'first_name': {
            'type': 'text',
            'value': 'John'
        },
        
        # Another text field
        'last_name': {
            'type': 'text',
            'value': 'Smith'
        },
        
        # Paragraph field
        'bio': {
            'type': 'paragraph',
            'value': 'Tell us about yourself...\nYou can write multiple paragraphs.\nLike this one.'
        },
        
        # Multiple choice
        'favorite_color': {
            'type': 'multiple_choice',
            'value': 'Blue'  # Exact match required
        },
        
        # Checkboxes (multiple selection)
        'interests': {
            'type': 'checkbox',
            'values': ['Technology', 'Design']  # Array of selections
        },
        
        # Dropdown
        'country': {
            'type': 'dropdown',
            'value': 'United States'
        }
    }
    
    config = FormConfig(
        url=FORM_URL,
        headless=False,
        timeout=20  # More time for comprehensive form
    )
    
    print("\n📝 Submitting comprehensive form with all field types...")
    print("   - Text fields: first_name, last_name")
    print("   - Paragraph field: bio")
    print("   - Multiple choice: favorite_color")
    print("   - Checkboxes: interests")
    print("   - Dropdown: country")
    
    filler = GoogleFormFiller(config)
    
    if filler.run(complete_form_data):
        print("\n✅ Complex form submitted successfully!")
    else:
        print("\n❌ Form submission failed")


def example_6_custom_config():
    """Example 6: Advanced configuration options."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Advanced Configuration")
    print("="*60)
    
    FORM_URL = "https://docs.google.com/forms/d/YOUR_FORM_ID/viewform?usp=pp_url"
    
    if "YOUR_FORM_ID" in FORM_URL:
        print("⚠️  Please update FORM_URL with your actual Google Form URL!")
        return
    
    form_data = {
        'email': {'type': 'text', 'value': 'test@example.com'},
        'message': {'type': 'paragraph', 'value': 'Test message'}
    }
    
    # Advanced configuration
    config = FormConfig(
        url=FORM_URL,
        headless=True,                    # Background mode
        timeout=20,                       # 20 second timeout for slow networks
        implicit_wait=10,                 # 10 second implicit wait
        log_file="advanced_config.log",   # Custom log file
        window_size="1280,720",           # Custom window size
        chrome_options=[                  # Additional Chrome options
            "--disable-extensions",
            "--disable-plugins",
            "--incognito"
        ]
    )
    
    print("\n⚙️  Using advanced configuration:")
    print(f"   Headless: {config.headless}")
    print(f"   Timeout: {config.timeout}s")
    print(f"   Implicit Wait: {config.implicit_wait}s")
    print(f"   Log File: {config.log_file}")
    print(f"   Window Size: {config.window_size}")
    
    print("\n📝 Submitting with custom configuration...")
    
    filler = GoogleFormFiller(config)
    if filler.run(form_data):
        print("✅ Form submitted successfully!")
    else:
        print("❌ Form submission failed")


def print_usage_guide():
    """Print a quick usage guide."""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║           GOOGLE FORM FILLER - USAGE GUIDE                                ║
╚═══════════════════════════════════════════════════════════════════════════╝

QUICK START:

1. Update the FORM_URL in the example with your actual Google Form URL
   Format: https://docs.google.com/forms/d/{FORM_ID}/viewform?usp=pp_url

2. Prepare your form data (see examples below)

3. Run the appropriate example:
   
   python usage_examples.py --example 1  # Simple submission
   python usage_examples.py --example 2  # Load from JSON
   python usage_examples.py --example 3  # Batch processing
   python usage_examples.py --example 5  # All field types demo

FIELD TYPES:

  Text Field:
    'field_name': {
        'type': 'text',
        'value': 'Your text here'
    }

  Paragraph Field:
    'field_name': {
        'type': 'paragraph',
        'value': 'Multi-line\\ntext here'
    }

  Multiple Choice:
    'field_name': {
        'type': 'multiple_choice',
        'value': 'Option Name'
    }

  Checkboxes:
    'field_name': {
        'type': 'checkbox',
        'values': ['Option 1', 'Option 2']
    }

  Dropdown:
    'field_name': {
        'type': 'dropdown',
        'value': 'Selected Option'
    }

IMPORTANT NOTES:

• Field values must match the form exactly (case-sensitive for dropdowns)
• Use --headless for background execution
• Check log files for detailed error messages
• Start with headless=False to see what's happening
• Batch processing adds 5-second delays between submissions

RUN OPTIONS:

python usage_examples.py                            # Show this guide
python usage_examples.py --example 1                # Run example 1
python usage_examples.py --example 2                # Run example 2
python usage_examples.py --example 3                # Run example 3
python usage_examples.py --example 4                # Run example 4
python usage_examples.py --example 5                # Run example 5
python usage_examples.py --example 6                # Run example 6

""")


if __name__ == "__main__":
    print("\n🚀 Google Form Filler - Usage Examples\n")
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--example":
            example_num = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            
            examples = {
                1: example_1_simple_submission,
                2: example_2_load_from_json,
                3: example_3_batch_processing,
                4: example_4_batch_from_json,
                5: example_5_all_field_types,
                6: example_6_custom_config
            }
            
            if example_num in examples:
                try:
                    examples[example_num]()
                except KeyboardInterrupt:
                    print("\n\n⚠️  Interrupted by user")
                except Exception as e:
                    print(f"\n❌ Error: {str(e)}")
                    print("Check the log file for detailed information")
            else:
                print(f"Example {example_num} not found. Available: 1-6")
        elif sys.argv[1] == "--help":
            print_usage_guide()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information")
    else:
        print_usage_guide()
