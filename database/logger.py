import logging


def setup_logger():
    logger_ = logging.getLogger('Database')
    logger_.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s - %(name)s: "%(message)s"'
    )

    stderr_handler = logging.StreamHandler()
    file_handler = logging.FileHandler('database.log')
    file_handler.setFormatter(formatter)
    stderr_handler.setFormatter(formatter)

    logger_.addHandler(file_handler)
    logger_.addHandler(stderr_handler)

    return logger_


def log(func):
    def wrapper(*args, **kwargs):
        logger.info(f'Function {func.__module__}.{func.__name__} called with args: {args}, kwargs: {kwargs}')
        result = func(*args, **kwargs)
        logger.info(f'Function {func.__module__}.{func.__name__} returned {result}')
        return result

    return wrapper


logger = setup_logger()
