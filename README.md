# todoist-notifier

View your most important task for today at a glance.
An app for the Raspberry Pi connected to a small screen that shows only one TickTick task.

## Features
- Shows the most important task for today
    - It determines the most important task using priority and due date
    - Override by adding `@focus` tag to a task and have it take precedence
- Configurable display settings for different screen sizes
- Automatic periodic refresh (default: 5 minutes)

## Stack

- Raspberry Pi
- Tkinter for GUI
- Python for backend
- TickTick Open API
- Flask for the optional webhook receiver

## Installation

### Prerequisites
- Python 3.9 or higher (the client uses `zoneinfo`)
- Tkinter (`sudo apt install python3-tk` on Raspberry Pi OS, `sudo pacman -S tk` on Arch)
- TickTick account and API token

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd todoist-notifier
```

2. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your settings:
```bash
cp .env.example .env
# Edit .env and add your TickTick API token
```

To get your TickTick API token:
1. Register an app at https://developer.ticktick.com/
2. Complete the OAuth flow to obtain an access token
3. Add it to your .env file as `TICKTICK_API_KEY`

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

### Running the Tests

```bash
# Offline: parsing and selection logic, no API token needed
python3 tests/test_task_selection.py

# Live: verifies the API token and prints today's tasks
python3 test_api.py
```

### Configuration Options

All configuration is done via environment variables in your `.env` file:

**Required:**
- `TICKTICK_API_KEY` - Your TickTick API token

**Display Settings (optional):**
- `DISPLAY_WIDTH` - Screen width in pixels (default: 800)
- `DISPLAY_HEIGHT` - Screen height in pixels (default: 480)
- `DISPLAY_FULLSCREEN` - Run fullscreen: true/false (default: false)
- `DISPLAY_FONT_SIZE` - Base font size (default: 24)
- `REFRESH_INTERVAL` - Auto-refresh interval in seconds (default: 300)

**Webhook Settings (optional):**
- `WEBHOOK_ENABLED` - Enable webhook server: true/false (default: false)

The TickTick Open API does not support webhooks, so the display refreshes by
polling on `REFRESH_INTERVAL`. The `/webhook` endpoint is retained only for a
self-hosted bridge that can POST to it to force an immediate refresh.
- `WEBHOOK_HOST` - Webhook server host (default: 0.0.0.0)
- `WEBHOOK_PORT` - Webhook server port (default: 5000)

**Task Selection (optional):**
- `FOCUS_TAG` - Label to override task selection (default: @focus)

Note: Set `WEBHOOK_ENABLED=false` if you're on university/restricted networks where you can't open ports.

### Keyboard Shortcuts

- `Escape`: Exit fullscreen mode
- `Ctrl+C`: Quit application

## Project Structure

```
todoist-notifier/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── .env                    # Your configuration (create from .env.example)
├── tests/
│   └── test_task_selection.py   # Offline tests (no token required)
└── src/
    ├── api/
    │   └── ticktick_client.py   # TickTick API wrapper
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
3. **Due time**: If priorities are equal, earlier due times take precedence. All-day
   tasks sort after timed ones, and task ID breaks any remaining tie so the same
   task list always yields the same choice.

Only tasks due **today** are considered; overdue and undated tasks are ignored.

TickTick's priorities (None/Low/Medium/High) are mapped onto the P4-P1 scale
used by the display: High is P1 (red), Medium is P2 (orange), Low is P3 (blue),
and None is P4 (grey).

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
Description=TickTick Notifier Display
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/todoist-notifier
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/pi/.Xauthority"
ExecStart=/home/pi/todoist-notifier/.venv/bin/python3 /home/pi/todoist-notifier/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=graphical.target
```

3. Enable and start the service:
```bash
sudo systemctl enable todoist-notifier
sudo systemctl start todoist-notifier
```

## Troubleshooting

**No tasks displayed:**
- Check that you have tasks due today in TickTick
- Verify your API token is correct (an expired token reports a 401)
- Check console for error messages

**Display issues on Raspberry Pi:**
- Adjust `width`, `height`, and `font_size` in config
- Try fullscreen mode for better fit
- Ensure X server is running (required for Tkinter)

## License

MIT