
@echo off
REM Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Try install python through chocolatey.
    echo install chocolatey from https://chocolatey.org/install
    @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "[System.Net.ServicePointManager]::SecurityProtocol = 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
    choco install uv -y
    uv install python -y
    REM Check if Python installation was successful
    python --version >nul 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        echo Failed to install Python.
        exit /b %ERRORLEVEL% 
    )
    )

REM Check if chromedriver is installed
IF NOT EXIST "chromedriver.exe" (
    echo Chromedriver is not installed. Installing...
    REM Install chromedriver using Chocolatey
    choco install chromedriver -y
)

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