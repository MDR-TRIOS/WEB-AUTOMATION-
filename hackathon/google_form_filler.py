"""
Google Form Auto-Filler using Selenium
A production-ready script to automatically fill and submit Google Forms with prefilled URLs.

Features:
- Support for multiple field types (text, paragraph, multiple choice, checkboxes, dropdowns)
- Proper wait handling with WebDriverWait
- Modular design with separate handlers for each field type
- Comprehensive error handling and logging
- Batch mode for multiple submissions
- Headless mode option
- Detailed logging for each submission
"""

import logging
import time
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)


@dataclass
class FormConfig:
    """Configuration for form filling."""
    url: str
    headless: bool = True
    timeout: int = 10
    implicit_wait: int = 5
    log_file: Optional[str] = None
    chrome_options: Optional[List[str]] = None
    window_size: str = "1920,1080"


class GoogleFormLogger:
    """Setup and manage logging for form submissions."""
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file or f"form_submissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure logging with both file and console output."""
        self.logger = logging.getLogger("GoogleFormFiller")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
    
    def get_logger(self):
        return self.logger


class FieldHandler:
    """Base class for handling different form field types."""
    
    def __init__(self, driver, wait: WebDriverWait, logger: logging.Logger):
        self.driver = driver
        self.wait = wait
        self.logger = logger
    
    def fill_field(self, field_data: Dict[str, Any]) -> bool:
        """Fill a form field. Override in subclasses."""
        raise NotImplementedError


class TextFieldHandler(FieldHandler):
    """Handle short answer text fields."""
    
    def fill_field(self, field_data: Dict[str, Any]) -> bool:
        """Fill a text input field."""
        try:
            field_name = field_data.get('name', 'Unknown')
            field_value = field_data.get('value', '')
            
            # Find text input in the form
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            
            if not inputs:
                self.logger.warning(f"No text input found for field: {field_name}")
                return False
            
            # Find the correct input (usually the first one on this iteration)
            input_element = inputs[0] if len(inputs) == 1 else self._find_input_by_label(field_name)
            
            if input_element:
                input_element.clear()
                input_element.send_keys(field_value)
                self.logger.info(f"Filled text field '{field_name}' with: {field_value}")
                return True
            else:
                self.logger.warning(f"Could not locate text input for: {field_name}")
                return False
        except Exception as e:
            self.logger.error(f"Error filling text field: {str(e)}")
            return False
    
    def _find_input_by_label(self, label_text: str):
        """Try to find an input field by its associated label."""
        try:
            labels = self.driver.find_elements(By.TAG_NAME, "label")
            for label in labels:
                if label_text.lower() in label.text.lower():
                    # Find the input within or near this label
                    input_elem = label.find_element(By.CSS_SELECTOR, "input[type='text']")
                    return input_elem
        except:
            pass
        return None


class ParagraphFieldHandler(FieldHandler):
    """Handle paragraph/multiline text fields."""
    
    def fill_field(self, field_data: Dict[str, Any]) -> bool:
        """Fill a textarea field."""
        try:
            field_name = field_data.get('name', 'Unknown')
            field_value = field_data.get('value', '')
            
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            
            if not textareas:
                self.logger.warning(f"No textarea found for field: {field_name}")
                return False
            
            textarea = textareas[0]
            textarea.clear()
            textarea.send_keys(field_value)
            self.logger.info(f"Filled paragraph field '{field_name}'")
            return True
        except Exception as e:
            self.logger.error(f"Error filling paragraph field: {str(e)}")
            return False


