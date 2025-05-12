import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Загружаем настройки из .env
load_dotenv()

# Создаем директорию для логов, если она не существует
if not os.path.exists("logs"):
    os.makedirs("logs")

# Настраиваем логгер
logger = logging.getLogger("CityFeedbackBot")
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

# Создаем форматтер
formatter = logging.Formatter(
    os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
)

# Создаем обработчик для файла
log_file = f"logs/bot_{datetime.now().strftime('%Y-%m-%d')}.log"
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Создаем обработчик для консоли
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Отключаем логи от других модулей
logging.getLogger("vk_api").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING) 