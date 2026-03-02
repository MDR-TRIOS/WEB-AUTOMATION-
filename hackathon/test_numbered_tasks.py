#!/usr/bin/env python3
import re

# Copy TaskExecutor from simple_browser.py
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
    
    @staticmethod
    def parse_task(user_message):
        """Parse user message to extract task intent and parameters"""
        msg_lower = user_message.lower()
        
        # Check for parallel tasks (numbered, comma-separated, or with "and"/"also")
        if any(sep in msg_lower for sep in [",", "and", "also"]) or re.search(r'^\s*\d+\.', user_message):
            return TaskExecutor.parse_parallel_tasks(user_message)
        
        return {"type": "query", "message": user_message}
    
    @staticmethod
    def parse_parallel_tasks(user_message):
        """Parse multiple tasks from a single message, including compound tasks"""
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
        
        return {"type": "parallel", "tasks": tasks}

# Test message
test_msg = '1.open youtube and search for "shape of you" 2. open amazon and search for "shoes" 3.open flipkart and search for "python programming"'

print("Testing numbered task parsing...")
print(f"Input: {test_msg}\n")

# Parse task
task = TaskExecutor.parse_task(test_msg)

print(f"Task Type: {task['type']}")
print(f"Number of tasks: {len(task.get('tasks', []))}\n")

if task['type'] == 'parallel':
    for i, sub_task in enumerate(task['tasks']):
        print(f"Task {i+1}:")
        print(f"  Type: {sub_task.get('type')}")
        print(f"  Site: {sub_task.get('site')}")
        print(f"  Platform: {sub_task.get('platform')}")
        print(f"  Query: {sub_task.get('search_query')}")
        print(f"  URL: {sub_task.get('search_template')}{sub_task.get('search_query', '').replace(' ', '+')}")
        print()
