"""
로깅 유틸리티.
"""
import logging
import sys
from typing import Optional

from src.config.settings import LOG_LEVEL


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    로거를 설정하고 반환합니다.

    Args:
        name: 로거 이름
        level: 로깅 레벨 (기본값: settings.LOG_LEVEL)

    Returns:
        설정된 로거 객체
    """
    logger = logging.getLogger(name)

    if level is None:
        level = LOG_LEVEL

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # 이미 핸들러가 설정되어 있으면 추가하지 않음
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# 기본 로거 생성
logger = setup_logger("flutter_agent")
