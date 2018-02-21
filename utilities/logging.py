import logging
import os
dir_path = os.path.dirname(os.path.realpath(__file__))


def configure_logging(handler_type):
    logger = logging.getLogger()
    if "file" in str(handler_type):
        filename = dir_path + os.sep + "scraper.log"
        os.remove(filename) if os.path.exists(filename) else None
        handler = logging.FileHandler(filename=filename)
    else:
        handler = logging.StreamHandler()

    logFormatter = logging.Formatter("%(filename)s:%(lineno)s %(asctime)s [%(levelname)-5.5s]  %(message)s")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logFormatter)
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    logger.propagate = False

    return logger
