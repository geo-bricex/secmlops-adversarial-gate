import logging
from pathlib import Path


def configure_logging(name: str, log_dir: str | Path = "logs") -> logging.Logger:
    directory = Path(log_dir)
    directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        for handler in (logging.StreamHandler(), logging.FileHandler(directory / f"{name}.log", encoding="utf-8")):
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    return logger

