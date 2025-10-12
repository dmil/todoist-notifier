#!/usr/bin/env python3
"""
Todoist Notifier - Main Application Entry Point

Displays the most important Todoist task on a Raspberry Pi screen.
"""
import sys
import signal
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config import Config
from api.todoist_client import TodoistClient
from logic.task_selector import TaskSelector
from gui.display import TaskDisplay
from webhook.server import WebhookServer


class TodoistNotifier:
    """Main application controller."""

    def __init__(self):
        """Initialize the Todoist Notifier application."""
        # Load configuration
        self.config = Config()

        if not self.config.validate():
            raise ValueError("Invalid configuration. Please check your settings.")

        # Initialize components
        self.todoist = TodoistClient(self.config.get('todoist.api_token'))
        self.selector = TaskSelector(self.config.get('focus_tag'))

        # Initialize GUI
        self.display = TaskDisplay(
            width=self.config.get('display.width'),
            height=self.config.get('display.height'),
            fullscreen=self.config.get('display.fullscreen'),
            font_size=self.config.get('display.font_size')
        )

        # Initialize webhook server if enabled
        self.webhook = None
        if self.config.get('webhook.enabled'):
            self.webhook = WebhookServer(
                host=self.config.get('webhook.host'),
                port=self.config.get('webhook.port')
            )
            self.webhook.set_update_callback(self.refresh_task)

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def refresh_task(self) -> None:
        """
        Refresh and update the displayed task.

        This fetches the latest tasks from Todoist, selects the most important one,
        and updates the display.
        """
        try:
            # Fetch today's tasks
            tasks = self.todoist.get_today_tasks(force_refresh=True)

            # Select the most important task
            selected_task = self.selector.select_most_important_task(tasks)

            # Format and update display
            if selected_task:
                task_data = self.selector.format_task_for_display(selected_task)
                self.display.update_task(task_data)
            else:
                self.display.update_task(None)

        except Exception as e:
            error_msg = f"Failed to fetch tasks: {str(e)}"
            print(error_msg)
            self.display.show_error(error_msg)

    def start(self) -> None:
        """Start the application."""
        print("Starting Todoist Notifier...")
        print(f"Configuration: {self.config}")

        # Start webhook server if enabled
        if self.webhook:
            self.webhook.start()
            print(f"Webhook server started on {self.config.get('webhook.host')}:{self.config.get('webhook.port')}")
            print(f"Webhook endpoint: http://{self.config.get('webhook.host')}:{self.config.get('webhook.port')}/webhook")

        # Initial task refresh
        self.refresh_task()

        # Set up automatic refresh
        refresh_interval = self.config.get('display.refresh_interval')
        self.display.set_refresh_callback(self.refresh_task)
        self.display.schedule_refresh(refresh_interval * 1000)  # Convert to ms

        print(f"Display refresh interval: {refresh_interval} seconds")
        print("\nApplication started successfully!")
        print("Press Ctrl+C to exit")

        # Start GUI main loop
        self.display.run()

    def stop(self) -> None:
        """Stop the application gracefully."""
        print("\nStopping Todoist Notifier...")

        if self.webhook:
            self.webhook.stop()

        self.display.destroy()
        print("Application stopped.")

    def _signal_handler(self, signum, frame):
        """Handle interrupt signals for graceful shutdown."""
        self.stop()
        sys.exit(0)


def main():
    """Main entry point."""
    try:
        # Create and start the application
        app = TodoistNotifier()
        app.start()

    except KeyboardInterrupt:
        print("\nReceived interrupt signal")
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("\nTo set up your configuration:")
        print("1. Copy .env.example to .env and add your Todoist API token")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
