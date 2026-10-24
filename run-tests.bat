@echo off
chcp 65001 >nul
cd /d "%~dp0"
call .venv\Scripts\activate.bat
pytest tests/test_yandex_form.py -n 2 -v
echo.
echo Готово. Чтобы посмотреть Allure-отчёт, запустите open-allure-report.bat
pause
