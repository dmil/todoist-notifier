"""
Task selection logic to determine the most important task to display.
"""
from typing import Optional, List
from todoist_api_python.models import Task
from datetime import datetime


class TaskSelector:
    """Logic for selecting the most important task to display."""

    def __init__(self, focus_tag: str = "@focus"):
        """
        Initialize the task selector.

        Args:
            focus_tag: Tag used to manually override task selection (default: @focus)
        """
        self.focus_tag = focus_tag

    def select_most_important_task(self, tasks: List[Task]) -> Optional[Task]:
        """
        Select the most important task from a list based on:
        1. @focus tag override
        2. Priority level
        3. Due time (earlier is more important)

        Args:
            tasks: List of tasks to choose from

        Returns:
            The most important task, or None if list is empty
        """
        if not tasks:
            return None

        # First check for @focus tag override
        focus_task = self._find_focus_task(tasks)
        if focus_task:
            return focus_task

        # Sort by priority (4 = highest, 1 = lowest in Todoist) and due time
        return self._select_by_priority_and_time(tasks)

    def _find_focus_task(self, tasks: List[Task]) -> Optional[Task]:
        """
        Find a task with the focus tag.

        Args:
            tasks: List of tasks to search

        Returns:
            Task with focus tag, or None if not found
        """
        for task in tasks:
            if task.labels and self.focus_tag.replace("@", "") in task.labels:
                return task
        return None

    def _select_by_priority_and_time(self, tasks: List[Task]) -> Task:
        """
        Select task based on priority and due time.

        Priority takes precedence, then earlier due time.

        Args:
            tasks: List of tasks to choose from

        Returns:
            The highest priority task with earliest time
        """
        def task_sort_key(task: Task) -> tuple:
            # Priority: 4 (highest) to 1 (lowest), negate to sort descending
            priority = -task.priority if task.priority else 0

            # Due time: earlier is more important. Tasks with no specific time
            # sort after timed tasks; task ID breaks any remaining tie so the
            # same task list always yields the same choice.
            due_time = self._due_timestamp(task)

            return (priority, due_time, str(task.id))

        return min(tasks, key=task_sort_key)

    def _due_datetime(self, task: Task) -> Optional[datetime]:
        """
        Get the specific due datetime for a task, if it has one.

        Args:
            task: Task to inspect

        Returns:
            The due datetime, or None for date-only tasks
        """
        due = getattr(task, 'due', None)
        if due is None:
            return None

        due_dt = getattr(due, 'datetime', None)
        if due_dt is None:
            return None

        if isinstance(due_dt, str):
            try:
                return datetime.fromisoformat(due_dt.replace('Z', '+00:00'))
            except ValueError:
                return None

        return due_dt

    def _due_timestamp(self, task: Task) -> float:
        """
        Get a sortable due time for a task.

        Args:
            task: Task to inspect

        Returns:
            POSIX timestamp of the due time, or infinity if no time is set
        """
        due_dt = self._due_datetime(task)
        if due_dt is None:
            return float('inf')

        return due_dt.timestamp()

    def format_task_for_display(self, task: Task) -> dict:
        """
        Format a task for display purposes.

        Args:
            task: Task to format

        Returns:
            Dictionary with formatted task information
        """
        # Format due time if available
        due_time_str = "No time set"
        due_dt = self._due_datetime(task)
        if due_dt:
            due_time_str = due_dt.strftime('%I:%M %p').lstrip('0')
        elif task.due and hasattr(task.due, 'date'):
            # Date-only task: no specific time to show
            due_time_str = "Today"

        # Priority indicator
        priority_text = {
            4: "P1 (Urgent)",
            3: "P2 (High)",
            2: "P3 (Medium)",
            1: "P4 (Low)"
        }.get(task.priority, "No priority")

        return {
            "id": task.id,
            "content": task.content,
            "due_time": due_time_str,
            "priority": priority_text,
            "priority_level": task.priority,
            "project_id": task.project_id,
            "labels": task.labels or [],
            "description": task.description or "",
            "has_focus": self.focus_tag.replace("@", "") in (task.labels or [])
        }
