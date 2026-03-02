import sys
sys.path.insert(0, '.')
from simple_browser import TaskExecutor

msg = 'open youtube,amazon and wikipedia'
print(f'Input: {msg}')

task = TaskExecutor.parse_task(msg)
print(f'Task type: {task.get("type")}')

if task.get('type') == 'parallel':
    tasks_list = task.get('tasks', [])
    print(f'Number of parallel tasks: {len(tasks_list)}')
    for i, t in enumerate(tasks_list):
        print(f'  Task {i+1}: type={t.get("type")}, url={t.get("url")}')
else:
    print(f'ERROR: Expected parallel task, got: {task}')
