#!/usr/bin/env python3
"""Test the numbered format detection flow"""
import re

class TaskExecutor:
    COMMON_SEARCHES = {
        "amazon": "https://www.amazon.in/s?k=",
        "flipkart": "https://www.flipkart.com/search?q=",
        "youtube": "https://www.youtube.com/results?search_query=",
        "google": "https://www.google.com/search?q=",
    }
    
    @staticmethod
    def parse_task(user_message):
        """Parse user message to extract task intent and parameters"""
        msg_lower = user_message.lower()
        
        # Check for parallel tasks (numbered, comma-separated, or with "and"/"also")
        if any(sep in msg_lower for sep in [",", "and", "also"]) or re.search(r'^\s*\d+\.', user_message):
            return TaskExecutor.parse_parallel_tasks(user_message)
        
        return {"type": "unknown"}
    
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

# Test
msg = '1.open youtube and search for a song "shape of you" 2. open amazon and search for "shoes" 3.open flipkart and search for "python programming"'
print("Testing numbered format detection and parsing:")
print(f"Input: {msg[:60]}...\n")

result = TaskExecutor.parse_task(msg)
print(f"✓ parse_task() returned type: '{result.get('type')}'")
print(f"✓ Number of tasks: {len(result.get('tasks', []))}\n")

if result.get('type') == 'parallel':
    print("SUCCESS: Recognized as parallel task type\n")
    for i, task in enumerate(result.get('tasks', []), 1):
        print(f"Tab {i}: {task['platform'].upper()} → search '{task['search_query']}'")
else:
    print("ERROR: Not recognized as parallel task!")