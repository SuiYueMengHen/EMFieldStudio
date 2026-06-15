import logging
import os
import sys
from datetime import datetime


_logger = None


def get_logger(name: str = "DiffractionLab", level: int = logging.INFO) -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)-8s %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        try:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f'diffraction_{datetime.now().strftime("%Y%m%d")}.log')
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass

    _logger = logger
    return logger


def set_log_level(level: int):
    logger = get_logger()
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)
