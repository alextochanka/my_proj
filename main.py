import os
import time
import signal
import sys
from multiprocessing import Process
import logging
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Создание папки для логов
os.makedirs('logs', exist_ok=True)

# Настройка логирования с правильной кодировкой
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/main.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Глобальные переменные для процессов
flask_process = None
bot_process = None


def wait_for_mysql(max_attempts=30, delay=2):
    """Ожидание доступности MySQL"""
    import mysql.connector
    from mysql.connector import Error

    logger.info("Ожидание подключения к MySQL...")

    db_config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'Tochankau110574'),
        'database': os.getenv('MYSQL_DATABASE', 'Gold_medal')
    }

    for attempt in range(max_attempts):
        try:
            # Сначала пробуем подключиться без указания базы данных
            temp_config = db_config.copy()
            temp_config.pop('database', None)

            conn = mysql.connector.connect(**temp_config)
            if conn.is_connected():
                # Проверяем существование базы данных
                cursor = conn.cursor()
                cursor.execute("SHOW DATABASES LIKE %s", (db_config['database'],))
                database_exists = cursor.fetchone()

                if not database_exists:
                    logger.info(f"База данных '{db_config['database']}' не существует, создаем...")
                    cursor.execute(f"CREATE DATABASE {db_config['database']}")
                    logger.info(f"База данных '{db_config['database']}' создана успешно")

                cursor.close()
                conn.close()
                logger.info("MySQL готов!")
                return True

        except Error as e:
            if attempt % 5 == 0:  # Логируем каждую 5-ю попытку
                logger.info(f"Ожидание MySQL... (попытка {attempt + 1}/{max_attempts}) - {e}")
            time.sleep(delay)

    logger.error(f"MySQL не доступен после {max_attempts} попыток!")
    return False


def run_flask_app():
    """Запуск Flask приложения"""
    try:
        logger.info("Запуск Flask приложения...")

        # Добавляем путь для импорта
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))

        from app import app, initialize_database

        if initialize_database():
            logger.info("База данных для Flask приложения инициализирована успешно")
            app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        else:
            logger.error("Не удалось инициализировать базу данных для Flask приложения")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Ошибка запуска Flask приложения: {e}")
        sys.exit(1)


def run_telegram_bot():
    """Запуск Telegram бота"""
    try:
        logger.info("Запуск Telegram бота...")

        # Даем время Flask приложению запуститься
        time.sleep(3)

        # Добавляем путь для импорта
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))

        import telegram_bot
        telegram_bot.start_bot()

    except ImportError as e:
        logger.error(f"Не удалось импортировать модуль telegram_bot: {e}")
        logger.info("Telegram бот будет пропущен")
    except Exception as e:
        logger.error(f"Ошибка запуска Telegram бота: {e}")
        # Не завершаем весь процесс, если бот не запустился
        logger.info("Продолжаем работу без Telegram бота")


def signal_handler(sig, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger.info("Получен сигнал завершения...")

    global flask_process, bot_process

    if flask_process and flask_process.is_alive():
        logger.info("Остановка Flask приложения...")
        flask_process.terminate()
        flask_process.join(timeout=5)
        if flask_process.is_alive():
            logger.warning("Flask процесс не завершился gracefully, принудительное завершение")
            flask_process.kill()

    if bot_process and bot_process.is_alive():
        logger.info("Остановка Telegram бота...")
        bot_process.terminate()
        bot_process.join(timeout=5)
        if bot_process.is_alive():
            logger.warning("Bot процесс не завершился gracefully, принудительное завершение")
            bot_process.kill()

    logger.info("Все процессы остановлены. Выход.")
    sys.exit(0)


def check_process_health():
    """Проверка состояния процессов"""
    global flask_process, bot_process

    issues = []

    if not flask_process or not flask_process.is_alive():
        issues.append("Flask приложение не запущено")

    if bot_process and not bot_process.is_alive():
        issues.append("Telegram бот не запущен")

    return issues


def main():
    """Основная функция запуска"""
    global flask_process, bot_process

    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Запуск Football Application System...")

    # Проверяем обязательные переменные окружения
    required_env_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
        logger.info("Проверьте файл .env в корневой директории проекта")
        sys.exit(1)

    # Ожидаем доступность MySQL
    if not wait_for_mysql():
        logger.error("Не удалось подключиться к MySQL. Завершение работы.")
        sys.exit(1)

    # Запускаем процессы
    try:
        # Запуск Flask приложения
        flask_process = Process(target=run_flask_app, name="FlaskApp")
        flask_process.daemon = True
        flask_process.start()
        logger.info(f"Flask процесс запущен (PID: {flask_process.pid})")

        # Даем время Flask приложению запуститься
        time.sleep(2)

        # Запуск Telegram бота (если модуль существует)
        try:
            # Проверяем существование модуля telegram_bot
            import importlib.util
            spec = importlib.util.find_spec("telegram_bot")

            if spec is not None:
                bot_process = Process(target=run_telegram_bot, name="TelegramBot")
                bot_process.daemon = True
                bot_process.start()
                logger.info(f"Telegram бот процесс запущен (PID: {bot_process.pid})")
            else:
                logger.info("Модуль telegram_bot не найден. Запуск только Flask приложения.")
                bot_process = None
        except Exception as e:
            logger.warning(f"Не удалось проверить модуль telegram_bot: {e}. Запуск только Flask приложения.")
            bot_process = None

        # Мониторинг процессов
        logger.info("Система запущена. Мониторинг процессов...")

        health_check_count = 0
        while True:
            time.sleep(10)
            health_check_count += 1

            # Проверяем состояние процессов каждые 30 секунд
            if health_check_count % 3 == 0:
                issues = check_process_health()
                if issues:
                    logger.warning(f"Проблемы с процессами: {', '.join(issues)}")

                # Перезапуск бота, если он упал (только если он был запущен изначально)
                if (bot_process and not bot_process.is_alive() and
                        importlib.util.find_spec("telegram_bot") is not None):
                    logger.info("Перезапуск Telegram бота...")
                    bot_process = Process(target=run_telegram_bot, name="TelegramBot")
                    bot_process.daemon = True
                    bot_process.start()
                    logger.info(f"Telegram бот перезапущен (PID: {bot_process.pid})")

            # Если Flask приложение упало - завершаем всё
            if not flask_process.is_alive():
                logger.error("Flask процесс завершился неожиданно! Завершение работы.")
                break

    except KeyboardInterrupt:
        logger.info("Прерывание пользователем...")
    except Exception as e:
        logger.error(f"Неожиданная ошибка в основном процессе: {e}")
    finally:
        signal_handler(None, None)


if __name__ == '__main__':
    main()