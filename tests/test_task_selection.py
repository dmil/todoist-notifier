#!/usr/bin/env python3
"""
Offline tests for TickTick task parsing and task selection.

Runs without a network connection or an API token: the client's parsing
helpers are exercised against captured API payloads.

Usage: python3 tests/test_task_selection.py
"""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from api.ticktick_client import TickTickClient, Task, Due
from logic.task_selector import TaskSelector

TODAY = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()

_results = []


def check(name, got, want):
    """Record a single assertion and print its outcome."""
    ok = got == want
    _results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        print(f"        got:  {got!r}")
        print(f"        want: {want!r}")


def raw_task(**overrides):
    """Build a raw TickTick payload shaped like a real API response."""
    payload = {
        'id': '1',
        'projectId': 'p1',
        'title': 'a task',
        'content': '',
        'priority': 0,
        'status': 0,
        'dueDate': None,
        'isAllDay': False,
        'tags': None,
        'timeZone': 'America/New_York',
    }
    payload.update(overrides)
    return payload


client = TickTickClient.__new__(TickTickClient)
selector = TaskSelector('@focus')

# --- parsing -------------------------------------------------------------

# TickTick names the task in 'title' and stores notes in 'content'
parsed = client._parse_task(raw_task(title='write tests', content='some notes'))
check('title becomes the displayed content', parsed.content, 'write tests')
check('content becomes the description', parsed.description, 'some notes')

# TickTick priorities 0/1/3/5 map onto the internal 1-4 scale
check('priority 5 -> 4 (urgent)', client._parse_task(raw_task(priority=5)).priority, 4)
check('priority 3 -> 3 (high)', client._parse_task(raw_task(priority=3)).priority, 3)
check('priority 1 -> 2 (medium)', client._parse_task(raw_task(priority=1)).priority, 2)
check('priority 0 -> 1 (low)', client._parse_task(raw_task(priority=0)).priority, 1)
check('unknown priority falls back to low',
      client._parse_task(raw_task(priority=99)).priority, 1)

# An all-day task on the 29th arrives as 04:00Z for a New York user
allday = client._parse_task(raw_task(
    dueDate='2026-08-29T04:00:00.000+0000', isAllDay=True))
check('all-day task keeps its local date', allday.due.date, '2026-08-29')
check('all-day task exposes no time', allday.due.datetime, None)

# A 9pm New York task is stored as the next UTC day; the local date must win
late = client._parse_task(raw_task(
    dueDate='2026-08-30T01:00:00.000+0000', isAllDay=False))
check('late task keeps the local date, not the UTC one', late.due.date, '2026-08-29')
check('late task keeps its local time', late.due.datetime.strftime('%I:%M %p'), '09:00 PM')

check('missing due date -> None', client._parse_task(raw_task()).due, None)
check('completed task is dropped', client._parse_task(raw_task(status=2)), None)
check('null tags become an empty list', client._parse_task(raw_task()).labels, [])
check('tags become labels', client._parse_task(raw_task(tags=['focus'])).labels, ['focus'])

# --- selection -----------------------------------------------------------

tasks = [
    Task('1', 'low', priority=1, due=Due(TODAY)),
    Task('2', 'urgent', priority=4, due=Due(TODAY)),
    Task('3', 'medium', priority=2, due=Due(TODAY)),
]
check('picks highest priority', selector.select_most_important_task(tasks).content, 'urgent')

tasks = [
    Task('1', 'urgent', priority=4, due=Due(TODAY)),
    Task('2', 'focused', priority=1, labels=['focus'], due=Due(TODAY)),
]
check('focus label overrides priority',
      selector.select_most_important_task(tasks).content, 'focused')

check('empty list -> None', selector.select_most_important_task([]), None)

nine = client._parse_task(raw_task(id='9am', title='9am', priority=3,
                                   dueDate='2026-08-29T13:00:00.000+0000'))
five = client._parse_task(raw_task(id='5pm', title='5pm', priority=3,
                                   dueDate='2026-08-29T21:00:00.000+0000'))
check('equal priority -> earliest due time',
      selector.select_most_important_task([five, nine]).content, '9am')

# Timed tasks outrank all-day tasks of the same priority
allday_task = client._parse_task(raw_task(id='allday', title='all day', priority=3,
                                          dueDate='2026-08-29T04:00:00.000+0000',
                                          isAllDay=True))
check('timed task beats an all-day task at equal priority',
      selector.select_most_important_task([allday_task, five]).content, '5pm')

# Ordering must not depend on hash randomisation
tie = [Task('6001', 'alpha', priority=3, due=Due(TODAY)),
       Task('6002', 'beta', priority=3, due=Due(TODAY)),
       Task('6003', 'gamma', priority=3, due=Due(TODAY))]
check('tie-break is deterministic',
      selector.select_most_important_task(tie).content, 'alpha')

# --- today filtering -----------------------------------------------------

client._tasks_cache, client._last_fetch = [], None
client._project_ids = lambda: ['p1']
client._project_tasks = lambda _pid: [
    raw_task(id='a', title='due today', dueDate=f'{TODAY}T13:00:00.000+0000'),
    raw_task(id='b', title='overdue', dueDate=f'{YESTERDAY}T13:00:00.000+0000'),
    raw_task(id='c', title='no due date'),
    raw_task(id='d', title='done', dueDate=f'{TODAY}T13:00:00.000+0000', status=2),
]
client._refresh_tasks()
check('only today\'s open tasks survive',
      sorted(t.content for t in client._tasks_cache), ['due today'])

# --- display formatting --------------------------------------------------

formatted = selector.format_task_for_display(
    client._parse_task(raw_task(title='ship it', priority=5, tags=['focus'],
                                dueDate='2026-08-29T13:00:00.000+0000')))
check('formats priority label', formatted['priority'], 'P1 (Urgent)')
check('flags focus task', formatted['has_focus'], True)
check('shows the real due time', formatted['due_time'], '9:00 AM')

formatted = selector.format_task_for_display(allday_task)
check('all-day task shows no clock time', formatted['due_time'], 'Today')

# Markdown link URLs are stripped, keeping only the link text
md = selector.format_task_for_display(
    client._parse_task(raw_task(title='see [docs](https://example.com/x)')))
check('markdown link keeps its text', md['content'], 'see docs')

md = selector.format_task_for_display(
    client._parse_task(raw_task(content='read [the guide](http://g.io) now')))
check('markdown link stripped from description', md['description'], 'read the guide now')

print(f"\n{sum(_results)}/{len(_results)} passed")
sys.exit(0 if all(_results) else 1)
