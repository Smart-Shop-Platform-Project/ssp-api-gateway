import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    logger = logging.getLogger("ssp-api-gateway")
    logger.setLevel(logging.INFO)

    # Standard JSON handler for production (Easier for CloudWatch/ELK to parse)
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Quiet noisy internal libraries so your logs stay clean
    _LIBRARY_LEVELS = {
        "httpx": "WARNING",
        "botocore": "WARNING",
        "uvicorn": "INFO",
        "sqlalchemy.engine": "WARNING"
    }
    for lib_name, level in _LIBRARY_LEVELS.items():
        logging.getLogger(lib_name).setLevel(level)

    return logger

# Initialize once
logger = setup_logging()
