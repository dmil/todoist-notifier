"""
Configuration management for the TickTick Notifier application.
"""
import os
from typing import Any
from dotenv import load_dotenv


class Config:
    """Application configuration manager using environment variables."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load environment variables from .env file
        load_dotenv()

        # Build configuration from environment variables with sensible defaults
        self._config = {
            'ticktick': {
                'api_token': os.getenv('TICKTICK_API_KEY', '')
            },
            'display': {
                'width': int(os.getenv('DISPLAY_WIDTH', 800)),
                'height': int(os.getenv('DISPLAY_HEIGHT', 480)),
                'fullscreen': os.getenv('DISPLAY_FULLSCREEN', 'false').lower() == 'true',
                'font_size': int(os.getenv('DISPLAY_FONT_SIZE', 24)),
                'theme': os.getenv('DISPLAY_THEME', 'dark').lower(),
                'refresh_interval': int(os.getenv('REFRESH_INTERVAL', 300))  # seconds
            },
            'webhook': {
                'enabled': os.getenv('WEBHOOK_ENABLED', 'false').lower() == 'true',
                'port': int(os.getenv('WEBHOOK_PORT', 5000)),
                'host': os.getenv('WEBHOOK_HOST', '0.0.0.0')
            },
            'focus_tag': os.getenv('FOCUS_TAG', '@focus')
        }


    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key (supports dot notation, e.g., 'display.width')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def validate(self) -> bool:
        """
        Validate that required configuration is present.

        Returns:
            True if configuration is valid
        """
        # Check for required API token
        api_token = self.get('ticktick.api_token')
        if not api_token:
            print("ERROR: TickTick API token not configured!")
            print("Set TICKTICK_API_KEY in your .env file")
            return False

        return True

    def __repr__(self) -> str:
        """String representation of config."""
        # Mask the API token for security
        import json
        safe_config = {
            'display': self._config['display'],
            'webhook': self._config['webhook'],
            'focus_tag': self._config['focus_tag'],
            'ticktick': {
                'api_token': '***' if self._config['ticktick']['api_token'] else 'NOT SET'
            }
        }
        return json.dumps(safe_config, indent=2)
