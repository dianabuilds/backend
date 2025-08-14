import os
import yaml
import logging.config
from pathlib import Path

def configure_logging(config_path=None):
    """
    Настраивает логирование из YAML-файла.
    
    Args:
        config_path: Путь к файлу конфигурации. Если None, ищет в стандартных местах.
    """
    if config_path is None:
        # Сначала проверяем переменную окружения
        config_path = os.environ.get("LOG_CONFIG")
        
        if not config_path:
            # Ищем в стандартных местах
            candidates = [
                # Текущая директория
                Path.cwd() / "logging.yaml",
                # Корень проекта
                Path(__file__).resolve().parents[2] / "logging.yaml",
                # Рядом с этим файлом
                Path(__file__).resolve().parent / "logging.yaml",
            ]
            
            for path in candidates:
                if path.exists():
                    config_path = str(path)
                    break
    
    if not config_path or not Path(config_path).exists():
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(name)s: %(message)s',
        )
        logging.warning(f"Logging config file not found, using basic configuration")
        return False
    
    # Создаем директорию для логов, если её нет
    logs_dir = Path.cwd() / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Загружаем конфигурацию и применяем её
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
        logging.info(f"Logging configured from {config_path}")
        return True
    except Exception as e:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(name)s: %(message)s',
        )
        logging.error(f"Error configuring logging from {config_path}: {e}")
        return False
