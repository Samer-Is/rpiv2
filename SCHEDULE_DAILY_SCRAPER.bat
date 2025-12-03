@echo off
REM ============================================
REM Schedule Daily Competitor Price Scraper
REM This will create a Windows Task Scheduler entry
REM to run the scraper every day at midnight
REM ============================================

echo.
echo ====================================================
echo   Scheduling Daily Competitor Price Scraper
echo ====================================================
echo.
echo This will create a scheduled task to run daily at midnight
echo.
pause

REM Get the current directory
set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%daily_competitor_scraper.py

REM Create the scheduled task
schtasks /create /tn "RentyCompetitorPriceScraper" /tr "python \"%PYTHON_SCRIPT%\"" /sc daily /st 00:00 /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ====================================================
    echo   SUCCESS: Scheduled task created!
    echo ====================================================
    echo.
    echo Task Name: RentyCompetitorPriceScraper
    echo Schedule: Daily at 12:00 AM
    echo Script: %PYTHON_SCRIPT%
    echo.
    echo To view the task:
    echo   schtasks /query /tn "RentyCompetitorPriceScraper"
    echo.
    echo To run manually now:
    echo   schtasks /run /tn "RentyCompetitorPriceScraper"
    echo.
    echo To delete the task:
    echo   schtasks /delete /tn "RentyCompetitorPriceScraper" /f
    echo.
) else (
    echo.
    echo ====================================================
    echo   FAILED: Could not create scheduled task
    echo ====================================================
    echo.
    echo Please run this script as Administrator
    echo.
)

pause




