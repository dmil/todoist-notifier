"""
Todoist API Client wrapper for fetching tasks and managing authentication.
"""
from typing import List, Optional
from datetime import datetime, date
from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task


class TodoistClient:
    """Wrapper for Todoist API operations."""

    def __init__(self, api_token: str):
        """
        Initialize the Todoist API client.

        Args:
            api_token: Todoist API authentication token
        """
        self.api = TodoistAPI(api_token)
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
        """Fetch fresh task data from Todoist API."""
        try:
            # Get all active tasks (returns a paginator in newer API versions)
            all_tasks_paginator = self.api.get_tasks()

            # Convert to list if it's a paginator
            all_tasks = list(all_tasks_paginator)

            # Filter for today's tasks
            today = date.today().isoformat()
            today_tasks = []

            for task in all_tasks:
                # Check if task has a due date
                if not hasattr(task, 'due') or task.due is None:
                    continue

                # due might be a string (date only) or have a datetime
                if hasattr(task.due, 'date'):
                    task_date = task.due.date
                else:
                    # If it's just a string
                    task_date = str(task.due)

                # Compare dates
                if task_date == today:
                    today_tasks.append(task)

            self._tasks_cache = today_tasks
            self._last_fetch = datetime.now()

        except Exception as e:
            print(f"Error fetching tasks from Todoist: {e}")
            raise

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

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """
        Get a specific task by ID.

        Args:
            task_id: The Todoist task ID

        Returns:
            Task object or None if not found
        """
        try:
            return self.api.get_task(task_id)
        except Exception as e:
            print(f"Error fetching task {task_id}: {e}")
            return None

    def mark_task_complete(self, task_id: str) -> bool:
        """
        Mark a task as complete.

        Args:
            task_id: The Todoist task ID

        Returns:
            True if successful, False otherwise
        """
        try:
            self.api.close_task(task_id)
            # Remove from cache if present
            self._tasks_cache = [t for t in self._tasks_cache if t.id != task_id]
            return True
        except Exception as e:
            print(f"Error completing task {task_id}: {e}")
            return False
