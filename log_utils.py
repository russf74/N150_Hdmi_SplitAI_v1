import logging

def setup_logging(log_file: str):
    """
    Set up logging to the specified file with timestamps.
    """
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def log(message: str):
    """
    Log a message to the configured log file and console.
    """
    logging.info(message)
    print(message)