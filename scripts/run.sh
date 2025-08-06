#!/bin/bash
# Скрипт для запуска приложения в разных режимах

# Установка переменных по умолчанию
HOST="0.0.0.0"
PORT="8000"
WORKERS=4
ENVIRONMENT=${ENVIRONMENT:-"development"}

# Функция для вывода справки
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  -d, --dev        Run in development mode with auto-reload"
    echo "  -p, --prod       Run in production mode with multiple workers"
    echo "  --host HOST      Specify host (default: 0.0.0.0)"
    echo "  --port PORT      Specify port (default: 8000)"
    echo "  --workers N      Specify number of workers (default: 4, only in prod mode)"
    echo ""
    echo "Examples:"
    echo "  $0 --dev         Run in development mode"
    echo "  $0 --prod        Run in production mode"
    echo "  $0 --prod --port 5000 --workers 8  Run in production on port 5000 with 8 workers"
}

# Обработка аргументов командной строки
MODE="dev"
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--dev)
            MODE="dev"
            shift
            ;;
        -p|--prod)
            MODE="prod"
            shift
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Переход в корневую директорию проекта
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR/.."

# Установка переменной окружения для продакшена
if [ "$MODE" = "prod" ]; then
    export ENVIRONMENT="production"
    echo "Running in PRODUCTION mode"
else
    export ENVIRONMENT="development"
    echo "Running in DEVELOPMENT mode"
fi

# Проверка наличия миграций и применение их при необходимости
echo "Checking database migrations..."
python scripts/init_db.py

# Запуск приложения в соответствующем режиме
if [ "$MODE" = "dev" ]; then
    echo "Starting development server at $HOST:$PORT with auto-reload"
    uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
else
    echo "Starting production server at $HOST:$PORT with $WORKERS workers"
    gunicorn app.main:app -w "$WORKERS" -k uvicorn.workers.UvicornWorker --bind "$HOST:$PORT"
fi
