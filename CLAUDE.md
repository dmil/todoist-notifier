# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a TickTick notification display application designed to run on a Raspberry Pi with a small screen. The app displays a single, most important task from TickTick at a glance.

**Target Platform:** Raspberry Pi
**Display:** Tkinter GUI on a small screen
**Backend:** Python
**External API:** TickTick Open API (https://api.ticktick.com/open/v1)

## Key Features

- Displays the most important task for today based on priority and due date
- Support for `@focus` tag to manually override task selection
- Periodic polling for updates (the TickTick Open API has no webhooks)

## Development Setup

This project is in early stages. When implementing, you'll need to:

1. Set up Python virtual environment for development
2. Install dependencies (`requests`, Flask, Tkinter)
3. Configure TickTick API credentials in `.env` as `TICKTICK_API_KEY`
4. Run `python3 tests/test_task_selection.py` for offline checks, `python3 test_api.py` for a live check

## Architecture Notes

The application will need these core components:

1. **Task Selection Logic**: Algorithm to determine "most important" task based on:
   - Priority level (normalised from TickTick's 0/1/3/5 scale to an internal 1-4 scale)
   - Due date/time
   - `@focus` tag override

2. **TickTick Integration**:
   - API client for fetching tasks
   - Bearer-token authentication
   - The Open API has no "all tasks" endpoint, so the client enumerates every
     project (plus the Inbox, which the project listing omits) and filters locally
   - Due dates arrive as UTC instants with a per-task `timeZone`; convert into
     that zone before comparing against today, and honour the `isAllDay` flag

3. **GUI Layer**: Tkinter-based display optimized for small screens (Raspberry Pi)

4. **State Management**: Handle task updates and refresh cycles

## Raspberry Pi Considerations

- Tkinter must be configured for the specific screen resolution
- Consider power management for always-on display
- Network connectivity required for TickTick API access
- Each refresh costs one request per project, so keep `REFRESH_INTERVAL` reasonable
