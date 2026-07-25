@echo off
setlocal EnableExtensions

REM Kami local Windows PDF runner
REM Usage:
REM   render_pdf.cmd "<HTML_PATH>" "<PDF_PATH>"

set "LOCAL_DIR=%~dp0"
set "PY_SCRIPT=%LOCAL_DIR%render_pdf.py"
set "RESULT_JSON=%LOCAL_DIR%render_result.json"
set "LOG_FILE=%LOCAL_DIR%render_pdf.log"

if "%~1"=="" goto usage
if "%~2"=="" goto usage

REM Prefer the known working Python 3.12 with WeasyPrint
set "PYTHON_EXE="
if exist "C:\Program Files\Python312\python.exe" set "PYTHON_EXE=C:\Program Files\Python312\python.exe"
if not defined PYTHON_EXE (
  where python >nul 2>&1 && for /f "delims=" %%I in ('where python') do (
    if not defined PYTHON_EXE set "PYTHON_EXE=%%I"
  )
)

if not defined PYTHON_EXE (
  >"%RESULT_JSON%" echo {"success": false, "html": "%~1", "pdf": "%~2", "size": 0, "error": "python.exe not found"}
  >"%LOG_FILE%" echo [error] python.exe not found
  exit /b 1
)

"%PYTHON_EXE%" "%PY_SCRIPT%" "%~1" "%~2"
set "RC=%ERRORLEVEL%"
exit /b %RC%

:usage
>"%RESULT_JSON%" echo {"success": false, "html": "", "pdf": "", "size": 0, "error": "Usage: render_pdf.cmd HTML_PATH PDF_PATH"}
>"%LOG_FILE%" echo [error] Usage: render_pdf.cmd HTML_PATH PDF_PATH
exit /b 2
