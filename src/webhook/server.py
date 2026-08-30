"""
Flask-based webhook server for receiving real-time update pushes.

Note: the TickTick Open API does not offer webhooks, so nothing calls this
endpoint under the default configuration. It is retained so a self-hosted
bridge (or a future TickTick push mechanism) can trigger an immediate refresh.
"""
from flask import Flask, request, jsonify
from typing import Callable, Optional
import threading
import logging


class WebhookServer:
    """Webhook server for receiving task update pushes."""

    def __init__(self, host: str = '0.0.0.0', port: int = 5000):
        """
        Initialize the webhook server.

        Args:
            host: Host address to bind to
            port: Port number to listen on
        """
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.update_callback: Optional[Callable] = None
        self.server_thread: Optional[threading.Thread] = None

        # Disable Flask's default logging in production
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        # Set up routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Set up Flask routes for webhook endpoints."""

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({'status': 'ok'}), 200

        @self.app.route('/webhook', methods=['POST'])
        def webhook():
            """
            Main webhook endpoint for task events.

            An external bridge can POST here when tasks are updated.
            """
            try:
                data = request.get_json()

                if not data:
                    return jsonify({'error': 'No data provided'}), 400

                # Extract event type and data
                event_type = data.get('event_name', '')
                event_data = data.get('event_data', {})

                print(f"Received webhook event: {event_type}")

                # Trigger update callback if registered
                if self.update_callback and self._should_trigger_update(event_type):
                    print("Triggering task refresh...")
                    self.update_callback()

                return jsonify({'status': 'success'}), 200

            except Exception as e:
                print(f"Error processing webhook: {e}")
                return jsonify({'error': str(e)}), 500

    def _should_trigger_update(self, event_type: str) -> bool:
        """
        Determine if an event should trigger a display update.

        Args:
            event_type: The event type

        Returns:
            True if update should be triggered
        """
        # Trigger on task-related events
        update_events = [
            'item:added',
            'item:updated',
            'item:deleted',
            'item:completed',
            'item:uncompleted'
        ]
        return event_type in update_events

    def set_update_callback(self, callback: Callable) -> None:
        """
        Register a callback to be called when tasks are updated.

        Args:
            callback: Function to call on task updates
        """
        self.update_callback = callback

    def start(self) -> None:
        """Start the webhook server in a background thread."""
        if self.server_thread and self.server_thread.is_alive():
            print("Webhook server is already running")
            return

        print(f"Starting webhook server on {self.host}:{self.port}")

        # Run Flask in a separate thread
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True
        )
        self.server_thread.start()

    def _run_server(self) -> None:
        """Run the Flask server."""
        self.app.run(
            host=self.host,
            port=self.port,
            debug=False,
            use_reloader=False
        )

    def stop(self) -> None:
        """Stop the webhook server."""
        # Flask doesn't have a built-in stop method, but the daemon thread
        # will stop when the main application exits
        print("Webhook server stopping...")
