@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "INPUT_DIR=%SCRIPT_DIR%inputs"
set "OUTPUT_DIR=%SCRIPT_DIR%outputs"
set "SVG_DIR=%OUTPUT_DIR%\svg"
set "PNG_DIR=%OUTPUT_DIR%\png"

set "MERMAID_WIDTH=1600"
set "MERMAID_HEIGHT=1200"
set "MERMAID_SCALE=2"

if not exist "%SVG_DIR%" mkdir "%SVG_DIR%"
if not exist "%PNG_DIR%" mkdir "%PNG_DIR%"

:: If a file was provided, render only that file.
if not "%~1"=="" goto :renderOne

set "FOUND_FILES="
for %%f in ("%INPUT_DIR%\*.mmd") do (
    if exist "%%~ff" (
        set "FOUND_FILES=1"
        call :render "%%~ff"
        if errorlevel 1 exit /b 1
    )
)

if not defined FOUND_FILES (
    echo No .mmd files found in "%INPUT_DIR%".
    exit /b 0
)

echo Done.
exit /b 0

:renderOne
if not exist "%~1" (
    echo File not found: "%~1"
    exit /b 1
)

call :render "%~f1"
if errorlevel 1 exit /b 1

echo Done.
exit /b 0

:render
set "FILE=%~1"

echo Processing "%FILE%" -^> "%SVG_DIR%\%~n1.svg"
mmdc -i "%FILE%" -o "%SVG_DIR%\%~n1.svg" -e svg -b transparent -w %MERMAID_WIDTH% -H %MERMAID_HEIGHT% -s %MERMAID_SCALE%
if errorlevel 1 exit /b 1

echo Processing "%FILE%" -^> "%PNG_DIR%\%~n1.png"
mmdc -i "%FILE%" -o "%PNG_DIR%\%~n1.png" -b transparent -w %MERMAID_WIDTH% -H %MERMAID_HEIGHT% -s %MERMAID_SCALE%
if errorlevel 1 exit /b 1

exit /b 0