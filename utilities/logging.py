import logging
import os
import uuid

logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)
logging.getLogger("ThreadPool").setLevel(logging.CRITICAL)


def configure_logging(handler_type, log_dir=""):
    logger = logging.getLogger()
    if "file" in str(handler_type):
        name = str(uuid.uuid4())
        filename = log_dir + os.sep + "{}.log".format(name)
        os.remove(filename) if os.path.exists(filename) else None
        handler = logging.FileHandler(filename=filename)
    else:
        handler = logging.StreamHandler()

    logFormatter = logging.Formatter("%(filename)s:%(lineno)s %(asctime)s [%(levelname)-5.5s]  %(message)s")
    handler.setFormatter(logFormatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
