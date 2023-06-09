import logging

import sqlalchemy.exc as exc

import config


def setup_logger():
    logger_ = logging.getLogger('Database')
    logger_.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s - %(name)s: "%(message)s"'
    )

    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(formatter)
    logger_.addHandler(stderr_handler)

    if config.database_log_file is not None:
        file_handler = logging.FileHandler(config.database_log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger_.addHandler(file_handler)

    return logger_


def log(func):
    def wrapper(*args, **kwargs):
        logger.info(f'Function {func.__module__}.{func.__name__} called with args: {args}, kwargs: {kwargs}')
        try:
            result = func(*args, **kwargs)
            logger.info(f'Function {func.__module__}.{func.__name__} returned {result}')
            return result
        except exc.SQLAlchemyError as e:
            logger.error(f'Function {func.__module__}.{func.__name__} raised {e}')
            raise exc.SQLAlchemyError(f"{func.__module__}.{func.__name__}, error description: {e.args[0]}!")

    return wrapper


logger = setup_logger()
