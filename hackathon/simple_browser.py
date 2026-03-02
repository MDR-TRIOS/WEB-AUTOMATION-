import sys
import warnings
# Suppress PyQt5 deprecation warnings (not related to our code)
warnings.filterwarnings('ignore', category=DeprecationWarning)

from google.genai import Client
import json
import time
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtGui import QFont, QColor
from bs4 import BeautifulSoup
import threading
import os

# Clean up QtWebEngine cache if needed
cache_dir = os.path.expandvars(r'%LOCALAPPDATA%\My Simple Browser')
if os.path.exists(cache_dir):
    try:
        import shutil
        shutil.rmtree(cache_dir, ignore_errors=True)
    except:
        pass

# Initialize Gemini AI client
AI_CLIENT = Client(api_key="AIzaSyAnrLYoIfnNG1ZajefTXpDOiRYj7H_hRUc")

# Signal definitions for thread-safe GUI updates
class ChatSignals(QObject):
    """Defines signals for thread-safe communication"""
    tab_opened = pyqtSignal(str)  # tab_name
    chat_message = pyqtSignal(str)  # HTML message
    status_message = pyqtSignal(str)  # status text

class BrowserTab:
    """Represents a single browser tab with metadata"""
    def __init__(self, tab_id, browser_view, label="New Tab"):
        self.tab_id = tab_id
        self.browser_view = browser_view
        self.label = label
        self.url = ""
        self.is_loading = False
        self.task_info = None

