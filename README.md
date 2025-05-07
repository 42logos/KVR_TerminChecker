# Appointment Checker 🚀

> **⚠️ WARNING / 警告:**  
> This project is **intended for educational and testing purposes only**. Any illegal or unauthorized use is **strictly at your own risk**.  
> 本项目仅供学习和测试用途，任何不合法或未授权的使用风险自负。

---

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Requirements](#requirements)
- [Setup](#setup)
- [Usage](#usage)
- [Configuration](#configuration)
- [Service Mode](#service-mode)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

- **Automated Appointment Checking:**  
  Reliably monitors the Munich registration office for available slots.
- **Dual Modes:**  
  Use either a command-line interface or a modern GUI ([`src/gui/main.py`](src/gui/main.py)).
- **Service-Ready:**  
  Deploy as a Windows service using [`ServiceWrapper`](src/ServiceWrapper.py).
- **Logging:**  
  Detailed logs are saved in the `logs/` directory for auditing and debugging.
- **Configurable:**  
  All major parameters (service/location IDs, target date, intervals) are easily adjustable in [`src/config.py`](src/config.py) and `settings.toml`.
- **Progress Feedback:**  
  CLI mode uses `tqdm` for progress bars; GUI mode displays real-time logs.

---


## Requirements

- **Python:** 3.11 or newer
- **OS:** Windows (service mode supported)
- **Dependencies:**  
  See [pyproject.toml](pyproject.toml) and [requirements.txt](requirements.txt) for all required packages.

---

## Setup

### 1. Command-Line Mode

```bat
run.bat
```

This script will:
1. Create a virtual environment.
2. Install dependencies.
3. Launch the CLI interface ([`src/Main.py`](src/Main.py)).

### 2. Graphical Mode

```bat
rungui.bat
```

This launches the GUI ([`src/gui/main.py`](src/gui/main.py)) for a visual experience.

---

## Usage

### CLI

- Edit configuration in [`src/config.py`](src/config.py) or `settings.toml` as needed.
- Run `run.bat` or `python src/Main.py`.

### GUI

- Run `rungui.bat` or `python src/gui/main.py`.
- The GUI displays logs and allows for easier monitoring.

---

## Configuration

You can configure the appointment checker using either [`src/config.py`](src/config.py) (for advanced users) or the user-friendly [`settings.toml`](settings.toml) file.

### Editing `settings.toml`

Open `settings.toml` and adjust the following parameters:

| Name              | Description                                                                                   | Example           |
|-------------------|----------------------------------------------------------------------------------------------|-------------------|
| `SERVICE_ID`      | The unique ID for the service you want to book (e.g., registration, passport, etc.).         | `"10339027"`      |
| `LOCATION_ID`     | The unique ID for the office/location where you want the appointment.                        | `"10187259"`      |
| `TARGET_DATE`     | The specific date you want to book (format: `YYYY-MM-DD`). Leave empty to list all dates.    | `"2025-06-07"`    |
| `TIMEOUT`         | Maximum time (in seconds) to wait for web elements to load (Selenium explicit wait).         | `20`              |
| `BREAK_INTERVAL`  | Time (in seconds) to wait between each check for available appointments.                     | `5`               |
| `RESTART_INTERVAL`| Time (in seconds) after which the script will restart the browser session.                   | `35`              |
| `HEADLESS`        | Run browser in headless mode (`true` = no window, `false` = show browser window).            | `true`            |

#### Example

```toml
SERVICE_ID = "10339027"      # Service type (change to your desired service)
LOCATION_ID = "10187259"     # Location ID (change to your desired location)
TARGET_DATE = "2025-06-07"   # Target date (leave empty to list all available dates)
TIMEOUT = 20                 # Selenium explicit wait time (seconds)
BREAK_INTERVAL = 5           # Interval between checks (seconds)
RESTART_INTERVAL = 35        # Restart interval (seconds)
HEADLESS = true              # Run browser in headless mode (no window)
```

#### How to Use

1. Open `settings.toml` in a text editor.
2. Change the values as needed (see table above).
3. Save the file.
4. Run the program as usual (`run.bat`, `rungui.bat`, or directly with Python).

#### Advanced: Environment Variables

You can override any setting by exporting environment variables before running the program. For example:

```powershell
$env:DYNACONF_SERVICE_ID="your_service_id"
$env:DYNACONF_LOCATION_ID="your_location_id"
python src/Main.py
```

### Logging

- All logs are saved in the `logs/YYYY-MM-DD.log` file.
- Logs are also displayed in real-time in the GUI.

For more details on configuration, see comments in [`settings.toml`](settings.toml) and [`src/config.py`](src/config.py).
---

## Service Mode

Use [`ServiceWrapper`](src/ServiceWrapper.py) to install and manage this tool as a Windows service:

```bat
# Install the service
python ServiceWrapper.py install

# Start the service
python ServiceWrapper.py start

# Stop the service
python ServiceWrapper.py stop

# Uninstall the service
python ServiceWrapper.py remove
```

---

## Troubleshooting

- **No appointments found:**  
  Check your `SERVICE_ID`, `LOCATION_ID`, and `TARGET_DATE` in the config.
- **Webdriver errors:**  
  Ensure Chrome is installed and up to date.
- **Permission issues:**  
  Run as administrator if installing as a service.
- **Logs:**  
  Review logs in the `logs/` directory for error details.

---

## License

MIT License

© 2025 [Ylogos]

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

* The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED. ANY ILLEGAL USE IS AT YOUR OWN RISK.**
