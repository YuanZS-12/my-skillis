@echo off
setlocal

if "%~1"=="" (
    echo Usage: skills\nx-cad\scripts\nx-run.bat path\to\journal.py
    exit /b 2
)

set JOURNAL=%~1

if not exist "%JOURNAL%" (
    echo ERROR: Journal not found: %JOURNAL%
    exit /b 2
)

if "%NXBIN%"=="" (
    echo ERROR: NXBIN is not set.
    echo Set it first, for example:
    echo   set NXBIN=C:\Program Files\Siemens\NX2206\NXBIN
    exit /b 2
)

if not exist "%NXBIN%" (
    echo ERROR: NXBIN directory does not exist: %NXBIN%
    exit /b 2
)

if exist "%NXBIN%\run_journal.exe" (
    "%NXBIN%\run_journal.exe" "%JOURNAL%"
    exit /b %ERRORLEVEL%
)

if exist "%NXBIN%\ugraf.exe" (
    "%NXBIN%\ugraf.exe" -nx -python "%JOURNAL%"
    exit /b %ERRORLEVEL%
)

echo ERROR: Could not find run_journal.exe or ugraf.exe in %NXBIN%
exit /b 2
