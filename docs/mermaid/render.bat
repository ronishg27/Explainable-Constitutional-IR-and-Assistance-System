@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "INPUT_DIR=%SCRIPT_DIR%inputs"
set "OUTPUT_DIR=%SCRIPT_DIR%outputs"

rem SVG + PNG export: viewport size + scale (Puppeteer). Tune MERMAID_* as needed.
set "MERMAID_WIDTH=1600"
set "MERMAID_HEIGHT=1200"
set "MERMAID_SCALE=2"

if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

set "FOUND_FILES="
for %%f in ("%INPUT_DIR%\*.mmd") do (
    if exist "%%~ff" (
        set "FOUND_FILES=1"
        echo Processing %%~ff -^> %OUTPUT_DIR%\%%~nf.svg
        mmdc -i "%%~ff" -o "%OUTPUT_DIR%\%%~nf.svg" -e svg -b transparent -w %MERMAID_WIDTH% -H %MERMAID_HEIGHT% -s %MERMAID_SCALE%
        if errorlevel 1 exit /b 1
        echo Processing %%~ff -^> %OUTPUT_DIR%\%%~nf.png
        mmdc -i "%%~ff" -o "%OUTPUT_DIR%\%%~nf.png" -b transparent -w %MERMAID_WIDTH% -H %MERMAID_HEIGHT% -s %MERMAID_SCALE%
        if errorlevel 1 exit /b 1
    )
)

if not defined FOUND_FILES (
    echo No .mmd files found in "%INPUT_DIR%".
    exit /b 0
)

echo Done.
endlocal