class TaskExecutor:
    """Execute browser tasks from chatbot commands"""
    
    COMMON_SEARCHES = {
        "amazon": "https://www.amazon.in/s?k=",
        "flipkart": "https://www.flipkart.com/search?q=",
        "ebay": "https://www.ebay.com/sch/i.html?_nkw=",
        "google": "https://www.google.com/search?q=",
        "youtube": "https://www.youtube.com/results?search_query=",
        "reddit": "https://www.reddit.com/search?q=",
        "github": "https://github.com/search?q=",
    }
    
    # Direct website URLs (not search)
    WEBSITE_SHORTCUTS = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "facebook": "https://www.facebook.com",
        "twitter": "https://www.twitter.com",
        "instagram": "https://www.instagram.com",
        "github": "https://www.github.com",
        "stackoverflow": "https://www.stackoverflow.com",
        "reddit": "https://www.reddit.com",
        "linkedin": "https://www.linkedin.com",
        "amazon": "https://www.amazon.com",
        "flipkart": "https://www.flipkart.com",
        "ebay": "https://www.ebay.com",
        "wikipedia": "https://www.wikipedia.org",
        "quora": "https://www.quora.com",
        "medium": "https://www.medium.com",
    }
    
    # Fallback search options
    FALLBACK_SEARCHES = {
        "google_scholar": "https://scholar.google.com/scholar?q=",
        "bing": "https://www.bing.com/search?q=",
        "duckduckgo": "https://duckduckgo.com/?q=",
    }
    
    @staticmethod
    def parse_task(user_message):
        """Parse user message to extract task intent and parameters"""
        import re
        msg_lower = user_message.lower()
        
        # Check for parallel tasks (numbered, comma-separated, or with "and"/"also")
        if any(sep in msg_lower for sep in [",", "and", "also"]) or re.search(r'^\s*\d+\.', user_message):
            return TaskExecutor.parse_parallel_tasks(user_message)
        
        # Search on specific platform
        for platform, url_template in TaskExecutor.COMMON_SEARCHES.items():
            if f"search {platform}" in msg_lower or f"{platform} search" in msg_lower:
                return {
                    "type": "search",
                    "platform": platform,
                    "query": user_message.replace(f"search {platform}", "").replace(f"{platform} search", "").strip(),
                    "url_template": url_template
                }
        
        # Generic search
        if any(keyword in msg_lower for keyword in ["search for", "find", "look for", "search google"]):
            return {
                "type": "search",
                "platform": "google",
                "query": user_message.replace("search for", "").replace("search", "").replace("find", "").replace("look for", "").strip(),
                "url_template": TaskExecutor.COMMON_SEARCHES["google"]
            }
        
        # Compare prices
        if "compare" in msg_lower or "price" in msg_lower:
            return {
                "type": "compare",
                "query": user_message,
                "platforms": ["amazon", "flipkart", "ebay"]
            }
        
        # Open URL or website
        if "open" in msg_lower or "visit" in msg_lower:
            return {
                "type": "navigate",
                "url": user_message
            }
        
        # Extract info
        if "extract" in msg_lower or "scrape" in msg_lower:
            return {
                "type": "extract",
                "command": user_message
            }
        
        return {
            "type": "query",
            "message": user_message
        }
    
    @staticmethod
    def parse_parallel_tasks(user_message):
        """Parse multiple tasks from a single message, including compound tasks"""
        import re
        
        tasks = []
        task_strings = []
        
        # Check if numbered format (1. 2. 3. etc)
        if re.search(r'^\s*\d+\.', user_message):
            # Split using lookahead to keep boundaries clear before each numbered task
            parts = re.split(r'(?=\d+\.\s*open)', user_message, flags=re.IGNORECASE)
            # Each part now starts with "1. open...", "2. open...", etc.
            # Remove leading number from each part
            for part in parts:
                part = part.strip()
                if part:
                    # Remove the leading "N. " (number, dot, spaces)
                    part = re.sub(r'^\s*\d+\.\s*', '', part, flags=re.IGNORECASE)
                    if part:
                        task_strings.append(part)
        else:
            # Try comma-separated format
            task_strings = [t.strip() for t in user_message.split(',') if t.strip()]
        
        # Parse each task string
        for task_str in task_strings:
            if not task_str:
                continue
            
            task_lower = task_str.lower()
            
            # Try to match compound task: "open X and search for [quoted?]Y"
            # First try quoted content with high priority
            quoted_match = re.search(
                r'open\s+(\w+)\s+and\s+(?:search\s+for\s+)?(?:a\s+\w+\s+)?["\']([^"\']+)["\']',
                task_str,
                re.IGNORECASE
            )
            
            if quoted_match:
                site = quoted_match.group(1).lower()
                query = quoted_match.group(2).strip()
                
                # Find platform
                platform = site
                if platform not in TaskExecutor.COMMON_SEARCHES:
                    for p in TaskExecutor.COMMON_SEARCHES.keys():
                        if site.startswith(p) or p in site:
                            platform = p
                            break
                
                search_template = TaskExecutor.COMMON_SEARCHES.get(platform, "")
                
                tasks.append({
                    "type": "compound",
                    "site": site,
                    "platform": platform,
                    "search_query": query,
                    "search_template": search_template
                })
            else:
                # Fallback: match unquoted (look for pattern: open X and search for Y...)
                unquoted_match = re.search(
                    r'open\s+(\w+)\s+and\s+search\s+(?:for\s+)?(?:a\s+\w+\s+)?(\w+(?:\s+\w+)*?)(?:\s*$|\s+\d+\.)',
                    task_str,
                    re.IGNORECASE
                )
                
                if unquoted_match:
                    site = unquoted_match.group(1).lower()
                    query = unquoted_match.group(2).strip()
                    query = re.sub(r'[\s,\.]+$', '', query).strip()
                    
                    # Find platform
                    platform = site
                    if platform not in TaskExecutor.COMMON_SEARCHES:
                        for p in TaskExecutor.COMMON_SEARCHES.keys():
                            if site.startswith(p) or p in site:
                                platform = p
                                break
                    
                    search_template = TaskExecutor.COMMON_SEARCHES.get(platform, "")
                    
                    tasks.append({
                        "type": "compound",
                        "site": site,
                        "platform": platform,
                        "search_query": query,
                        "search_template": search_template
                    })
                elif "open" in task_lower:
                    # Simple navigation
                    url = re.sub(r'open\s+', '', task_str, flags=re.IGNORECASE).strip()
                    url = re.sub(r'[\d\.\s,\.]+$', '', url).strip()
                    if url:
                        tasks.append({"type": "navigate", "url": url})
        
        return {"type": "parallel", "tasks": tasks}

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        
        # Initialize signals for thread-safe updates
        self.signals = ChatSignals()
        self.signals.tab_opened.connect(self.on_tab_opened_signal)
        self.signals.chat_message.connect(self.on_chat_message_signal)
        self.signals.status_message.connect(self.on_status_message_signal)
        
        # Initialize tab management
        self.tabs = {}  # Dictionary to store BrowserTab objects by tab_id
        self.tab_counter = 0
        self.current_tab_id = None
        
        # Main layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        
        # Left panel: Tab cards
        left_panel = QWidget()
        left_panel_layout = QVBoxLayout()
        left_panel_layout.setContentsMargins(0, 0, 0, 0)
        left_panel_layout.setSpacing(0)
        
        # Create container for grid
        tabs_container = QWidget()
        tabs_container.setStyleSheet("""
            QWidget {
                background: #ffffff;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        self.tabs_layout = QGridLayout()
        self.tabs_layout.setSpacing(12)
        self.tabs_layout.setContentsMargins(12, 12, 12, 12)
        tabs_container.setLayout(self.tabs_layout)
        
        # Add container to layout and push to top with stretch at bottom
        left_panel_layout.addWidget(tabs_container, 0, Qt.AlignTop)
        left_panel_layout.addStretch()
        left_panel.setLayout(left_panel_layout)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(left_panel)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumWidth(320)
        scroll_area.setStyleSheet("""
            QScrollArea { 
                background: #fafafa;
                border-right: 1px solid #e0e0e0;
            }
            QScrollBar:vertical { background-color: #f5f5f5; width: 12px; }
            QScrollBar::handle:vertical { 
                background: #cccccc;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: #999999; }
        """)
        
        # Right panel: Browser view
        self.browser_container = QWidget()
        self.browser_container.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-left: 1px solid #e0e0e0;
            }
        """)
        browser_layout = QVBoxLayout()
        browser_layout.setContentsMargins(0, 0, 0, 0)
        self.browser_container.setLayout(browser_layout)
        
        # Initialize url_bar before creating first tab
        self.url_bar = None
        
        # Create initial home tab
        self.create_new_tab(is_home=True)
        
        # Add panels to main layout
        main_layout.addWidget(scroll_area, 1)
        main_layout.addWidget(self.browser_container, 3)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Task tracking
        self.active_tasks = {}
        self.task_counter = 0
        self.page_load_timer = None
        self.current_task = None
        
        # Reference to current browser view
        self.browser = None

        # Chatbox (Dock Widget)
        self.chat_dock = QDockWidget("Chat", self)
        self.chat_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        
        chat_widget = QWidget()
        chat_widget.setStyleSheet("""
            QWidget {
                background: #ffffff;
            }
        """)
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(10, 10, 10, 10)
        chat_layout.setSpacing(8)
        
        # Chat history label
        chat_label = QLabel("💬 Chat Assistant")
        chat_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-weight: 700;
                font-size: 14px;
                padding: 10px 12px;
                background: #111111;
                border-radius: 6px;
                border-left: 4px solid #444444;
            }
        """)
        chat_layout.addWidget(chat_label)
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                color: #111111;
                selection-background-color: #cccccc;
            }
        """)
        chat_layout.addWidget(self.chat_history)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask me to search, compare prices, or perform tasks...")
        self.chat_input.setMinimumHeight(42)
        self.chat_input.returnPressed.connect(self.send_chat_message)
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 13px;
                color: #111111;
                selection-background-color: #cccccc;
            }
            QLineEdit:focus {
                border: 1px solid #111111;
                background-color: #ffffff;
            }
        """)
        chat_layout.addWidget(self.chat_input)
        
        chat_widget.setLayout(chat_layout)
        self.chat_dock.setWidget(chat_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.chat_dock)

        self.showMaximized()

        # Premium, modern, monochrome UI styling
        self.setStyleSheet("""
            QMainWindow { background: #fafafa; }
            QToolBar {
                background: #ffffff;
                border-bottom: 1px solid #e0e0e0;
                spacing: 8px;
                padding: 10px 16px;
                min-height: 48px;
            }
            QToolBar::separator { background-color: #e0e0e0; width: 1px; margin: 0 8px; }
            QToolButton {
                color: #111111;
                background: #ffffff;
                border: 1px solid #e0e0e0;
                padding: 10px 18px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                margin: 3px;
                transition: all 0.2s;
            }
            QToolButton:hover {
                background: #f0f0f0;
                color: #000000;
                border: 1px solid #cccccc;
            }
            QToolButton:pressed {
                background: #111111;
                color: #ffffff;
                border: 1px solid #111111;
            }
            QLineEdit {
                background: #ffffff;
                color: #111111;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px 18px;
                font-size: 14px;
                font-weight: 500;
                margin: 0 6px;
            }
            QLineEdit:focus {
                border: 1px solid #111111;
            }
            QStatusBar {
                background: #ffffff;
                color: #111111;
                border-top: 1px solid #e0e0e0;
                font-weight: 500;
                font-size: 13px;
                padding: 8px 16px;
            }
            QDockWidget {
                color: #111111;
                background: #ffffff;
                border-top: 1px solid #e0e0e0;
            }
            QDockWidget::title {
                background: #f5f5f5;
                color: #111111;
                padding: 14px;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                border-radius: 10px 10px 0 0;
                font-weight: 600;
                font-size: 14px;
            }
            QTextEdit {
                background: #ffffff;
                color: #111111;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            QLabel {
                color: #111111;
                font-weight: 600;
                font-size: 14px;
            }
        """)

        navbar = QToolBar()
        navbar.setMovable(False)
        self.addToolBar(navbar)

        back_btn = QAction('◀ Back', self)
        back_btn.triggered.connect(self.on_back_clicked)
        navbar.addAction(back_btn)

        forward_btn = QAction('▶ Forward', self)
        forward_btn.triggered.connect(self.on_forward_clicked)
        navbar.addAction(forward_btn)

        navbar.addSeparator()

        reload_btn = QAction('🔄 Reload', self)
        reload_btn.triggered.connect(self.on_reload_clicked)
        navbar.addAction(reload_btn)

        home_btn = QAction('🏠 Home', self)
        home_btn.triggered.connect(self.navigate_home)
        navbar.addAction(home_btn)
        
        navbar.addSeparator()
        
        new_tab_btn = QAction('+ New Tab', self)
        new_tab_btn.triggered.connect(lambda: self.create_new_tab(is_home=True))
        navbar.addAction(new_tab_btn)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL or search...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.url_bar.setMinimumHeight(32)
        navbar.addWidget(self.url_bar)

        navbar.addSeparator()

        scrape_btn = QAction('📄 Scrape Page', self)
        scrape_btn.triggered.connect(self.scrape_page)
        navbar.addAction(scrape_btn)

        text_extractor_btn = QAction('📋 Text Extract', self)
        text_extractor_btn.triggered.connect(self.open_text_extractor)
        navbar.addAction(text_extractor_btn)

        # Status Bar for Link Previews
        self.status = QStatusBar()
        self.setStatusBar(self.status)

    def create_new_tab(self, url="", label="New Tab", is_home=False, set_as_current=True):
        """Create a new tab with a browser view"""
        self.tab_counter += 1
        tab_id = self.tab_counter
        print(f"DEBUG create_new_tab: Creating tab #{tab_id} with label='{label}', is_home={is_home}, set_as_current={set_as_current}")
        
        # Create browser view
        browser_view = QWebEngineView()
        
        # Create BrowserTab object
        browser_tab = BrowserTab(tab_id, browser_view, label)
        self.tabs[tab_id] = browser_tab
        print(f"DEBUG create_new_tab: BrowserTab #{tab_id} created, total tabs now = {len(self.tabs)}")
        
        # Set tab content
        if is_home:
            import os
            home_path = os.path.abspath('home.html').replace('\\', '/')
            browser_view.setUrl(QUrl(f'file:///{home_path}'))
            label = "Home"
        elif url:
            browser_view.setUrl(QUrl(url))
        
        # Connect signals
        browser_view.loadFinished.connect(lambda success, tid=tab_id: self.on_page_load_finished(success, tid))
        browser_view.loadStarted.connect(lambda tid=tab_id: self.on_page_load_started(tid))
        browser_view.urlChanged.connect(self.update_url_bar)
        browser_view.page().linkHovered.connect(lambda url: self.update_status_bar(url))
        
        # Create tab card button
        print(f"DEBUG create_new_tab: Calling create_tab_card for tab #{tab_id}")
        self.create_tab_card(tab_id, label)
        
        # Switch to this tab if requested
        if set_as_current:
            print(f"DEBUG create_new_tab: set_as_current=True, switching to tab #{tab_id}")
            self.switch_to_tab(tab_id)
        else:
            print(f"DEBUG create_new_tab: set_as_current=False, NOT switching to tab #{tab_id}")
        
        print(f"DEBUG create_new_tab: Tab #{tab_id} creation complete")
        return tab_id
    
    def create_tab_card(self, tab_id, label):
        """Create a clickable card for the tab"""
        print(f"DEBUG create_tab_card: Creating card for tab #{tab_id}, label='{label}'")
        card = QPushButton(label)
        card.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 16px;
                font-weight: 600;
                color: #111111;
                text-align: left;
                font-size: 13px;
                margin: 3px;
            }
            QPushButton:hover {
                background: #f5f5f5;
                border: 1px solid #cccccc;
            }
            QPushButton:pressed {
                background: #111111;
                color: #ffffff;
                border: 1px solid #111111;
            }
        """)
        card.setMinimumHeight(80)
        card.setCursor(Qt.PointingHandCursor)
        card.clicked.connect(lambda: self.switch_to_tab(tab_id))
        
        # Store reference to card
        self.tabs[tab_id].card = card
        
        # Add to grid layout
        index = len(self.tabs) - 1  # 0-based index
        row = index // 2
        col = index % 2
        print(f"DEBUG create_tab_card: Adding card to grid at row={row}, col={col}")
        self.tabs_layout.addWidget(card, row, col)
        print(f"DEBUG create_tab_card: Card #{tab_id} added to grid successfully")
    
    def switch_to_tab(self, tab_id):
        """Switch to a specific tab"""
        print(f"DEBUG switch_to_tab: Switching to tab #{tab_id}")
        if tab_id not in self.tabs:
            print(f"DEBUG switch_to_tab: Tab #{tab_id} NOT FOUND in self.tabs!")
            return
        
        print(f"DEBUG switch_to_tab: Tab #{tab_id} found. Total tabs = {len(self.tabs)}")
        
        # Clear previous browser from container
        layout = self.browser_container.layout()
        while layout.count():
            widget = layout.takeAt(0).widget()
            if widget:
                widget.setParent(None)
                print(f"DEBUG switch_to_tab: Removed widget from layout")
        
        # Set current tab
        self.current_tab_id = tab_id
        self.browser = self.tabs[tab_id].browser_view
        
        # Add browser to container
        layout.addWidget(self.browser)
        print(f"DEBUG switch_to_tab: Added browser view #{tab_id} to container")
        
        # Update URL bar
        self.update_url_bar()
        
        # Update card styling
        for tid, tab in self.tabs.items():
            if hasattr(tab, 'card'):
                if tid == tab_id:
                    tab.card.setStyleSheet("""
                        QPushButton {
                            background: #111111;
                            border: 1px solid #111111;
                            border-radius: 8px;
                            padding: 16px;
                            font-weight: 600;
                            color: #ffffff;
                            text-align: left;
                            font-size: 13px;
                            margin: 3px;
                            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                        }
                        QPushButton:hover {
                            background: #333333;
                            border: 1px solid #333333;
                        }
                    """)
                    print(f"DEBUG switch_to_tab: Highlighted card for tab #{tab_id}")
                else:
                    tab.card.setStyleSheet("""
                        QPushButton {
                            background: #ffffff;
                            border: 1px solid #e0e0e0;
                            border-radius: 8px;
                            padding: 16px;
                            font-weight: 600;
                            color: #111111;
                            text-align: left;
                            font-size: 13px;
                            margin: 3px;
                        }
                        QPushButton:hover {
                            background: #f5f5f5;
                            border: 1px solid #cccccc;
                        }
                    """)
        
        print(f"DEBUG switch_to_tab: Successfully switched to tab #{tab_id}")
    
    def on_back_clicked(self):
        """Handle back button click"""
        if self.browser:
            self.browser.back()
    
    def on_forward_clicked(self):
        """Handle forward button click"""
        if self.browser:
            self.browser.forward()
    
    def on_reload_clicked(self):
        """Handle reload button click"""
        if self.browser:
            self.browser.reload()
    
    def update_url_bar(self):
        """Update URL bar with current tab's URL"""
        if self.browser and self.url_bar:
            self.url_bar.setText(self.browser.url().toString())

    def on_tab_opened_signal(self, tab_name):
        """Handle tab opened signal from worker thread"""
        self.status.showMessage(f"Opening {tab_name}...")
    
    def on_chat_message_signal(self, message):
        """Handle chat message signal from worker thread"""
        self.chat_history.append(message)
    
    def on_status_message_signal(self, message):
        """Handle status message signal from worker thread"""
        self.status.showMessage(message)

    def navigate_home(self):
        if self.browser:
            import os
            home_path = os.path.abspath('home.html').replace('\\', '/')
            self.browser.setUrl(QUrl(f'file:///{home_path}'))

    def navigate_to_url(self):
        if self.browser:
            url = self.url_bar.text()
            # Smart URL parsing
            url = self.normalize_url(url)
            self.browser.setUrl(QUrl(url))

    def normalize_url(self, url):
        """Normalize URL for proper navigation"""
        # Check website shortcuts first
        url_lower = url.lower().strip()
        if url_lower in TaskExecutor.WEBSITE_SHORTCUTS:
            return TaskExecutor.WEBSITE_SHORTCUTS[url_lower]
        
        # If it has a dot, assume it's a domain
        if '.' in url:
            if not url.startswith('http'):
                url = 'https://' + url
        else:
            # No dot - could be a shortcut or add .com
            if url_lower not in TaskExecutor.WEBSITE_SHORTCUTS:
                url = 'https://' + url + '.com'
            else:
                url = TaskExecutor.WEBSITE_SHORTCUTS[url_lower]
        
        return url

    def update_status_bar(self, url):
        self.status.showMessage(url)

    def scrape_page(self):
        if self.browser:
            self.status.showMessage("Scraping page...")
            self.browser.page().toHtml(self.save_html)

    def save_html(self, html):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Page HTML", "scraped_page.html", "HTML Files (*.html);;All Files (*)", options=options)
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                self.status.showMessage(f"Successfully saved to {file_path}")
                
                # Extract and display product data
                self.extract_product_data(file_path)
                
            except Exception as e:
                self.status.showMessage(f"Error saving file: {str(e)}")
        else:
            self.status.showMessage("Scrape cancelled")

    def extract_product_data(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find Title
            title_element = soup.find(id="productTitle")
            title = title_element.text.strip() if title_element else "Title not found"
            
            # Find Price
            price_whole = soup.find(class_="a-price-whole")
            price_fraction = soup.find(class_="a-price-fraction")
            price_symbol = soup.find(class_="a-price-symbol")
            
            if price_whole and price_fraction and price_symbol:
                price = f"{price_symbol.text}{price_whole.text}{price_fraction.text}"
            else:
                price = "Price not found"
                
            # Display Result
            QMessageBox.information(self, "Extracted Product Data", f"Title: {title}\nPrice: {price}")
            
        except Exception as e:
            QMessageBox.warning(self, "Extraction Error", f"Failed to extract data: {str(e)}")

    def send_chat_message(self):
        msg = self.chat_input.text()
        if msg:
            self.chat_history.append(f"<b style='color:#4a7c9e'>You:</b> {msg}")
            self.chat_input.clear()
            
            # Parse task from message
            task = TaskExecutor.parse_task(msg)
            
            # Execute task if it's actionable
            if task["type"] in ["search", "navigate", "compare", "parallel"]:
                self.execute_browser_task(task, msg)
            else:
                # Use page context for query
                if self.browser:
                    self.browser.page().toHtml(lambda html: self.process_chat_with_context(html, msg))
    
    def execute_browser_task(self, task, original_msg):
        """Execute browser automation tasks"""
        try:
            if task["type"] == "parallel":
                self.execute_parallel_tasks(task, original_msg)
            elif task["type"] == "search":
                self.perform_search(task, original_msg)
            elif task["type"] == "navigate":
                self.perform_navigation(task, original_msg)
            elif task["type"] == "compare":
                self.perform_comparison(task, original_msg)
        except Exception as e:
            self.chat_history.append(f"<b style='color:#cc0000'>Error:</b> {str(e)}<br>")
    
    def execute_parallel_tasks(self, task, original_msg):
        """Execute multiple tasks in parallel using separate tabs"""
        tasks_list = task.get("tasks", [])
        
        if not tasks_list:
            self.chat_history.append("<b style='color:#cc0000'>Error:</b> No tasks to execute<br>")
            return
        
        print(f"DEBUG: Starting parallel task execution with {len(tasks_list)} tasks")
        self.chat_history.append(f"<b style='color:#0066cc'>Assistant:</b> Setting up {len(tasks_list)} parallel tasks...<br>")
        self.status.showMessage(f"Creating {len(tasks_list)} tabs...")
        
        first_tab_id = None
        
        # Create tabs directly on main thread (without switching to each one)
        for i, sub_task in enumerate(tasks_list):
            try:
                task_type = sub_task.get("type")
                print(f"DEBUG: Processing task {i+1}/{len(tasks_list)}, type={task_type}")
                
                if task_type == "compound":
                    # Open site and search
                    site = sub_task.get("site", "")
                    search_query = sub_task.get("search_query", "")
                    platform = sub_task.get("platform", "")
                    search_template = sub_task.get("search_template", "")
                    
                    if not search_template:
                        # Try to find the search template
                        search_template = TaskExecutor.COMMON_SEARCHES.get(platform, "")
                    
                    # Build the search URL
                    search_url = search_template + search_query.replace(" ", "+")
                    print(f"DEBUG: Creating compound task tab - site={site}, query={search_query}, url={search_url}")
                    
                    # Create tab WITHOUT switching to it (set_as_current=False)
                    tab_id = self.create_new_tab(label=f"Tab {i + 1} - {site.title()}", set_as_current=False)
                    print(f"DEBUG: Tab {i+1} created with ID={tab_id}")
                    if first_tab_id is None:
                        first_tab_id = tab_id
                    self.tabs[tab_id].browser_view.setUrl(QUrl(search_url))
                    self.chat_history.append(f"<b style='color:#4a7c9e'>➜ Tab {i + 1}:</b> {site.upper()} - Searching: <b>{search_query}</b><br>")
                    
                elif sub_task["type"] == "navigate":
                    url = sub_task.get("url", "")
                    url = self.normalize_url(url)
                    print(f"DEBUG: Creating navigate task tab - url={url}")
                    tab_id = self.create_new_tab(label=f"Tab {i + 1}", set_as_current=False)
                    print(f"DEBUG: Tab {i+1} created with ID={tab_id}")
                    if first_tab_id is None:
                        first_tab_id = tab_id
                    self.tabs[tab_id].browser_view.setUrl(QUrl(url))
                    self.chat_history.append(f"<b style='color:#4a7c9e'>➜ Tab {i + 1}:</b> Loading {url}<br>")
                    
                elif sub_task["type"] == "search":
                    platform = sub_task.get("platform", "google")
                    query = sub_task.get("query", "").strip()
                    url_template = sub_task.get("url_template", TaskExecutor.COMMON_SEARCHES.get("google", ""))
                    search_url = url_template + query.replace(" ", "+")
                    print(f"DEBUG: Creating search task tab - platform={platform}, query={query}, url={search_url}")
                    tab_id = self.create_new_tab(label=f"Tab {i + 1}", set_as_current=False)
                    print(f"DEBUG: Tab {i+1} created with ID={tab_id}")
                    if first_tab_id is None:
                        first_tab_id = tab_id
                    self.tabs[tab_id].browser_view.setUrl(QUrl(search_url))
                    self.chat_history.append(f"<b style='color:#4a7c9e'>➜ Tab {i + 1}:</b> Searching {query}<br>")
                
                QApplication.processEvents()  # Process events to update UI
                
            except Exception as e:
                print(f"DEBUG: Error in task {i+1}: {str(e)}")
                self.chat_history.append(f"<b style='color:#cc0000'>✗ Tab {i + 1} Error:</b> {str(e)}<br>")
        
        # Switch to first tab so browser displays something
        print(f"DEBUG: Total tabs created. Switching to first tab ID={first_tab_id}")
        if first_tab_id is not None:
            self.switch_to_tab(first_tab_id)
            print(f"DEBUG: Switched to tab {first_tab_id}")
        
        self.chat_history.append(f"<b style='color:#4a7c9e'>✓ Status:</b> All {len(tasks_list)} tabs opened and loading in parallel<br>")
    
    def execute_task_in_new_tab(self, task, task_index):
        """Execute a single task in a new tab (runs in background thread)"""
        try:
            if task["type"] == "navigate":
                url = task.get("url", "")
                url = self.normalize_url(url)
                # Use proper closure to capture variables
                QTimer.singleShot(100, lambda u=url, i=task_index: self._set_tab_url(u, i))
            elif task["type"] == "search":
                platform = task.get("platform", "google")
                query = task.get("query", "").strip()
                url_template = task.get("url_template", TaskExecutor.COMMON_SEARCHES.get("google", ""))
                search_url = url_template + query.replace(" ", "+")
                QTimer.singleShot(100, lambda u=search_url, i=task_index: self._set_tab_url(u, i))
        except Exception as e:
            self.signals.chat_message.emit(f"<b style='color:#cc0000'>Error:</b> {str(e)}<br>")
    
    def _set_tab_url(self, url, task_index):
        """Helper to set tab URL from main thread"""
        try:
            # Create new tab
            tab_id = self.create_new_tab(label=f"Tab {task_index + 1}")
            if tab_id in self.tabs:
                self.tabs[tab_id].browser_view.setUrl(QUrl(url))
                self.signals.chat_message.emit(f"<b style='color:#4a7c9e'>✓</b> Tab {task_index + 1} loading: {url}<br>")
        except Exception as e:
            self.signals.chat_message.emit(f"<b style='color:#cc0000'>Error opening tab:</b> {str(e)}<br>")
    
    
    def on_page_load_started(self, tab_id=None):
        """Called when page starts loading"""
        if tab_id and tab_id in self.tabs:
            self.tabs[tab_id].is_loading = True
        self.status.showMessage("Loading page...")
    
    def on_page_load_finished(self, success, tab_id=None):
        """Called when page finishes loading"""
        if tab_id and tab_id in self.tabs:
            self.tabs[tab_id].is_loading = False
        
        # Only process if this is the active tab
        if not self.browser:
            return
            
        if success:
            current_url = self.browser.url().toString()
            self.status.showMessage(f"✓ Page loaded: {current_url}")
            
            if self.current_task:
                task_type = self.current_task.get("type", "")
                task_query = self.current_task.get("query", "")
                platform = self.current_task.get("platform", "")
                task_url = self.current_task.get("url", "")
                
                if task_type == "search":
                    self.chat_history.append(f"<b style='color:#4a7c9e'>✓ Status:</b> Search results loaded for '<b>{task_query}</b>' on <b>{platform}</b>.<br>")
                elif task_type == "navigate":
                    self.chat_history.append(f"<b style='color:#4a7c9e'>✓ Status:</b> Successfully opened <b>{task_url}</b><br>")
                elif task_type == "compare":
                    self.chat_history.append(f"<b style='color:#4a7c9e'>✓ Status:</b> First platform loaded. You can compare prices now.<br>")
                elif task_type == "parallel":
                    self.chat_history.append(f"<b style='color:#4a7c9e'>✓ Status:</b> Tab loaded successfully<br>")
                
                self.current_task = None
        else:
            current_url = self.browser.url().toString()
            error_msg = self.analyze_load_error(current_url)
            self.status.showMessage(f"✗ Page failed to load")
            self.chat_history.append(f"<b style='color:#cc0000'>✗ Error:</b> {error_msg}<br>")
            self.show_troubleshooting_options()
            self.current_task = None
    
    def analyze_load_error(self, url):
        """Analyze and provide helpful error message"""
        if not url:
            return "Invalid URL provided. Please check and try again."
        
        # Common network error patterns
        error_explanations = {
            "ERR_NAME_NOT_RESOLVED": "DNS resolution failed - cannot find the website. Check your internet connection or DNS settings.",
            "ERR_INTERNET_DISCONNECTED": "No internet connection. Check your network connectivity.",
            "ERR_CONNECTION_REFUSED": "Connection refused by the server. The website may be down.",
            "ERR_TIMED_OUT": "Connection timed out. The server took too long to respond.",
            "ERR_FILE_NOT_FOUND": "404 - Page not found. The URL may be incorrect.",
            "ERR_SSL_PROTOCOL_ERROR": "SSL/TLS certificate error. The website's security certificate may be invalid.",
        }
        
        # Check page content for error type
        for error_code, explanation in error_explanations.items():
            # Return default comprehensive message
            return "Unable to load the webpage. This could be due to: DNS resolution failure, firewall/proxy blocking, invalid URL, or server unavailability."
    
    def show_troubleshooting_options(self):
        """Show troubleshooting steps in chat"""
        troubleshooting = """
        <b style='color:#ff6b6b'>⚠ Network Issue Detected</b><br><br>
        <b>Quick Fixes:</b><br>
        1. Check your internet connection<br>
        2. Check if firewall is blocking the browser<br>
        3. Try using a direct IP or different URL<br>
        4. Check DNS settings (try 8.8.8.8)<br>
        5. Disable VPN/Proxy if active<br><br>
        <b style='color:#4a7c9e'>Try one of these:</b><br>
        • Type a different URL you know works<br>
        • Try searching instead (e.g., "search google for test")<br>
        • Check network settings and retry
        """
        self.chat_history.append(troubleshooting)
    
    def perform_search(self, task, original_msg):
        """Perform a search task"""
        platform = task.get("platform", "google")
        query = task.get("query", "").strip()
        
        if not query:
            query = original_msg.replace("search", "").replace("find", "").replace("look for", "").strip()
        
        search_url = task["url_template"] + query.replace(" ", "+")
        
        self.chat_history.append(f"<b style='color:#0066cc'>Assistant:</b> Searching for '{query}' on {platform}...<br>")
        self.status.showMessage(f"Initiating search on {platform}...")
        
        # Store task info for load completion handler
        self.current_task = {
            "type": "search",
            "query": query,
            "platform": platform,
            "url": search_url
        }
        
        try:
            # Try HTTPS first, then fallback
            if not search_url.startswith("https"):
                search_url = search_url.replace("http://", "https://")
            
            # Make sure we have a browser
            if not self.browser or self.current_tab_id is None:
                print(f"DEBUG perform_search: No browser available, creating new tab")
                self.create_new_tab(url=search_url, label=f"Search: {query}")
            else:
                # Navigate to search
                self.browser.setUrl(QUrl(search_url))
        except Exception as e:
            self.chat_history.append(f"<b style='color:#cc0000'>✗ Error:</b> Failed to navigate to {platform}: {str(e)}<br>")
            self.show_troubleshooting_options()
            self.current_task = None
    
    def perform_navigation(self, task, original_msg):
        """Navigate to a specified URL"""
        url = original_msg.replace("open", "").replace("visit", "").strip()
        
        # Clean up URL
        url = url.strip('"\' ')
        
        # Check if it's a known website shortcut
        url_lower = url.lower()
        if url_lower in TaskExecutor.WEBSITE_SHORTCUTS:
            url = TaskExecutor.WEBSITE_SHORTCUTS[url_lower]
        # Handle URLs without protocol
        elif not url.startswith("http://") and not url.startswith("https://"):
            # Remove common punctuation
            url = url.rstrip('.,!?;:')
            
            # Check if it contains a domain (has a dot)
            if "." in url:
                url = "https://" + url
            else:
                # Might be a single word like "youtube", try to add .com
                if url_lower in TaskExecutor.WEBSITE_SHORTCUTS:
                    url = TaskExecutor.WEBSITE_SHORTCUTS[url_lower]
                else:
                    url = "https://" + url + ".com"
        
        self.chat_history.append(f"<b style='color:#0066cc'>Assistant:</b> Opening {url}...<br>")
        self.status.showMessage(f"Loading: {url}")
        
        # Store task info for load completion handler
        self.current_task = {
            "type": "navigate",
            "url": url
        }
        
        try:
            # Make sure we have a browser - if not, use current or create new tab
            if not self.browser or self.current_tab_id is None:
                print(f"DEBUG perform_navigation: No browser available, creating new tab")
                self.create_new_tab(url=url, label="Navigation")
            else:
                # Navigate to URL
                self.browser.setUrl(QUrl(url))
        except Exception as e:
            self.chat_history.append(f"<b style='color:#cc0000'>✗ Error:</b> Failed to navigate to {url}: {str(e)}<br>")
            self.show_troubleshooting_options()
            self.current_task = None
    
    def perform_comparison(self, task, original_msg):
        """Perform price comparison across platforms"""
        query_match = original_msg.replace("compare", "").replace("price", "").strip()
        platforms = task.get("platforms", ["amazon", "flipkart"])
        
        self.chat_history.append(f"<b style='color:#0066cc'>Assistant:</b> Comparing prices for '{query_match}' across {', '.join(platforms)}...<br>")
        self.chat_history.append(f"<b style='color:#4a7c9e'>Info:</b> Opening first platform ({platforms[0]})...<br>")
        
        # Open first platform
        if platforms:
            first_platform = platforms[0]
            search_url = TaskExecutor.COMMON_SEARCHES[first_platform] + query_match.replace(" ", "+")
            
            # Store task info
            self.current_task = {
                "type": "compare",
                "query": query_match,
                "platforms": platforms
            }
            
            try:
                # Make sure we have a browser
                if not self.browser or self.current_tab_id is None:
                    print(f"DEBUG perform_comparison: No browser available, creating new tab")
                    self.create_new_tab(url=search_url, label=f"Compare: {query_match}")
                else:
                    self.browser.setUrl(QUrl(search_url))
            except Exception as e:
                self.chat_history.append(f"<b style='color:#cc0000'>✗ Error:</b> Failed to start comparison: {str(e)}<br>")
                self.current_task = None
    
    def update_task_status(self, status_msg):
        """Update task status in chat"""
        self.chat_history.append(f"<b style='color:#4a7c9e'>Status:</b> {status_msg}<br>")
    
    def update_comparison_results(self, query, platforms):
        """Update comparison results"""
        results = f"Price comparison for '{query}' on platforms: {', '.join(platforms)}"
        self.chat_history.append(f"<b style='color:#4a7c9e'>Results:</b> {results}. Open each platform to compare prices.<br>")
            
    def process_chat_with_context(self, html, msg):
        """Process chat in background thread with AI response"""
        thread = threading.Thread(target=self._process_ai_chat, args=(html, msg))
        thread.daemon = True
        thread.start()
    
    def _process_ai_chat(self, html, msg):
        """Run AI chat processing in background thread"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            page_text = soup.get_text(separator=' ', strip=True)
            page_text_truncated = page_text[:10000]
            
            prompt = f"Webpage context:\n\n{page_text_truncated}\n\nQuestion: {msg}"
            full_prompt = f"You are a helpful browser assistant. Answer based on the webpage context. {prompt}"
            
            # Use new google.genai API
            response = AI_CLIENT.models.generate_content(
                model='gemini-2.5-flash',
                contents=full_prompt
            )
            ai_reply = response.text
            # Emit signal to update GUI from main thread
            self.signals.chat_message.emit(f"<b style='color:#0066cc'>Assistant:</b> {ai_reply}<br>")
        except Exception as e:
            self.signals.chat_message.emit(f"<b style='color:#cc0000'>Error:</b> {str(e)}<br>")
    
    def open_text_extractor(self):
        """Open YouTube and inject Text Extractor script"""
        print("DEBUG: Opening Text Extractor...")
        
        # Create new tab with YouTube
        tab_id = self.create_new_tab(
            url="https://www.youtube.com",
            label="🎥 Text Extractor",
            set_as_current=True
        )
        
        # Wait for page to load, then inject script
        if tab_id in self.tabs:
            browser = self.tabs[tab_id].browser_view
            browser.loadFinished.connect(lambda success, bid=tab_id: self.inject_text_extractor_script(browser) if success else None)
            self.chat_history.append(f"<b style='color:#0066cc'>Assistant:</b> 🎥 Opening YouTube for text extraction...<br><b style='color:#4a7c9e'>📌 How to use:</b><br>1. Play a YouTube video<br>2. Pause when you want to extract text<br>3. Click the <b>📋 Extract Text</b> button that appears<br>4. Text will be extracted and displayed!<br>")
    
    def inject_text_extractor_script(self, browser):
        """Inject Text Extractor JavaScript into the current page"""
        try:
            print("DEBUG: Preparing to inject Text Extractor script...")
            
            # Check if URL is YouTube
            current_url = browser.url().toString()
            if 'youtube.com' not in current_url.lower():
                print(f"DEBUG: Not a YouTube page: {current_url}")
                self.chat_history.append(f"<b style='color:#4a7c9e'>ℹ️ Info:</b> Text Extractor works best on YouTube. Current URL: {current_url}<br>")
                return
            
            # Read the JavaScript file
            import os
            script_path = os.path.join(os.path.dirname(__file__), 'text_extractor.js')
            
            if not os.path.exists(script_path):
                print(f"DEBUG: Script file not found at {script_path}")
                self.chat_history.append(f"<b style='color:#cc0000'>✗ Error:</b> Text Extractor script not found<br>")
                return
            
            with open(script_path, 'r', encoding='utf-8') as f:
                script_code = f.read()
            
            # Create a safer injection that wraps the script in error handling
            safe_script = f"""
            (function() {{
                console.log('[TextExtractor] Script injection started');
                try {{
                    {script_code}
                }} catch(error) {{
                    console.error('[TextExtractor] Injection failed:', error);
                }}
            }})();
            """
            
            # Inject script into page with error handling
            print("DEBUG: Injecting wrapped Text Extractor script...")
            browser.page().runJavaScript(safe_script, lambda result: self._on_script_injection_complete(result))
            
        except Exception as e:
            print(f"DEBUG: Failed to inject script: {str(e)}")
            self.chat_history.append(f"<b style='color:#cc0000'>✗ Error:</b> Failed to load Text Extractor: {str(e)}<br>")
    
    def _on_script_injection_complete(self, result):
        """Callback when script injection completes"""
        print(f"DEBUG: Script injection completed. Result: {result}")
        self.chat_history.append(f"<b style='color:#2c5282'>✅ Ready:</b> Text Extractor is active!<br><b style='color:#4a7c9e'>→ Play a video, pause it, and click the extraction button that appears.<br></b>")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setApplicationName('My Simple Browser')
    window = MainWindow()
    sys.exit(app.exec_())