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

# The original priority colours, used at full strength for the accent bar.
PRIORITY_COLORS = {
    4: '#FF4444',  # Red - Urgent
    3: '#FFA500',  # Orange - High
    2: '#4DA6FF',  # Blue - Medium
    1: '#CCCCCC',  # Grey - Low
}
DEFAULT_COLOR = '#FFD700'  # Gold - used when no priority is known

WHITE = '#FFFFFF'
DARK_INK = '#1A1A1A'

# Smallest contrast ratio the metadata line is allowed to fall to
MIN_CONTRAST = 4.5

# Smallest contrast the accent bar needs against the background behind it
MIN_ACCENT_CONTRAST = 1.35

# Priority names shown in the metadata line
PRIORITY_NAMES = {4: 'Urgent', 3: 'High', 2: 'Medium', 1: 'Low'}


def _rgb(colour: str) -> list:
    """Split a hex colour into its RGB components."""
    return [int(colour[i:i + 2], 16) for i in (1, 3, 5)]


def _hex(channels) -> str:
    """Join RGB components back into a hex colour."""
    return '#%02X%02X%02X' % tuple(max(0, min(255, int(round(c)))) for c in channels)


def _blend(colour: str, target: str, amount: float) -> str:
    """
    Mix one colour towards another.

    Args:
        colour: Starting hex colour
        target: Hex colour to move towards
        amount: 0 keeps the original, 1 returns the target

    Returns:
        The blended hex colour
    """
    start, finish = _rgb(colour), _rgb(target)
    return _hex([start[i] + (finish[i] - start[i]) * amount for i in range(3)])


def _luminance(colour: str) -> float:
    """Relative luminance of a hex colour, per WCAG."""
    channels = [c / 255 for c in _rgb(colour)]
    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                for c in channels]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast(one: str, two: str) -> float:
    """Contrast ratio between two hex colours, from 1 to 21."""
    first, second = _luminance(one), _luminance(two)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def build_scheme(colour: str, opacity: float) -> dict:
    """
    Derive a full colour scheme from one priority colour.

    Tkinter cannot make a widget translucent, so a lower opacity is applied by
    mixing the colour towards white. The accent bar keeps the colour at full
    strength, and the ink is chosen for whichever gives better contrast against
    the softened background, so the display stays readable at any setting.

    Args:
        colour: The priority's hex colour at full strength
        opacity: How much of the colour to keep, from 0 to 1

    Returns:
        Mapping of bg/accent/text/meta colours
    """
    bg = _blend(colour, WHITE, 1 - opacity)

    # At full opacity the bar would match the background exactly, so deepen it
    # until it separates from the background it sits on.
    accent = colour
    for step in range(1, 11):
        if _contrast(bg, accent) >= MIN_ACCENT_CONTRAST:
            break
        accent = _blend(colour, DARK_INK, step * 0.08)

    ink = DARK_INK if _contrast(bg, DARK_INK) >= _contrast(bg, WHITE) else WHITE

    # Fade the metadata towards the background, stopping while it stays legible
    meta = ink
    for step in range(1, 21):
        candidate = _blend(ink, bg, step * 0.05)
        if _contrast(bg, candidate) < MIN_CONTRAST:
            break
        meta = candidate

    return {'bg': bg, 'accent': accent, 'text': ink, 'meta': meta}


class TaskDisplay:
    """GUI display for showing the most important task."""

    def __init__(self, width: int = 800, height: int = 480, fullscreen: bool = False,
                 font_size: int = 24, colour_opacity: float = 0.75):
        """
        Initialize the task display.

        Args:
            width: Window width in pixels
            height: Window height in pixels
            fullscreen: Whether to run in fullscreen mode
            font_size: Base font size for task content
            colour_opacity: How saturated the backgrounds are, from 0 to 1
        """
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.font_size = font_size
        # Clamp to a range that still leaves the priority distinguishable
        opacity = max(0.15, min(1.0, colour_opacity))
        self.theme = {p: build_scheme(c, opacity) for p, c in PRIORITY_COLORS.items()}
        self.theme['default'] = build_scheme(DEFAULT_COLOR, opacity)

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
