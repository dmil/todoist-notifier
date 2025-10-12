# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Todoist notification display application designed to run on a Raspberry Pi with a small screen. The app displays a single, most important task from Todoist at a glance.

**Target Platform:** Raspberry Pi
**Display:** Tkinter GUI on a small screen
**Backend:** Python
**External API:** Todoist API

## Key Features

- Displays the most important task for today based on priority and due date
- Support for `@focus` tag to manually override task selection
- Real-time updates via Todoist Webhooks

## Development Setup

This project is in early stages. When implementing, you'll need to:

1. Set up Python virtual environment for development
2. Install dependencies (Todoist API client, Tkinter)
3. Configure Todoist API credentials
4. Set up webhook endpoint for real-time updates

## Architecture Notes

The application will need these core components:

1. **Task Selection Logic**: Algorithm to determine "most important" task based on:
   - Priority level (from Todoist)
   - Due date/time
   - `@focus` tag override

2. **Todoist Integration**:
   - API client for fetching tasks
   - Webhook receiver for real-time updates
   - Authentication handling

3. **GUI Layer**: Tkinter-based display optimized for small screens (Raspberry Pi)

4. **State Management**: Handle task updates and refresh cycles

## Raspberry Pi Considerations

- Tkinter must be configured for the specific screen resolution
- Consider power management for always-on display
- Network connectivity required for Todoist API access
- Webhook server needs to be accessible (consider ngrok or port forwarding for development)
