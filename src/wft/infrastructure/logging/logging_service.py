import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data, default=str)


class LoggingService:
    def __init__(self, log_dir: Optional[Path] = None, level: str = "INFO") -> None:
        self._logger = logging.getLogger("wft")
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self._logger.handlers.clear()

        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(JsonFormatter())
        self._logger.addHandler(console)

        if log_dir:
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(
                log_dir / f"wft_{datetime.now(timezone.utc).strftime('%Y%m%d')}.jsonl",
                encoding="utf-8",
            )
            file_handler.setFormatter(JsonFormatter())
            self._logger.addHandler(file_handler)

        self._redact_keys = {"password", "secret", "key", "token", "authorization"}

    def get_logger(self) -> logging.Logger:
        return self._logger

    def _redact(self, msg: str) -> str:
        for key in self._redact_keys:
            msg = msg.replace(key, "***")
        return msg

    def info(self, msg: str, *args: object) -> None:
        self._logger.info(self._redact(msg), *args)

    def warning(self, msg: str, *args: object) -> None:
        self._logger.warning(self._redact(msg), *args)

    def error(self, msg: str, *args: object) -> None:
        self._logger.error(self._redact(msg), *args)

    def critical(self, msg: str, *args: object) -> None:
        self._logger.critical(self._redact(msg), *args)

    def debug(self, msg: str, *args: object) -> None:
        self._logger.debug(self._redact(msg), *args)
