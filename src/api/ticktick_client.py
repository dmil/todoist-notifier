"""
TickTick API client wrapper for fetching tasks and managing authentication.

Uses the TickTick Open API (https://api.ticktick.com/open/v1), which has no
endpoint for "all tasks" -- tasks are fetched per project and filtered locally.
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import requests

API_BASE = "https://api.ticktick.com/open/v1"

# The Inbox is not returned by the project listing but is readable under this id.
INBOX_PROJECT_ID = "inbox"

# TickTick priorities (0 none, 1 low, 3 medium, 5 high) mapped onto the
# internal 1-4 scale used by the selector and the display colour scheme,
# where 4 is the most urgent.
PRIORITY_MAP = {5: 4, 3: 3, 1: 2, 0: 1}

# Task status values; anything non-zero is completed or abandoned.
STATUS_ACTIVE = 0


@dataclass
class Due:
    """Due information for a task."""

    date: str
    datetime: Optional[datetime] = None


@dataclass
class Task:
    """A single actionable task, normalised across API shapes."""

    id: str
    content: str
    priority: int = 1
    labels: List[str] = field(default_factory=list)
    due: Optional[Due] = None
    description: str = ""
    project_id: str = ""


class TickTickClient:
    """Wrapper for TickTick API operations."""

    def __init__(self, api_token: str, timeout: int = 15):
        """
        Initialize the TickTick API client.

        Args:
            api_token: TickTick API authentication token
            timeout: Per-request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_token}',
            'Accept': 'application/json',
        })
        self._tasks_cache: List[Task] = []
        self._last_fetch: Optional[datetime] = None

    def get_today_tasks(self, force_refresh: bool = False) -> List[Task]:
        """
        Fetch all tasks due today.

        Args:
            force_refresh: Force a fresh API call instead of using cache

        Returns:
            List of tasks due today
        """
        if force_refresh or not self._tasks_cache or self._should_refresh():
            self._refresh_tasks()

        return self._tasks_cache

    def _refresh_tasks(self) -> None:
        """Fetch fresh task data from the TickTick API."""
        try:
            today = date.today().isoformat()
            today_tasks = []

            for project_id in self._project_ids():
                for raw in self._project_tasks(project_id):
                    task = self._parse_task(raw)

                    # Skip tasks with no due date, and anything not due today
                    if task is None or task.due is None:
                        continue

                    if task.due.date == today:
                        today_tasks.append(task)

            self._tasks_cache = today_tasks
            self._last_fetch = datetime.now()

        except Exception as e:
            print(f"Error fetching tasks from TickTick: {e}")
            raise

    def _project_ids(self) -> List[str]:
        """
        List every project id to scan, including the Inbox.

        Returns:
            List of project identifiers
        """
        projects = self._get('/project') or []
        ids = [p['id'] for p in projects if p.get('id')]

        # The Inbox is absent from the listing, so scan it explicitly
        return [INBOX_PROJECT_ID] + ids

    def _project_tasks(self, project_id: str) -> List[dict]:
        """
        Fetch the undone tasks belonging to one project.

        Args:
            project_id: The TickTick project id

        Returns:
            List of raw task dictionaries (empty if the project is unreadable)
        """
        try:
            data = self._get(f'/project/{project_id}/data') or {}
        except requests.HTTPError as e:
            # A single unreadable project should not blank the whole display
            print(f"Warning: could not read project {project_id}: {e}")
            return []

        return data.get('tasks') or []

    def _get(self, path: str):
        """
        Perform an authenticated GET against the Open API.

        Args:
            path: API path beginning with a slash

        Returns:
            Decoded JSON response
        """
        response = self.session.get(f'{API_BASE}{path}', timeout=self.timeout)

        if response.status_code == 401:
            raise RuntimeError(
                "TickTick rejected the API token (401). "
                "Check TICKTICK_API_KEY in your .env file."
            )

        response.raise_for_status()

        if not response.content:
            return None

        return response.json()

    def _parse_task(self, raw: dict) -> Optional[Task]:
        """
        Convert a raw TickTick task into the internal Task shape.

        Args:
            raw: Raw task dictionary from the API

        Returns:
            Parsed task, or None if the task is completed
        """
        if raw.get('status', STATUS_ACTIVE) != STATUS_ACTIVE:
            return None

        return Task(
            id=raw.get('id', ''),
            # TickTick names the task in 'title'; 'content' holds the notes
            content=raw.get('title', ''),
            priority=PRIORITY_MAP.get(raw.get('priority', 0), 1),
            labels=raw.get('tags') or [],
            due=self._parse_due(raw),
            description=raw.get('content') or '',
            project_id=raw.get('projectId', ''),
        )

    def _parse_due(self, raw: dict) -> Optional[Due]:
        """
        Build due information from a raw task.

        TickTick returns due dates as UTC instants alongside the timezone the
        task was created in, so an all-day task on the 29th arrives as
        2026-08-29T04:00:00+0000 for a New York user. Converting back into the
        task's own zone recovers the date the user actually sees.

        Args:
            raw: Raw task dictionary from the API

        Returns:
            Due information, or None if the task has no due date
        """
        raw_due = raw.get('dueDate')
        if not raw_due:
            return None

        try:
            due_dt = datetime.fromisoformat(raw_due)
        except ValueError:
            print(f"Warning: unparseable due date {raw_due!r}")
            return None

        local_dt = due_dt.astimezone(self._zone(raw.get('timeZone')))

        # All-day tasks carry a meaningless midnight time, so expose the date only
        if raw.get('isAllDay'):
            return Due(date=local_dt.date().isoformat())

        return Due(date=local_dt.date().isoformat(), datetime=local_dt)

    @staticmethod
    def _zone(timezone_name: Optional[str]):
        """
        Resolve a task's timezone, falling back to the system zone.

        Args:
            timezone_name: IANA timezone name from the API

        Returns:
            A tzinfo instance
        """
        if timezone_name:
            try:
                return ZoneInfo(timezone_name)
            except (ZoneInfoNotFoundError, ValueError):
                print(f"Warning: unknown timezone {timezone_name!r}, using local time")

        return datetime.now().astimezone().tzinfo

    def _should_refresh(self) -> bool:
        """
        Check if cache should be refreshed (older than 5 minutes).

        Returns:
            True if cache should be refreshed
        """
        if not self._last_fetch:
            return True

        elapsed = (datetime.now() - self._last_fetch).total_seconds()
        return elapsed > 300  # 5 minutes

    def get_task_by_id(self, project_id: str, task_id: str) -> Optional[Task]:
        """
        Get a specific task by id.

        Args:
            project_id: The project the task belongs to
            task_id: The TickTick task id

        Returns:
            Task object or None if not found
        """
        try:
            raw = self._get(f'/project/{project_id}/task/{task_id}')
            return self._parse_task(raw) if raw else None
        except Exception as e:
            print(f"Error fetching task {task_id}: {e}")
            return None

    def mark_task_complete(self, project_id: str, task_id: str) -> bool:
        """
        Mark a task as complete.

        Args:
            project_id: The project the task belongs to
            task_id: The TickTick task id

        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.post(
                f'{API_BASE}/project/{project_id}/task/{task_id}/complete',
                timeout=self.timeout,
            )
            response.raise_for_status()

            # Remove from cache if present
            self._tasks_cache = [t for t in self._tasks_cache if t.id != task_id]
            return True
        except Exception as e:
            print(f"Error completing task {task_id}: {e}")
            return False
