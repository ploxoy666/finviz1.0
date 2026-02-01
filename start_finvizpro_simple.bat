@echo off
chcp 65001 >nul
title FinvizPro Launcher (Simple)

echo ========================================
echo    FinvizPro - Запуск приложения
echo ========================================
echo.

REM Получаем путь к текущей директории
set "PROJECT_DIR=%~dp0"

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден! Установите Python и добавьте его в PATH.
    pause
    exit /b 1
)

echo [1/3] Запуск бэкенда...
echo.

REM Запускаем бэкенд в новом окне
start "FinvizPro Backend" cmd /k "cd /d "%PROJECT_DIR%backend" && python app.py"

REM Ждем 10 секунд, чтобы бэкенд успел запуститься
echo [2/3] Ожидание запуска бэкенда (10 секунд)...
echo Проверьте окно "FinvizPro Backend" - там должно появиться сообщение о запуске сервера.
timeout /t 10 /nobreak

echo [3/3] Открытие фронтенда в браузере...
echo.

REM Открываем фронтенд в браузере по умолчанию
start "" "http://localhost:5000"

echo.
echo ========================================
echo    ✓ FinvizPro запущен!
echo ========================================
echo.
echo Бэкенд: http://localhost:5000
echo.
echo Для остановки закройте окно "FinvizPro Backend"
echo.
pause
