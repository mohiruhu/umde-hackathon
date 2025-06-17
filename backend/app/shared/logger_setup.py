import os
import logging
import sys
from logging.handlers import RotatingFileHandler

USE_CLOUDWATCH = os.getenv("USE_CLOUDWATCH_LOGS", "false").lower() == "true"

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # Prevent duplicate handlers on reload

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    # Local file logging
    os.makedirs("logs", exist_ok=True)
    file_handler = RotatingFileHandler("logs/cms_parser.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)



    # Optional CloudWatch
    if USE_CLOUDWATCH:
        try:
            import watchtower
            cloudwatch_handler = watchtower.CloudWatchLogHandler(
                log_group=os.getenv("CLOUDWATCH_LOG_GROUP", "UMDELogs"),
                stream_name=os.getenv("CLOUDWATCH_LOG_STREAM", "cms-parser"),
                create_log_group=True,
                region_name=os.getenv("AWS_REGION", "us-east-1")
            )
            cloudwatch_handler.setFormatter(formatter)
            logger.addHandler(cloudwatch_handler)
            logger.info("✅ CloudWatch logging enabled")
        except Exception as e:
            logger.warning(f"⚠️ CloudWatch logging failed: {e}")

    return logger

def get_logger(name: str = "umde") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
