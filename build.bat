@echo off
setlocal

rem ============================================================================
rem  Builds CrayonAllPortals_v<version>.exe into the dist folder.
rem
rem  The version comes from version.txt (e.g. 1_6), the same file the app shows
rem  in its title bar. Bump it there, then double-click this file.
rem ============================================================================

rem Always run from the project folder, wherever this was started from
cd /d "%~dp0"

if not exist "version.txt" (
    echo Missing version.txt next to build.bat
    goto :fail
)
set /p VERSION=<version.txt
set "NAME=CrayonAllPortals_v%VERSION%"

rem Use the project's virtual environment if there is one, otherwise Python on PATH
set "PYTHON=python"
if exist "portals_venv\Scripts\python.exe" set "PYTHON=portals_venv\Scripts\python.exe"

"%PYTHON%" --version >nul 2>&1
if errorlevel 1 (
    echo Python was not found. Install Python and make sure it is on PATH.
    goto :fail
)

for %%F in (CrayonAllPortals.py simple_rings.png icon.ico logo.png version.txt) do (
    if not exist "%%F" (
        echo Missing %%F next to build.bat
        goto :fail
    )
)

echo.
echo === Checking packages ===
"%PYTHON%" -m pip install --disable-pip-version-check --quiet -r requirements.txt pyinstaller
if errorlevel 1 goto :fail

echo.
echo === Building %NAME%.exe (takes a few minutes) ===
"%PYTHON%" -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --icon=icon.ico ^
    --collect-all ortools ^
    --name "%NAME%" ^
    --add-data "simple_rings.png;." ^
    --add-data "icon.ico;." ^
    --add-data "logo.png;." ^
    --add-data "version.txt;." ^
    CrayonAllPortals.py
if errorlevel 1 goto :fail

echo.
echo Done: %CD%\dist\%NAME%.exe
pause
exit /b 0

:fail
echo.
echo Build failed.
pause
exit /b 1
