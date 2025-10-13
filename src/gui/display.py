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

        # Configure background - bright yellow/amber for attention
        self.root.configure(bg='#FFD700')

        # Create main container with vertical centering
        self.main_frame = tk.Frame(self.root, bg='#FFD700')
        self.main_frame.pack(expand=True, fill='both')

        # Spacer to push content to center
        tk.Frame(self.main_frame, bg='#FFD700').pack(expand=True, fill='both')

        # Task content label (main text) - large and centered with high contrast
        # Try multiple fonts for better emoji + text support
        # Tkinter will use the first available font
        self.task_label = tk.Label(
            self.main_frame,
            text="Loading tasks...",
            font=('Noto Sans', font_size * 2, 'bold'),
            bg='#FFD700',
            fg='#000000',
            wraplength=width - 100,
            justify='center'
        )
        self.task_label.pack(padx=50, pady=30)

        # Spacer to push metadata to bottom
        tk.Frame(self.main_frame, bg='#FFD700').pack(expand=True, fill='both')

        # Task details frame at bottom
        self.details_frame = tk.Frame(self.main_frame, bg='#FFD700')
        self.details_frame.pack(side='bottom', fill='x', padx=40, pady=30)

        # Metadata container (due time and priority side by side)
        self.metadata_frame = tk.Frame(self.details_frame, bg='#FFD700')
        self.metadata_frame.pack()

        # Due time label
        self.time_label = tk.Label(
            self.metadata_frame,
            text="",
            font=('Helvetica', font_size - 10),
            bg='#FFD700',
            fg='#CC6600',
            justify='center'
        )
        self.time_label.pack(side='left', padx=10)

        # Priority label
        self.priority_label = tk.Label(
            self.metadata_frame,
            text="",
            font=('Helvetica', font_size - 10),
            bg='#FFD700',
            fg='#CC0000',
            justify='center'
        )
        self.priority_label.pack(side='left', padx=10)

        # Focus indicator (hidden by default)
        self.focus_label = tk.Label(
            self.metadata_frame,
            text="",
            font=('Helvetica', font_size - 10, 'italic'),
            bg='#FFD700',
            fg='#00AA00',
            justify='center'
        )
        self.focus_label.pack(side='left', padx=10)

        # Last updated timestamp
        self.update_label = tk.Label(
            self.details_frame,
            text="",
            font=('Helvetica', font_size - 12),
            bg='#FFD700',
            fg='#666666',
            justify='center'
        )
        self.update_label.pack(pady=(10, 0))

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

        # Get background and text colors based on priority
        bg_color, text_color, meta_color = self._get_background_colors(task_data['priority_level'])

        # Update all background colors
        self.root.configure(bg=bg_color)
        self.main_frame.configure(bg=bg_color)
        self.details_frame.configure(bg=bg_color)
        self.metadata_frame.configure(bg=bg_color)

        # Update all widgets with new colors
        self.task_label.config(
            text=task_data['content'],
            bg=bg_color,
            fg=text_color
        )

        # Update spacers
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, tk.Frame) and widget != self.details_frame:
                widget.configure(bg=bg_color)

        # Update time (simple text, no emoji)
        time_text = task_data['due_time']
        self.time_label.config(text=time_text, bg=bg_color, fg=meta_color)

        # Update priority with color coding (simple text, no emoji)
        priority_text = task_data['priority']
        self.priority_label.config(text=priority_text, bg=bg_color, fg=meta_color)

        # Show focus indicator if applicable
        if task_data.get('has_focus', False):
            self.focus_label.config(text="Focus Task", bg=bg_color, fg=meta_color)
        else:
            self.focus_label.config(text="", bg=bg_color)

        # Update timestamp
        now = datetime.now().strftime("%I:%M:%S %p")
        self.update_label.config(text=f"Last updated: {now}", bg=bg_color, fg=meta_color)

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

    def _get_background_colors(self, priority: int) -> tuple:
        """
        Get background, text, and metadata colors based on priority level.

        Args:
            priority: Priority level (1-4)

        Returns:
            Tuple of (background_color, text_color, metadata_color)
        """
        color_schemes = {
            4: ('#FF4444', '#FFFFFF', '#FFE6E6'),  # Bright Red bg - Urgent!
            3: ('#FFA500', '#000000', '#664200'),  # Orange bg - High
            2: ('#4DA6FF', '#FFFFFF', '#E6F2FF'),  # Blue bg - Medium
            1: ('#CCCCCC', '#000000', '#666666')   # Gray bg - Low
        }
        return color_schemes.get(priority, ('#FFD700', '#000000', '#666666'))

    def _get_priority_color(self, priority: int) -> str:
        """
        Get color for priority level (kept for compatibility).

        Args:
            priority: Priority level (1-4)

        Returns:
            Hex color code
        """
        colors = {
            4: '#CC0000',  # Dark Red - Urgent
            3: '#CC6600',  # Dark Orange - High
            2: '#0066CC',  # Dark Blue - Medium
            1: '#666666'   # Gray - Low
        }
        return colors.get(priority, '#000000')

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
