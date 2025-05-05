# Appointment Checker 🚀

> **⚠️ WARNING / 警告:**
> This project is **intended for educational and testing purposes only**. Any illegal or unauthorized use is **strictly at your own risk**.
> 本项目仅供学习和测试用途，任何不合法或未授权的使用风险自负。

---

## Table of Contents

* [Features](#features)
* [Requirements](#requirements)
* [Setup](#setup)
* [Service Mode](#service-mode)
* [License](#license)

---

## Features

* **Automated Appointment Checking:**
  Never miss an available slot at the Munich registration office with our reliable Auto-Checker.
* **Dual Modes:**
  Choose between the power of a CLI or a user-friendly GUI for maximum flexibility.
* **Service-Ready:**
  Deploy as a Windows service seamlessly using [`ServiceWrapper`](src/ServiceWrapper.py).

---

## Requirements

This project uses modern Python. See [pyproject.toml](pyproject.toml) and [requirements.txt](requirements.txt) for all dependencies.

---

## Setup

### 1. Command-Line Wizardry

```bat
run.bat
```

This script will:

1. Create a virtual environment.
2. Install dependencies.
3. Launch the CLI interface (`src/Main.py`).

### 2. Graphical Spellcasting

```bat
rungui.bat
```

Launches the GUI at [`src/gui/main.py`](src/gui/main.py) for a visual experience.

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

## License

MIT License

© 2025 \[Ylogos]

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

* The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED. ANY ILLEGAL USE IS AT YOUR OWN RISK.**
