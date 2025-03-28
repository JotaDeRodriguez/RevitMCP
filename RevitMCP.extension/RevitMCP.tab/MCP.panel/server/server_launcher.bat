@echo off
REM MCP Server Launcher
REM Launches the MCP server with specified ports

set MCP_PORT=%1
set REVIT_PORT=%2

REM Check if ports were provided
if "%MCP_PORT%"=="" (
    set MCP_PORT=9876
)
if "%REVIT_PORT%"=="" (
    set REVIT_PORT=9877
)

echo Starting MCP Server on ports %MCP_PORT% (MCP) and %REVIT_PORT% (Revit)

REM Try to find Python executable
where python > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
    goto :RUN_SERVER
)

where py > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=py
    goto :RUN_SERVER
)

echo Python not found in PATH. Please add Python to your PATH.
exit /b 1

:RUN_SERVER
REM Get the directory of this script
set SCRIPT_DIR=%~dp0
set SERVER_SCRIPT=%SCRIPT_DIR%dummy_server.py

echo Running server using %PYTHON_CMD% %SERVER_SCRIPT% %MCP_PORT% %REVIT_PORT%
%PYTHON_CMD% "%SERVER_SCRIPT%" %MCP_PORT% %REVIT_PORT%

exit /b 0 