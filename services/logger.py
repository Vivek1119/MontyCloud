import datetime
import json
import os
import logging
import structlog
from utils.config import settings
from logging.handlers import RotatingFileHandler

if not os.path.exists(settings.LOG_DIR):
    os.makedirs(settings.LOG_DIR)

log_file = os.path.join(settings.LOG_DIR, "app.log")


logging.basicConfig(
    format="%(message)s",
    level=settings.LOG_LEVEL,
    handlers=[
        RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()  # keep console logs too
    ],
)

def custom_json_renderer(_, __, event_dict):
    level = event_dict.pop("level", "INFO").upper()
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
    json_part = json.dumps(event_dict, default=str, ensure_ascii=False)
    return f"{timestamp} [{level}] {json_part}"

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(settings.LOG_LEVEL),
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        custom_json_renderer
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
