import logging

def logging_crawler():
    logging.basicConfig(
    filename="applicationMain.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s  [%(filename)s:%(funcName)s]",
    level=logging.INFO,
)
    error_logger = logging.getLogger("error_logger")
    error_logger.setLevel(logging.ERROR)