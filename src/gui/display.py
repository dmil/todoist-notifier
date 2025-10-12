"""
Tkinter-based GUI for displaying the most important task on a small screen.
"""
import tkinter as tk
from typing import Optional, Callable
from datetime import datetime


class TaskDisplay:
    """GUI display for showing the most important task."""

    def __init__(self, width: int = 800, height: int = 480, fullscreen: bool = False,
                 font_size: int = 24):
        """
        Initialize the task display.

        Args:
            width: Window width in pixels
            height: Window height in pixels
            fullscreen: Whether to run in fullscreen mode
            font_size: Base font size for task content
        """
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.font_size = font_size

        # Create main window
        self.root = tk.Tk()
        self.root.title("Todoist Notifier")
        self.root.geometry(f"{width}x{height}")

        if fullscreen:
            self.root.attributes('-fullscreen', True)
            # Bind escape key to exit fullscreen
            self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))

        # Configure background
        self.root.configure(bg='#282828')

        # Create main container
        self.main_frame = tk.Frame(self.root, bg='#282828')
        self.main_frame.pack(expand=True, fill='both', padx=40, pady=40)

        # Task content label (main text)
        self.task_label = tk.Label(
            self.main_frame,
            text="Loading tasks...",
            font=('Helvetica', font_size, 'bold'),
            bg='#282828',
            fg='#EBDBB2',
            wraplength=width - 80,
            justify='left'
        )
        self.task_label.pack(pady=(0, 20))

        # Task details frame
        self.details_frame = tk.Frame(self.main_frame, bg='#282828')
        self.details_frame.pack(fill='x', pady=(0, 20))

        # Due time label
        self.time_label = tk.Label(
            self.details_frame,
            text="",
            font=('Helvetica', font_size - 6),
            bg='#282828',
            fg='#FABD2F',
            justify='left'
        )
        self.time_label.pack(anchor='w')

        # Priority label
        self.priority_label = tk.Label(
            self.details_frame,
            text="",
            font=('Helvetica', font_size - 6),
            bg='#282828',
            fg='#FB4934',
            justify='left'
        )
        self.priority_label.pack(anchor='w', pady=(5, 0))

        # Focus indicator
        self.focus_label = tk.Label(
            self.details_frame,
            text="",
            font=('Helvetica', font_size - 6, 'italic'),
            bg='#282828',
            fg='#B8BB26',
            justify='left'
        )
        self.focus_label.pack(anchor='w', pady=(5, 0))

        # Last updated timestamp
        self.update_label = tk.Label(
            self.main_frame,
            text="",
            font=('Helvetica', font_size - 10),
            bg='#282828',
            fg='#928374',
            justify='center'
        )
        self.update_label.pack(side='bottom', pady=(20, 0))

        # Store current task
        self.current_task = None

    def update_task(self, task_data: Optional[dict]) -> None:
        """
        Update the display with new task data.

        Args:
            task_data: Dictionary containing formatted task information,
                      or None if no tasks available
        """
        if not task_data:
            self.show_no_tasks()
            return

        self.current_task = task_data

        # Update task content
        self.task_label.config(text=task_data['content'])

        # Update time
        time_text = f"⏰ {task_data['due_time']}"
        self.time_label.config(text=time_text)

        # Update priority with color coding
        priority_text = f"📌 {task_data['priority']}"
        priority_color = self._get_priority_color(task_data['priority_level'])
        self.priority_label.config(text=priority_text, fg=priority_color)

        # Show focus indicator if applicable
        if task_data.get('has_focus', False):
            self.focus_label.config(text="⭐ Focus Task")
        else:
            self.focus_label.config(text="")

        # Update timestamp
        now = datetime.now().strftime("%I:%M:%S %p")
        self.update_label.config(text=f"Last updated: {now}")

    def show_no_tasks(self) -> None:
        """Display message when no tasks are available."""
        self.task_label.config(text="No tasks due today!")
        self.time_label.config(text="")
        self.priority_label.config(text="")
        self.focus_label.config(text="")

        now = datetime.now().strftime("%I:%M:%S %p")
        self.update_label.config(text=f"Last updated: {now}")

    def show_error(self, error_message: str) -> None:
        """
        Display an error message.

        Args:
            error_message: Error message to display
        """
        self.task_label.config(
            text=f"Error: {error_message}",
            fg='#FB4934'
        )
        self.time_label.config(text="")
        self.priority_label.config(text="")
        self.focus_label.config(text="")

    def _get_priority_color(self, priority: int) -> str:
        """
        Get color for priority level.

        Args:
            priority: Priority level (1-4)

        Returns:
            Hex color code
        """
        colors = {
            4: '#FB4934',  # Red - Urgent
            3: '#FABD2F',  # Yellow - High
            2: '#83A598',  # Blue - Medium
            1: '#928374'   # Gray - Low
        }
        return colors.get(priority, '#EBDBB2')

    def set_refresh_callback(self, callback: Callable) -> None:
        """
        Set up automatic refresh at specified interval.

        Args:
            callback: Function to call for refresh
        """
        self.refresh_callback = callback

    def schedule_refresh(self, interval_ms: int) -> None:
        """
        Schedule periodic refresh.

        Args:
            interval_ms: Refresh interval in milliseconds
        """
        if hasattr(self, 'refresh_callback'):
            self.refresh_callback()
            self.root.after(interval_ms, lambda: self.schedule_refresh(interval_ms))

    def run(self) -> None:
        """Start the GUI main loop."""
        self.root.mainloop()

    def destroy(self) -> None:
        """Clean up and close the window."""
        self.root.destroy()
