
@echo off
REM Check if Chrome is installed
IF NOT EXIST "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo Google Chrome is not installed. Please install it from https://www.google.com/chrome/
    
    echo try using chocolatey to install chrome
    echo Check if chocolatey is installed
    choco --version >nul 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        echo Chocolatey is not installed. Try install chocolatey from https://chocolatey.org/install
        @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "[System.Net.ServicePointManager]::SecurityProtocol = 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
    )
    choco install googlechrome -y
)

REM Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Try install uv through chocolatey.
    echo Check if chocolatey is installed
    choco --version >nul 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        echo Chocolatey is not installed. Try install chocolatey from https://chocolatey.org/install
        @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "[System.Net.ServicePointManager]::SecurityProtocol = 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
    )

    REM Check if uv is installed
    uv --version >nul 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        echo uv is not installed. Installing...
        choco install uv -y
    )
    
    uv run src/Main.py
    )
else (
    REM Check if virtual environment exists
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment.
        exit /b %ERRORLEVEL%
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install dependencies
pip install -r requirements.txt

REM Run Main.py
python src/Main.py
)



