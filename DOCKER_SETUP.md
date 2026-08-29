# Docker Setup with X11 GUI Support (macOS)

This guide will help you test the TickTick Notifier GUI on macOS using Docker with X11 forwarding.

## Prerequisites

1. **Docker Desktop** - Install from https://www.docker.com/products/docker-desktop
2. **XQuartz** - X11 server for macOS

## Step 1: Install XQuartz

```bash
# Install via Homebrew
brew install --cask xquartz

# Or download directly from: https://www.xquartz.org/
```

## Step 2: Configure XQuartz

1. **Start XQuartz**:
   ```bash
   open -a XQuartz
   ```

2. **Enable network connections**:
   - Go to XQuartz > Preferences (or press `⌘,`)
   - Navigate to the "Security" tab
   - Check "Allow connections from network clients"
   - Click "Restart" if prompted, or quit and restart XQuartz manually

3. **Restart XQuartz** to apply changes:
   ```bash
   # Quit XQuartz
   killall XQuartz

   # Start it again
   open -a XQuartz
   ```

## Step 3: Allow Docker to Connect to X11

Each time you start XQuartz, you need to allow Docker containers to connect:

```bash
# Add localhost to X11 access control list
xhost + localhost
```

You should see: `localhost being added to access control list`

**Note**: You'll need to run this command each time you restart XQuartz.

## Step 4: Verify Your Setup

Check that XQuartz is running and configured correctly:

```bash
# Verify DISPLAY is set (should show something like /private/tmp/com.apple.launchd.xxx/org.xquartz:0)
echo $DISPLAY

# Check X11 socket exists
ls -la /tmp/.X11-unix/
```

## Step 5: Run the Application

```bash
# Make sure you have a .env file with your TICKTICK_API_KEY
# Then build and run:
docker-compose up --build
```

The Tkinter GUI window should appear on your Mac!

## Troubleshooting

### "Cannot open display" Error

If you see `_tkinter.TclError: couldn't connect to display "host.docker.internal:0"`:

1. Make sure XQuartz is running
2. Run `xhost + localhost` again
3. Restart the Docker container

### No Window Appears

1. Check XQuartz is running: `ps aux | grep XQuartz`
2. Verify X11 socket: `ls /tmp/.X11-unix/`
3. Check Docker logs: `docker-compose logs`

### XQuartz Preferences Not Saving

- Try running XQuartz with sudo once to set preferences: `sudo open -a XQuartz`
- Then restart normally

### Performance Issues

X11 forwarding can be slower than native display. This is normal for testing purposes.

## Alternative: Test Without GUI

If X11 setup is too complex, consider testing the core logic without GUI:

```bash
# Test the API and task selection logic directly in Python
docker-compose exec todoist-notifier python3 -c "
import sys; sys.path.insert(0, 'src')
from api.ticktick_client import TickTickClient
from logic.task_selector import TaskSelector
import os

client = TickTickClient(os.getenv('TICKTICK_API_KEY'))
selector = TaskSelector('@focus')
task = selector.select_most_important_task(client.get_today_tasks())
print(f'Most important task: {task}')
"
```

## Notes

- X11 forwarding is only needed for testing on macOS
- On the actual Raspberry Pi, the display works natively without any special setup
- Once tested, you can deploy directly to your Raspberry Pi
