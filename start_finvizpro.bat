@echo off
chcp 65001 >nul
title FinvizPro Launcher

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

REM Проверяем наличие необходимых зависимостей
echo [1/4] Проверка зависимостей...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [ВНИМАНИЕ] Flask не установлен. Устанавливаю зависимости...
    cd /d "%PROJECT_DIR%backend"
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось установить зависимости!
        pause
        exit /b 1
    )
)

echo [2/4] Запуск бэкенда...
echo.

REM Запускаем бэкенд в новом окне
start "FinvizPro Backend" cmd /k "cd /d "%PROJECT_DIR%backend" && python app.py"

REM Ждем запуска бэкенда с проверкой доступности
echo [3/4] Ожидание запуска бэкенда...
set /a counter=0
:wait_loop
timeout /t 1 /nobreak >nul
set /a counter+=1

REM Проверяем, доступен ли сервер (используем curl если доступен, иначе просто ждем)
curl -s http://localhost:5000 >nul 2>&1
if %errorlevel% equ 0 (
    echo [✓] Бэкенд успешно запущен!
    goto backend_ready
)

if %counter% lss 15 (
    echo Ожидание... (%counter%/15 сек^)
    goto wait_loop
)

echo [ВНИМАНИЕ] Бэкенд не ответил за 15 секунд. Открываю браузер...
echo Если страница не загрузится, проверьте окно "FinvizPro Backend" на наличие ошибок.

:backend_ready
echo.
echo [4/4] Открытие фронтенда в браузере...
echo.

REM Открываем фронтенд в браузере по умолчанию
start "" "http://localhost:5000"

echo.
echo ========================================
echo    ✓ FinvizPro успешно запущен!
echo ========================================
echo.
echo Бэкенд: http://localhost:5000
echo Фронтенд: http://localhost:5000
echo.
echo Для остановки закройте окно "FinvizPro Backend"
echo.
pause
