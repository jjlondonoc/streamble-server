import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(log_to_console: bool = False, verbose: bool = False):
    """
    Configure all logging system

    Parameters:
        log_to_console (bool): if True, show logs in cmd.
        verbose (bool): if True, include DEBUG messages instead of INFO.
    """
    # Create path if not exists
    os.makedirs("logs", exist_ok=True)

    # Root logger configuration
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Log's format
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

    # Handler for file
    file_handler = RotatingFileHandler(
        "logs/streamble.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Print in cmd
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.info("Logger configured succesfully")