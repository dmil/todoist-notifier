# todoist-notifier

View your most important task for today at a glance.
An app for the Raspberry Pi connected to a small screen that shows only one todoist task.

## Features
- Shows the most important task for today
    - It determines the most important task using priority and due date
    - Override by adding `@focus` tag to a task and have it take precedence
- Automatically updates when tasks change using Todoist Webhooks
- Real-time display updates via webhook integration
- Configurable display settings for different screen sizes
- Automatic periodic refresh (default: 5 minutes)

## Stack

- Raspberry Pi
- Tkinter for GUI
- Python for backend
- Todoist API
- Flask for webhook server

## Installation

### Prerequisites
- Python 3.7 or higher
- Tkinter (usually comes with Python)
- Todoist account and API token

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd todoist-notifier
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your settings:
```bash
cp .env.example .env
# Edit .env and add your Todoist API token
```

To get your Todoist API token:
1. Go to https://todoist.com/app/settings/integrations/developer
2. Copy your API token
3. Add it to your .env file

## Usage

### Running the Application

**Option 1: Direct Python (Raspberry Pi / Linux)**
```bash
python3 main.py
```

**Option 2: Docker (recommended for testing on macOS/Windows)**
```bash
# Build and run with docker-compose
docker-compose up --build

# Or run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

Note: Docker is particularly useful for testing on macOS where Tkinter has compatibility issues. The container simulates the Linux environment of the Raspberry Pi.

**For macOS users**: To see the GUI in Docker, you'll need to set up X11 forwarding with XQuartz. See [DOCKER_SETUP.md](DOCKER_SETUP.md) for detailed instructions.

### Configuration Options

All configuration is done via environment variables in your `.env` file:

**Required:**
- `TODOIST_API_TOKEN` - Your Todoist API token

**Display Settings (optional):**
- `DISPLAY_WIDTH` - Screen width in pixels (default: 800)
- `DISPLAY_HEIGHT` - Screen height in pixels (default: 480)
- `DISPLAY_FULLSCREEN` - Run fullscreen: true/false (default: false)
- `DISPLAY_FONT_SIZE` - Base font size (default: 24)
- `REFRESH_INTERVAL` - Auto-refresh interval in seconds (default: 300)

**Webhook Settings (optional):**
- `WEBHOOK_ENABLED` - Enable webhook server: true/false (default: false)
- `WEBHOOK_HOST` - Webhook server host (default: 0.0.0.0)
- `WEBHOOK_PORT` - Webhook server port (default: 5000)

**Task Selection (optional):**
- `FOCUS_TAG` - Label to override task selection (default: @focus)

Note: Set `WEBHOOK_ENABLED=false` if you're on university/restricted networks where you can't open ports.

### Setting Up Webhooks

To receive real-time updates from Todoist:

1. Start the application (webhook server runs automatically)
2. Make your webhook endpoint publicly accessible:
   - For development: Use ngrok or similar tunnel service
   - For production: Set up port forwarding on your router

3. Configure the webhook in Todoist:
   - Go to Todoist App Settings > Integrations
   - Add your webhook URL: `http://your-ip:5000/webhook`

### Keyboard Shortcuts

- `Escape`: Exit fullscreen mode
- `Ctrl+C`: Quit application

## Project Structure

```
todoist-notifier/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── .env                    # Your configuration (create from .env.example)
└── src/
    ├── api/
    │   └── todoist_client.py    # Todoist API wrapper
    ├── gui/
    │   └── display.py           # Tkinter GUI display
    ├── logic/
    │   └── task_selector.py     # Task selection logic
    ├── webhook/
    │   └── server.py            # Flask webhook server
    └── config.py                # Configuration management
```

## Task Selection Logic

The app selects the most important task using this priority:

1. **@focus tag override**: Any task tagged with `@focus` (or your custom focus tag) will be displayed first
2. **Priority level**: Higher priority tasks (P1 > P2 > P3 > P4) are preferred
3. **Due time**: If priorities are equal, earlier due times take precedence

## Running on Raspberry Pi

### Auto-start on Boot

Create a systemd service to run the app on startup:

1. Create service file:
```bash
sudo nano /etc/systemd/system/todoist-notifier.service
```

2. Add the following content:
```ini
[Unit]
Description=Todoist Notifier Display
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/todoist-notifier
Environment="DISPLAY=:0"
ExecStart=/home/pi/todoist-notifier/venv/bin/python3 /home/pi/todoist-notifier/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:
```bash
sudo systemctl enable todoist-notifier
sudo systemctl start todoist-notifier
```

## Troubleshooting

**No tasks displayed:**
- Check that you have tasks due today in Todoist
- Verify your API token is correct
- Check console for error messages

**Webhook not receiving updates:**
- Ensure webhook server is running (check console output)
- Verify your webhook URL is publicly accessible
- Check Todoist webhook configuration

**Display issues on Raspberry Pi:**
- Adjust `width`, `height`, and `font_size` in config
- Try fullscreen mode for better fit
- Ensure X server is running (required for Tkinter)

## License

MIT