@echo off
echo ========================================
echo   Renty - Intelligent Dynamic Pricing
echo ========================================
echo.
echo Opening dashboard on: http://localhost:8502
echo.
echo Press Ctrl+C to stop the dashboard
echo ========================================
echo.

cd /d "%~dp0"
streamlit run dashboard_manager.py --server.port 8502

pause

