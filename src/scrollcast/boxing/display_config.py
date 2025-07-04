"""
Display Configuration
表示設定の管理
"""

from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class DisplayConfig:
    """表示設定の管理クラス"""
    
    # 必須設定
    resolution: Tuple[int, int]  # (width, height)
    font_size: int
    
    # 言語・地域設定
    language: str = 'auto'  # 'en', 'ja', 'auto'
    
    # 表示制約
    max_chars_per_line: Optional[int] = None  # Noneの場合は自動計算
    max_lines_per_screen: Optional[int] = None  # Noneの場合は自動計算
    
    # レイアウト設定
    margin_ratio: float = 0.1  # 画面端からのマージン比率
    line_spacing: float = 1.4  # 行間隔
    char_width_ratio: float = 0.6  # フォントサイズに対する文字幅比率
    
    # テキスト整形オプション
    preserve_paragraphs: bool = True  # 段落構造を保持
    punctuation_break: bool = True  # 句読点での改行
    optimize_spacing: bool = True  # 空白行の最適化
    word_wrap: bool = True  # 単語境界での折り返し
    
    # 言語固有設定
    japanese_break_chars: Tuple[str, ...] = ('。', '、', 'の', 'に', 'は', 'が', 'を', 'で', 'と')
    english_sentence_endings: Tuple[str, ...] = ('.', '!', '?')
    
    def __post_init__(self):
        """初期化後の処理"""
        # 自動計算が必要な値を設定
        if self.max_chars_per_line is None:
            self.max_chars_per_line = self._calculate_max_chars_per_line()
        
        if self.max_lines_per_screen is None:
            self.max_lines_per_screen = self._calculate_max_lines_per_screen()
    
    def _calculate_max_chars_per_line(self) -> int:
        """1行の最大文字数を計算"""
        width, height = self.resolution
        effective_width = width * (1.0 - self.margin_ratio * 2)
        avg_char_width = self.font_size * self.char_width_ratio
        max_chars = int(effective_width / avg_char_width)
        return max(max_chars, 10)  # 最小10文字保証
    
    def _calculate_max_lines_per_screen(self) -> int:
        """画面の最大行数を計算"""
        width, height = self.resolution
        effective_height = height * (1.0 - self.margin_ratio * 2)
        line_height = self.font_size * self.line_spacing
        max_lines = int(effective_height / line_height)
        return max(max_lines, 1)  # 最小1行保証
    
    @classmethod
    def create_mobile_portrait(cls, font_size: int = 64) -> 'DisplayConfig':
        """モバイル縦画面用の設定を作成"""
        return cls(
            resolution=(1080, 1920),
            font_size=font_size,
            margin_ratio=0.1,
            line_spacing=1.4
        )
    
    @classmethod
    def create_desktop(cls, font_size: int = 48) -> 'DisplayConfig':
        """デスクトップ用の設定を作成"""
        return cls(
            resolution=(1920, 1080),
            font_size=font_size,
            margin_ratio=0.15,
            line_spacing=1.5
        )
    
    @classmethod
    def create_mobile_landscape(cls, font_size: int = 48) -> 'DisplayConfig':
        """モバイル横画面用の設定を作成"""
        return cls(
            resolution=(1920, 1080),
            font_size=font_size,
            margin_ratio=0.1,
            line_spacing=1.3
        )