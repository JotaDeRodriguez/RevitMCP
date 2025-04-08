@echo off
REM MCP Server Launcher
REM Launches the MCP server with specified ports

echo ===== MCP Server Launch: %date% %time% ===== 

REM Set default ports and implementation
set MCP_PORT=9876
set REVIT_PORT=9877
set MODEL=claude-3-7-sonnet-latest
set API_KEY=
set MODERN=0

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :end_parse_args
if /i "%~1"=="--modern" (
    set MODERN=1
    shift
    goto :parse_args
)
if not "%~1"=="" (
    set MCP_PORT=%~1
    shift
)
if not "%~1"=="" (
    set REVIT_PORT=%~1
    shift
)
if not "%~1"=="" (
    set MODEL=%~1
    shift
)
if not "%~1"=="" (
    set API_KEY=%~1
    shift
)
goto :parse_args
:end_parse_args

REM Check for Python executable
echo Looking for Python executable...
where python > NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python not found in PATH
    echo Checking Python registry key...
    for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\Python\PythonCore\3.11\InstallPath" /ve 2^>NUL') do (
        set "PYTHON_EXE=%%b\python.exe"
    )
    if not defined PYTHON_EXE (
        for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\Python\PythonCore\3.10\InstallPath" /ve 2^>NUL') do (
            set "PYTHON_EXE=%%b\python.exe"
        )
    )
    if not defined PYTHON_EXE (
        for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\Python\PythonCore\3.9\InstallPath" /ve 2^>NUL') do (
            set "PYTHON_EXE=%%b\python.exe"
        )
    )
    if not defined PYTHON_EXE (
        echo Python not found! Please install Python 3.9 or newer.
        echo.
        echo Press any key to exit...
        pause > NUL
        exit /b 1
    )
) else (
    set "PYTHON_EXE=python"
    echo Found Python using 'python' command
)

REM Create logs directory if it doesn't exist
if not exist "%~dp0logs" mkdir "%~dp0logs"

REM Check Python version
echo Python version:
%PYTHON_EXE% --version > "%~dp0logs\launcher.log" 2>&1
%PYTHON_EXE% -c "import sys; print('Python', sys.version); print('Path:', sys.path)" >> "%~dp0logs\launcher.log" 2>&1

REM Ensure pip is up to date
echo Upgrading pip...
%PYTHON_EXE% -m pip install --upgrade pip >> "%~dp0logs\launcher.log" 2>&1

REM Install dependencies with detailed logging
echo Installing dependencies from requirements.txt...
%PYTHON_EXE% -m pip install -r "%~dp0requirements.txt" >> "%~dp0logs\launcher.log" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error installing dependencies from requirements.txt
    echo Check logs\launcher.log for details
    echo.
    echo Attempting to install packages directly...
    
    REM Install all dependencies directly
    %PYTHON_EXE% -m pip install fastapi>=0.104.1 uvicorn>=0.24.0 anthropic>=0.8.0 python-dotenv>=1.0.0 requests>=2.31.0 websockets>=11.0.3 pydantic>=2.0.0 urllib3>=2.0.0 httpx>=0.25.0 "mcp[cli]>=0.1.0" >> "%~dp0logs\launcher.log" 2>&1
    
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install dependencies. Please check your internet connection.
        echo See logs\launcher.log for details.
        echo.
        echo Press any key to exit...
        pause > NUL
        exit /b 1
    )
)

REM Verify MCP installation
echo Verifying MCP installation...
%PYTHON_EXE% -c "import mcp; print(f'MCP version: {mcp.__version__}')" >> "%~dp0logs\launcher.log" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Unable to verify MCP installation. Continuing anyway...
) else (
    echo MCP successfully installed.
)

REM Determine which server implementation to use
if "%MODERN%"=="1" (
    set "SCRIPT_PATH=%~dp0server_mcp.py"
    echo Using modern MCP implementation (server_mcp.py)
) else (
    set "SCRIPT_PATH=%~dp0server.py"
    echo Using legacy implementation (server.py)
)

echo.
echo Configuration Summary:
echo ---------------------
echo Python executable: %PYTHON_EXE%
echo Server script: %SCRIPT_PATH%
echo MCP Port: %MCP_PORT%
echo Revit Port: %REVIT_PORT%
echo Model: %MODEL%
if "%API_KEY%"=="" (
    echo API Key: Not set
) else (
    echo API Key: [MASKED]
)
echo.

REM Run server
echo Starting server process...
echo.
echo When finished, press Ctrl+C to stop the server.
echo.

if "%MODERN%"=="1" (
    %PYTHON_EXE% "%SCRIPT_PATH%" --mcp-port %MCP_PORT% --revit-port %REVIT_PORT% --model "%MODEL%" --api-key "%API_KEY%"
) else (
    %PYTHON_EXE% "%SCRIPT_PATH%" --mcp-port %MCP_PORT% --revit-port %REVIT_PORT% --model "%MODEL%" --api-key "%API_KEY%"
)

REM Check if server exited with an error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Server exited with error code: %ERRORLEVEL%
    echo Check logs\launcher.log for details.
    echo.
    echo Press any key to exit...
    pause > NUL
) else (
    echo.
    echo Server stopped successfully.
)

exit /b %ERRORLEVEL% 