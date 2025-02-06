
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from os import getenv
from pathlib import Path

from rich.logging import RichHandler

from multiprocessing import Queue
from logging_loki import LokiQueueHandler

from rpa_qt.root import ROOT_DIR
from rpa_qt.utils.config_yaml_loader import settings


logger = logging.getLogger("rpa_qt")

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)-13s: - %(levelname)-8s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def configure_log(logPath=f'{ROOT_DIR}/logs', fileName='debug'):
    # Change root logger level from WARNING (default) to NOTSET in order for all messages to be delegated.
    # logging.getLogger().setLevel(logging.NOTSET)
    logging.getLogger().setLevel(logging.INFO)

    # Add stdout handler, with level INFO
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    # formater = logging.Formatter('%(asctime)s - %(name)-13s: %(levelname)-8s %(message)s')
    console.setFormatter(CustomFormatter())
    logging.getLogger().addHandler(console)

    # Add file rotating handler, with level DEBUG
    if os.path.exists(logPath) == False:
        os.makedirs(logPath)
    log_file="{0}/{1}.log".format(logPath, fileName)
    rotatingHandler = logging.handlers.RotatingFileHandler(filename=log_file, maxBytes=(1048576*5), backupCount=5, encoding='utf-8')

    rotatingHandler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)-13s: - %(levelname)-8s - %(message)s (%(filename)s:%(lineno)d)')
    rotatingHandler.setFormatter(formatter)
    logging.getLogger().addHandler(rotatingHandler)

    # has_loki = settings.has_loki
    # if False:
    #     # Add loki handler
    #     LOKI_ENDPOINT=settings.loki_url+"/loki/api/v1/push"
    #     loki_logs_handler = LokiQueueHandler(
    #         Queue(-1),
    #         url=LOKI_ENDPOINT,  #getenv("LOKI_ENDPOINT"),
    #         tags={"application": "fastapi"},
    #         version="1",
    #     )
    #     loki_logs_handler.setLevel(logging.INFO)
    #     logging.getLogger().addHandler(loki_logs_handler)

    logger.info(f"Log file: {log_file}")




