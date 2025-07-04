"""
Boxing Layer - Text Structure & Formatting
テキスト構造化・改行処理層
"""

from .display_config import DisplayConfig
from .formatted_text import FormattedText
from .text_formatter import TextFormatter
from . import text_utils

__all__ = ['DisplayConfig', 'FormattedText', 'TextFormatter', 'text_utils']