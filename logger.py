import logging

import config


def setup_logger():
    logger_ = logging.getLogger('LavochkiBot')
    logger_.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s - %(name)s: "%(message)s"'
    )

    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(formatter)
    logger_.addHandler(stderr_handler)

    if config.bot_log_file is not None:
        file_handler = logging.FileHandler(config.bot_log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger_.addHandler(file_handler)

    return logger_


bot_logger = setup_logger()