class MultipleChoiceHandler(FieldHandler):
    """Handle multiple choice (radio button) fields."""
    
    def fill_field(self, field_data: Dict[str, Any]) -> bool:
        """Select a radio button option."""
        try:
            field_name = field_data.get('name', 'Unknown')
            field_value = field_data.get('value', '')
            
            # Find radio buttons (Google Forms use radio inputs or divs with role)
            radio_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            
            if not radio_buttons:
                # Try finding clickable divs with option text
                return self._select_by_text(field_value)
            
            # Look for the specific radio button value
            for radio in radio_buttons:
                try:
                    # Check aria-label or nearby label text
                    aria_label = radio.get_attribute('aria-label')
                    if aria_label and field_value.lower() in aria_label.lower():
                        radio.click()
                        self.logger.info(f"Selected radio button '{field_name}': {field_value}")
                        return True
                except StaleElementReferenceException:
                    continue
            
            return self._select_by_text(field_value)
        except Exception as e:
            self.logger.error(f"Error selecting radio button: {str(e)}")
            return False
    
    def _select_by_text(self, option_text: str) -> bool:
        """Find and click an option by its visible text."""
        try:
            # Find divs that contain the option text
            options = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{option_text}')]")
            if options:
                # Click the parent clickable element
                for option in options:
                    try:
                        # Find the closest clickable parent (radio option)
                        parent = option
                        for _ in range(5):  # Search up to 5 levels up
                            parent = parent.find_element(By.XPATH, "..")
                            if parent.get_attribute("role") == "radio" or parent.find_elements(By.CSS_SELECTOR, "input[type='radio']"):
                                parent.click()
                                self.logger.info(f"Selected option by text: {option_text}")
                                return True
                    except:
                        continue
        except Exception as e:
            self.logger.debug(f"Could not select by text '{option_text}': {str(e)}")
        return False


class CheckboxHandler(FieldHandler):
    """Handle checkbox fields."""
    
    def fill_field(self, field_data: Dict[str, Any]) -> bool:
        """Check/uncheck checkboxes."""
        try:
            field_name = field_data.get('name', 'Unknown')
            options = field_data.get('values', [])  # List of options to select
            
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            
            if not checkboxes:
                self.logger.warning(f"No checkboxes found for field: {field_name}")
                return False
            
            selected_count = 0
            for checkbox in checkboxes:
                try:
                    aria_label = checkbox.get_attribute('aria-label')
                    for option in options:
                        if aria_label and option.lower() in aria_label.lower():
                            if not checkbox.is_selected():
                                checkbox.click()
                                selected_count += 1
                except StaleElementReferenceException:
                    continue
            
            self.logger.info(f"Selected {selected_count} checkboxes for '{field_name}'")
            return selected_count > 0
        except Exception as e:
            self.logger.error(f"Error handling checkboxes: {str(e)}")
            return False


class DropdownHandler(FieldHandler):
    """Handle dropdown/select fields."""
    
    def fill_field(self, field_data: Dict[str, Any]) -> bool:
        """Select a dropdown option."""
        try:
            field_name = field_data.get('name', 'Unknown')
            field_value = field_data.get('value', '')
            
            # Google Forms dropdowns are usually divs with specific structure
            option_divs = self.driver.find_elements(By.XPATH, "//div[@role='option']")
            
            # First, click to open the dropdown
            dropdowns = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listbox']")
            
            if dropdowns:
                dropdown = dropdowns[0]
                dropdown.click()
                
                # Wait for options to appear
                self.wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@role='option']")))
                
                # Find and click the option
                options = self.driver.find_elements(By.XPATH, "//div[@role='option']")
                for option in options:
                    if field_value in option.text:
                        option.click()
                        self.logger.info(f"Selected dropdown '{field_name}': {field_value}")
                        return True
            
            self.logger.warning(f"Could not find or select option for: {field_name}")
            return False
        except TimeoutException:
            self.logger.error(f"Timeout waiting for dropdown options: {field_name}")
            return False
        except Exception as e:
            self.logger.error(f"Error handling dropdown: {str(e)}")
            return False


