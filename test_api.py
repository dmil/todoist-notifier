#!/usr/bin/env python3
"""
Test script to verify TickTick API connection and task selection logic.
"""
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config import Config
from api.ticktick_client import TickTickClient
from logic.task_selector import TaskSelector

# Internal priority scale: 4 is P1 (urgent), 1 is P4 (low)
PRIORITY_LABELS = {4: "P1 (Urgent)", 3: "P2 (High)", 2: "P3 (Medium)", 1: "P4 (Low)"}


def main():
    """Test the TickTick API and task selection."""
    print("="*60)
    print("TickTick Notifier - API Test")
    print("="*60)

    # Load configuration
    print("\nLoading configuration...")
    config = Config()

    if not config.validate():
        print("ERROR: Configuration validation failed!")
        return 1

    print(f"Configuration loaded:\n{config}")

    # Initialize TickTick client
    print("\n" + "="*60)
    print("Testing TickTick API connection...")
    print("="*60)

    try:
        ticktick = TickTickClient(config.get('ticktick.api_token'))

        # Fetch today's tasks
        print("\nFetching today's tasks...")
        tasks = ticktick.get_today_tasks(force_refresh=True)

        print(f"Found {len(tasks)} task(s) due today:")
        print()

        if not tasks:
            print("  No tasks due today! Add some tasks in TickTick with today's date.")
            print("  You can also add the '@focus' label to a task to test the focus feature.")
            return 0

        # Display all tasks
        for i, task in enumerate(tasks, 1):
            print(f"{i}. {task.content}")
            print(f"   Priority: {PRIORITY_LABELS.get(task.priority, 'No priority')}")
            print(f"   Labels: {', '.join(task.labels) if task.labels else 'None'}")
            if task.due:
                print(f"   Due: {task.due.datetime or task.due.date}")
            print()

        # Test task selection logic
        print("="*60)
        print("Testing Task Selection Logic...")
        print("="*60)

        selector = TaskSelector(config.get('focus_tag'))
        selected_task = selector.select_most_important_task(tasks)

        if selected_task:
            print("\nMost important task selected:")
            print(f"  ✓ {selected_task.content}")

            # Format for display
            formatted = selector.format_task_for_display(selected_task)
            print("\nFormatted for display:")
            print(f"  Content: {formatted['content']}")
            print(f"  Due Time: {formatted['due_time']}")
            print(f"  Priority: {formatted['priority']}")
            if formatted['has_focus']:
                print(f"  ⭐ This is a FOCUS task!")

        print("\n" + "="*60)
        print("✓ All tests passed successfully!")
        print("="*60)
        print("\nTo run the full app on Raspberry Pi:")
        print("  1. Copy this directory to your Raspberry Pi")
        print("  2. Set up .env with your API token")
        print("  3. Run: python3 main.py")

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
