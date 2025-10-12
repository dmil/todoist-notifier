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

            # Due time: earlier is more important
            due_time = float('inf')
            if task.due and task.due.datetime:
                # Parse datetime string
                try:
                    dt = datetime.fromisoformat(task.due.datetime.replace('Z', '+00:00'))
                    due_time = dt.timestamp()
                except (ValueError, AttributeError):
                    pass

            return (priority, due_time)

        return min(tasks, key=task_sort_key)

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
        if task.due and task.due.datetime:
            try:
                dt = datetime.fromisoformat(task.due.datetime.replace('Z', '+00:00'))
                due_time_str = dt.strftime("%I:%M %p")
            except (ValueError, AttributeError):
                pass

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
