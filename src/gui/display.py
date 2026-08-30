"""
Tkinter-based GUI for displaying the most important task on a small screen.
"""
import tkinter as tk
from tkinter import font as tkfont
from typing import Optional, Callable
from datetime import datetime

# Preferred display faces, in descending order. The first one actually
# installed wins; Raspberry Pi OS ships DejaVu Sans, and Noto Sans carries
# the widest emoji coverage for task titles.
FONT_PREFERENCES = ('Noto Sans', 'DejaVu Sans', 'Liberation Sans', 'Helvetica')

# Colour schemes keyed by priority (4 = most urgent). Each entry is a calm
# background with a single saturated accent, rather than a fully flooded
# screen, so the display stays readable for hours without glaring.
THEMES = {
    'dark': {
        'default': {'bg': '#414750', 'accent': '#C9D2DD', 'text': '#F2F4F7', 'meta': '#BAC1CA'},
        4: {'bg': '#8A3A30', 'accent': '#FFB3A3', 'text': '#FFF1ED', 'meta': '#E8C0B6'},
        3: {'bg': '#8A6024', 'accent': '#FFD494', 'text': '#FFF7EC', 'meta': '#EBD3AC'},
        2: {'bg': '#2C5F94', 'accent': '#A8D0F5', 'text': '#F0F7FF', 'meta': '#BDD5EC'},
        1: {'bg': '#4A515C', 'accent': '#C9D2DD', 'text': '#F2F4F7', 'meta': '#BAC1CA'},
    },
    'light': {
        'default': {'bg': '#E2E5E9', 'accent': '#5A6472', 'text': '#232830', 'meta': '#666E7A'},
        4: {'bg': '#F6D9D4', 'accent': '#B23A2E', 'text': '#3A1D18', 'meta': '#8A5348'},
        3: {'bg': '#F8E6C8', 'accent': '#A86C1A', 'text': '#3A2E18', 'meta': '#8A6A33'},
        2: {'bg': '#D6E4F3', 'accent': '#2F5F9E', 'text': '#182838', 'meta': '#4E6B8A'},
        1: {'bg': '#E2E5E9', 'accent': '#5A6472', 'text': '#232830', 'meta': '#666E7A'},
    },
}

# Priority names shown in the metadata line
PRIORITY_NAMES = {4: 'Urgent', 3: 'High', 2: 'Medium', 1: 'Low'}


class TaskDisplay:
    """GUI display for showing the most important task."""

    def __init__(self, width: int = 800, height: int = 480, fullscreen: bool = False,
                 font_size: int = 24, theme: str = 'dark'):
        """
        Initialize the task display.

        Args:
            width: Window width in pixels
            height: Window height in pixels
            fullscreen: Whether to run in fullscreen mode
            font_size: Base font size for task content
            theme: Colour scheme to use ('dark' or 'light')
        """
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.font_size = font_size
        self.theme = THEMES.get(theme, THEMES['dark'])

        # Create main window
        self.root = tk.Tk()
        self.root.title("TickTick Notifier")
        self.root.geometry(f"{width}x{height}")

        if fullscreen:
            self.root.attributes('-fullscreen', True)
            # Bind escape key to exit fullscreen
            self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))

        self.family = self._pick_font_family()
        scheme = self.theme['default']
        self.root.configure(bg=scheme['bg'])

        # Accent bar: carries the priority colour so the background does not
        # have to, keeping the screen calm while staying readable at a glance.
        self.accent_bar = tk.Frame(self.root, bg=scheme['accent'],
                                   height=max(14, int(font_size * 0.6)))
        self.accent_bar.pack(fill='x', side='top')
        self.accent_bar.pack_propagate(False)

        # Main container, vertically centred
        self.main_frame = tk.Frame(self.root, bg=scheme['bg'])
        self.main_frame.pack(expand=True, fill='both')

        # Spacer above the title
        self.top_spacer = tk.Frame(self.main_frame, bg=scheme['bg'])
        self.top_spacer.pack(expand=True, fill='both')

        # Task title: the one thing readable from across the room
        self.task_label = tk.Label(
            self.main_frame,
            text="Loading tasks...",
            font=(self.family, int(font_size * 1.9), 'bold'),
            bg=scheme['bg'],
            fg=scheme['text'],
            wraplength=width - int(width * 0.14),
            justify='center',
        )
        self.task_label.pack(padx=int(width * 0.07))

        # Metadata line: due time, priority and focus marker on one row
        self.meta_label = tk.Label(
            self.main_frame,
            text="",
            font=(self.family, int(font_size * 0.62)),
            bg=scheme['bg'],
            fg=scheme['meta'],
            justify='center',
        )
        self.meta_label.pack(pady=(int(font_size * 0.9), 0))

        # Spacer below the metadata
        self.bottom_spacer = tk.Frame(self.main_frame, bg=scheme['bg'])
        self.bottom_spacer.pack(expand=True, fill='both')

        # Footer timestamp, deliberately quiet
        self.update_label = tk.Label(
            self.root,
            text="",
            font=(self.family, max(8, int(font_size * 0.42))),
            bg=scheme['bg'],
            fg=scheme['meta'],
            justify='center',
        )
        self.update_label.pack(side='bottom', pady=(0, int(font_size * 0.7)))

        # Store current task
        self.current_task = None

    def _pick_font_family(self) -> str:
        """
        Choose the best available display font.

        Returns:
            Name of an installed font family
        """
        available = set(tkfont.families(self.root))
        for family in FONT_PREFERENCES:
            if family in available:
                return family

        return 'TkDefaultFont'

    def _apply_scheme(self, scheme: dict) -> None:
        """
        Repaint every widget in the given colour scheme.

        Args:
            scheme: Mapping of bg/accent/text/meta colours
        """
        self.root.configure(bg=scheme['bg'])
        self.accent_bar.configure(bg=scheme['accent'])

        for frame in (self.main_frame, self.top_spacer, self.bottom_spacer):
            frame.configure(bg=scheme['bg'])

        self.task_label.configure(bg=scheme['bg'], fg=scheme['text'])
        self.meta_label.configure(bg=scheme['bg'], fg=scheme['meta'])
        self.update_label.configure(bg=scheme['bg'], fg=scheme['meta'])

    def _stamp_update_time(self) -> None:
        """Refresh the footer timestamp."""
        now = datetime.now().strftime("%I:%M %p").lstrip('0').lower()
        self.update_label.config(text=f"Updated {now}")

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

        priority = task_data.get('priority_level')
        scheme = self.theme.get(priority, self.theme['default'])
        self._apply_scheme(scheme)

        self.task_label.config(text=task_data['content'])

        # Compose the metadata line, skipping anything we do not have
        parts = []
        if task_data.get('due_time') and task_data['due_time'] != 'No time set':
            parts.append(task_data['due_time'])

        if priority in PRIORITY_NAMES:
            parts.append(PRIORITY_NAMES[priority])

        if task_data.get('has_focus'):
            parts.append('Focus')

        self.meta_label.config(text='   ·   '.join(parts))
        self._stamp_update_time()

    def show_no_tasks(self) -> None:
        """Display message when no tasks are available."""
        self._apply_scheme(self.theme['default'])
        self.task_label.config(text="Nothing due today")
        self.meta_label.config(text="You're all clear")
        self._stamp_update_time()

    def show_error(self, error_message: str) -> None:
        """
        Display an error message.

        Args:
            error_message: Error message to display
        """
        self._apply_scheme(self.theme['default'])
        self.task_label.config(text="Can't reach TickTick")
        self.meta_label.config(text=error_message)
        self._stamp_update_time()

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
