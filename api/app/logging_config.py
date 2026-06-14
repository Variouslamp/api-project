import logging
import sys
from logging.handlers import RotatingFileHandler

import structlog
import structlog.processors
import structlog.stdlib


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors: list[structlog.types.Processor] = [
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[
                *shared_processors,
                structlog.dev.ConsoleRenderer(),
            ],
        )
    )

    file_handler = RotatingFileHandler(
        "logs/transactions.jsonl",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    file_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[
                *shared_processors,
                structlog.processors.JSONRenderer(),
            ],
        )
    )

    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.INFO)

    structlog.stdlib.recreate_defaults(log_level=logging.INFO)