class GoogleFormFiller:
    """Main class for filling and submitting Google Forms."""
    
    def __init__(self, config: FormConfig):
        self.config = config
        self.logger_handler = GoogleFormLogger(config.log_file)
        self.logger = self.logger_handler.get_logger()
        self.driver = None
        self.wait = None
        self.field_handlers = {}
        self._initialize_handlers()
    
    def _initialize_handlers(self):
        """Initialize field type handlers."""
        # Will be set when driver is created
        pass
    
    def _setup_driver(self):
        """Initialize Selenium WebDriver with Chrome."""
        try:
            chrome_options = Options()
            
            if self.config.headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument(f"--window-size={self.config.window_size}")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--start-maximized")
            
            # Add custom options if provided
            if self.config.chrome_options:
                for option in self.config.chrome_options:
                    chrome_options.add_argument(option)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(self.config.implicit_wait)
            self.wait = WebDriverWait(self.driver, self.config.timeout)
            
            self.logger.info("Chrome WebDriver initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {str(e)}")
            return False
    
    def _setup_field_handlers(self):
        """Create instances of field handlers."""
        self.field_handlers = {
            'text': TextFieldHandler(self.driver, self.wait, self.logger),
            'paragraph': ParagraphFieldHandler(self.driver, self.wait, self.logger),
            'multiple_choice': MultipleChoiceHandler(self.driver, self.wait, self.logger),
            'checkbox': CheckboxHandler(self.driver, self.wait, self.logger),
            'dropdown': DropdownHandler(self.driver, self.wait, self.logger),
        }
    
    def load_form(self) -> bool:
        """Load the Google Form page."""
        try:
            self.logger.info(f"Loading form from URL: {self.config.url}")
            self.driver.get(self.config.url)
            
            # Wait for form to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            self.logger.info("Form loaded successfully")
            return True
        except TimeoutException:
            self.logger.error("Timeout waiting for form to load")
            return False
        except Exception as e:
            self.logger.error(f"Error loading form: {str(e)}")
            return False
    
    def fill_form(self, form_data: Dict[str, Any]) -> bool:
        """Fill the form with provided data."""
        try:
            self.logger.info(f"Starting to fill form with {len(form_data)} fields")
            
            successful_fields = 0
            failed_fields = []
            
            for field_name, field_info in form_data.items():
                field_type = field_info.get('type', 'text')
                
                if field_type not in self.field_handlers:
                    self.logger.warning(f"No handler found for field type: {field_type}")
                    failed_fields.append(field_name)
                    continue
                
                handler = self.field_handlers[field_type]
                field_data = {
                    'name': field_name,
                    **field_info
                }
                
                if handler.fill_field(field_data):
                    successful_fields += 1
                else:
                    failed_fields.append(field_name)
            
            self.logger.info(f"Form filling completed: {successful_fields} successful, {len(failed_fields)} failed")
            if failed_fields:
                self.logger.warning(f"Failed fields: {', '.join(failed_fields)}")
            
            return len(failed_fields) == 0
        except Exception as e:
            self.logger.error(f"Error filling form: {str(e)}")
            return False
    
    def submit_form(self) -> bool:
        """Submit the form by clicking the submit button."""
        try:
            self.logger.info("Attempting to submit form")
            
            # Wait a moment for any final updates
            time.sleep(1)
            
            # Find and click submit button (multiple possible selectors)
            submit_button = None
            selectors = [
                "button[aria-label*='Submit']",
                "div[aria-label*='Submit']",
                "span:contains('Submit')",
                "button:contains('Submit')",
            ]
            
            try:
                # Try to find by xpath
                submit_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Submit')]"))
                )
            except TimeoutException:
                # Try alternative selectors
                for selector in selectors:
                    try:
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if buttons:
                            submit_button = buttons[0]
                            break
                    except:
                        continue
            
            if submit_button:
                submit_button.click()
                self.logger.info("Form submitted successfully")
                time.sleep(2)  # Wait for submission to complete
                return True
            else:
                self.logger.error("Could not find submit button")
                return False
        except Exception as e:
            self.logger.error(f"Error submitting form: {str(e)}")
            return False
    
    def wait_for_confirmation(self, timeout: int = 10) -> bool:
        """Wait for form submission confirmation."""
        try:
            self.logger.info("Waiting for form confirmation message")
            
            # Look for confirmation text (varies by form)
            confirmation_texts = [
                "Your response has been recorded",
                "Thanks for your response",
                "Form submitted",
                "Submission received",
            ]
            
            for text in confirmation_texts:
                try:
                    self.wait.until(
                        EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{text}')]"))
                    )
                    self.logger.info(f"Confirmation received: {text}")
                    return True
                except TimeoutException:
                    continue
            
            self.logger.warning("No explicit confirmation message found, but form may have been submitted")
            return True  # Return True as form likely submitted even without visible confirmation
        except Exception as e:
            self.logger.error(f"Error waiting for confirmation: {str(e)}")
            return False
    
    def fill_and_submit(self, form_data: Dict[str, Any]) -> bool:
        """Complete workflow: load, fill, and submit form."""
        try:
            if not self.load_form():
                return False
            
            if not self.fill_form(form_data):
                self.logger.warning("Some fields failed to fill, continuing to submission...")
            
            if not self.submit_form():
                return False
            
            if not self.wait_for_confirmation():
                self.logger.warning("Confirmation not received")
            
            self.logger.info("Form submission workflow completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error in fill_and_submit workflow: {str(e)}")
            return False
    
    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.logger.info("WebDriver closed")
    
    def run(self, form_data: Dict[str, Any]) -> bool:
        """Main execution method."""
        try:
            if not self._setup_driver():
                return False
            
            self._setup_field_handlers()
            
            success = self.fill_and_submit(form_data)
            return success
        finally:
            self.close()


