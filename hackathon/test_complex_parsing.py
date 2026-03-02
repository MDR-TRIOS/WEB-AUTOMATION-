import sys
sys.path.insert(0, '.')
from simple_browser import TaskExecutor

# Test the complex multi-tasking parsing
test_cases = [
    'open youtube and search for a song "shape of you"',
    '1.open youtube and search for a song "shape of you" 2. open amazon and search for "shoes" 3.open wikipedia and search for "python programming"',
    'open youtube and search for shape of you, open amazon and search for shoes, open wikipedia and search for python programming'
]

for test_msg in test_cases:
    print(f"\n\nTest: {test_msg}")
    print("-" * 80)
    task = TaskExecutor.parse_task(test_msg)
    print(f"Task type: {task.get('type')}")
    
    if task.get('type') == 'parallel':
        tasks_list = task.get('tasks', [])
        print(f"Number of tasks: {len(tasks_list)}")
        for i, t in enumerate(tasks_list):
            print(f"\n  Task {i+1}:")
            print(f"    Type: {t.get('type')}")
            if t.get('type') == 'compound':
                print(f"    Site: {t.get('site')}")
                print(f"    Platform: {t.get('platform')}")
                print(f"    Search Query: {t.get('search_query')}")
                print(f"    Search URL will be: {t.get('search_template')} + {t.get('search_query').replace(' ', '+')}")
            elif t.get('type') == 'navigate':
                print(f"    URL: {t.get('url')}")
            elif t.get('type') == 'search':
                print(f"    Platform: {t.get('platform')}")
                print(f"    Query: {t.get('query')}")
