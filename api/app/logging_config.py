import logging
import os
from logging.handlers import RotatingFileHandler


class TransactionFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        trace_id = getattr(record, "trace_id", "N/A")
        req = getattr(record, "request_data", {})
        resp_status = getattr(record, "response_status", None)
        resp_data = getattr(record, "response_data", {})

        lines = [
            f"━━━ POST /transactions/validate ━━━ [trace: {trace_id}]",
            "  • Request:",
        ]
        for key, val in req.items():
            lines.append(f"    - {key}: {val}")

        if resp_status == 200:
            lines.append(f"  • Response: {resp_status} OK")
        elif resp_status is not None:
            lines.append(f"  • Response: {resp_status}")
        else:
            lines.append("  • Response: N/A")

        for key, val in resp_data.items():
            if isinstance(val, list):
                for v in val:
                    lines.append(f"    - {key}: {v}")
            else:
                lines.append(f"    - {key}: {val}")

        return "\n".join(lines) + "\n"


def configure_logging() -> None:
    os.makedirs("logs", exist_ok=True)

    handler = RotatingFileHandler(
        "logs/transactions.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    handler.setFormatter(TransactionFormatter())

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