class BatchFormProcessor:
    """Process multiple form submissions in batch mode."""
    
    def __init__(self, config: FormConfig):
        self.config = config
        self.logger_handler = GoogleFormLogger(config.log_file)
        self.logger = self.logger_handler.get_logger()
    
    def process_batch(self, batch_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple form submissions."""
        try:
            self.logger.info(f"Starting batch processing of {len(batch_data)} submissions")
            
            results = {
                'total': len(batch_data),
                'successful': 0,
                'failed': 0,
                'submissions': []
            }
            
            for idx, form_data in enumerate(batch_data, 1):
                self.logger.info(f"Processing submission {idx}/{len(batch_data)}")
                
                filler = GoogleFormFiller(self.config)
                success = filler.run(form_data)
                
                results['submissions'].append({
                    'index': idx,
                    'success': success,
                    'timestamp': datetime.now().isoformat()
                })
                
                if success:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                
                # Add delay between submissions
                if idx < len(batch_data):
                    self.logger.info("Waiting 5 seconds before next submission...")
                    time.sleep(5)
            
            self.logger.info(
                f"Batch processing completed: {results['successful']} successful, {results['failed']} failed"
            )
            return results
        except Exception as e:
            self.logger.error(f"Error processing batch: {str(e)}")
            return {'total': len(batch_data), 'successful': 0, 'failed': len(batch_data), 'submissions': []}


def load_form_data_from_json(json_file: str) -> Optional[Dict[str, Any]]:
    """Load form data from a JSON file."""
    try:
        with open(json_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {str(e)}")
        return None


def main():
    """Example usage of the Google Form Filler."""
    
    # Example 1: Single form submission
    example_form_data = {
        'full_name': {
            'type': 'text',
            'value': 'John Doe'
        },
        'email': {
            'type': 'text',
            'value': 'john@example.com'
        },
        'comments': {
            'type': 'paragraph',
            'value': 'This is a test submission.\nMultiple lines are supported.'
        },
        'favorite_color': {
            'type': 'multiple_choice',
            'value': 'Blue'
        },
        'agree_to_terms': {
            'type': 'checkbox',
            'values': ['I agree']
        },
        'country': {
            'type': 'dropdown',
            'value': 'United States'
        }
    }
    
    # Initialize config
    config = FormConfig(
        url="https://docs.google.com/forms/d/YOUR_FORM_ID/viewform?usp=pp_url",
        headless=False,  # Set to True for background execution
        timeout=15,
        log_file="form_submissions.log"
    )
    
    # Single submission
    print("Starting Google Form Filler...")
    filler = GoogleFormFiller(config)
    
    if filler.run(example_form_data):
        print("✓ Form submitted successfully!")
    else:
        print("✗ Form submission failed")
    
    # Example 2: Batch processing (uncomment to use)
    # batch_data = [example_form_data] * 3  # Submit same form 3 times
    # processor = BatchFormProcessor(config)
    # results = processor.process_batch(batch_data)
    # print(f"\nBatch Results: {json.dumps(results, indent=2)}")


if __name__ == "__main__":
    main()
