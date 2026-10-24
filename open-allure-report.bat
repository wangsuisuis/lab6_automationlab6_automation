@echo off
chcp 65001 >nul
title Allure report - Lab 6
echo Запуск Allure-отчёта: http://127.0.0.1:8901
echo Не закрывайте это окно, пока смотрите отчёт (Ctrl+C — остановить).
echo.
"D:\lr6_work\allure_cli\allure-2.29.0\bin\allure.bat" open "%~dp0allure-report" -h 127.0.0.1 -p 8901
pause
