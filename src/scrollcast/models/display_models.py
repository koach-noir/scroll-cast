"""
Display Models
表示・レイアウト関連のデータモデル
"""

from dataclasses import dataclass
from typing import Tuple, Optional
from enum import Enum


class ResolutionPreset(Enum):
    """解像度プリセット"""
    MOBILE_PORTRAIT = "1080x1920"    # TikTok/Instagram Stories
    MOBILE_LANDSCAPE = "1920x1080"   # YouTube横画面
    DESKTOP_HD = "1920x1080"         # デスクトップ標準
    DESKTOP_4K = "3840x2160"         # 4K表示
    SQUARE = "1080x1080"             # Instagram投稿


@dataclass
class Resolution:
    """解像度設定"""
    width: int
    height: int
    
    @classmethod
    def from_string(cls, resolution_str: str) -> 'Resolution':
        """文字列から解像度を作成 (例: "1080x1920")"""
        width, height = map(int, resolution_str.split('x'))
        return cls(width, height)
    
    @classmethod
    def from_preset(cls, preset: ResolutionPreset) -> 'Resolution':
        """プリセットから解像度を作成"""
        return cls.from_string(preset.value)
    
    def to_tuple(self) -> Tuple[int, int]:
        """タプル形式で返す（既存コード互換性）"""
        return (self.width, self.height)
    
    def __str__(self) -> str:
        return f"{self.width}x{self.height}"
    
    @property
    def aspect_ratio(self) -> float:
        """アスペクト比を計算"""
        return self.width / self.height
    
    @property
    def is_portrait(self) -> bool:
        """縦画面かどうか"""
        return self.height > self.width


@dataclass
class FontConfig:
    """フォント設定"""
    size: int
    family: str = "Arial"
    bold: bool = True
    italic: bool = False
    
    # ASS形式用の色設定
    primary_color: str = "&H00FFFFFF"    # 白
    secondary_color: str = "&H000000FF"  # 青
    outline_color: str = "&H00000000"    # 黒アウトライン
    shadow_color: str = "&H80000000"     # 半透明黒影
    
    # 描画設定
    outline_width: int = 3
    shadow_offset: int = 0
    
    def to_ass_style_params(self) -> dict:
        """ASSスタイル用のパラメータを生成"""
        return {
            'fontname': self.family,
            'fontsize': self.size,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'outline_color': self.outline_color,
            'back_color': self.shadow_color,
            'bold': 1 if self.bold else 0,
            'italic': 1 if self.italic else 0,
            'outline': self.outline_width,
            'shadow': self.shadow_offset,
        }


@dataclass
class DisplayConfig:
    """表示設定の統一管理クラス"""
    
    # 基本設定
    resolution: Resolution
    font: FontConfig
    
    # 言語・地域設定
    language: str = 'auto'  # 'en', 'ja', 'auto'
    
    # 表示制約（None=自動計算）
    max_chars_per_line: Optional[int] = None
    max_lines_per_screen: Optional[int] = None
    
    # レイアウト設定
    margin_ratio: float = 0.1         # 画面端からのマージン比率
    line_spacing: float = 1.4         # 行間隔
    char_width_ratio: float = 0.6     # フォントサイズに対する文字幅比率
    
    # テキスト整形オプション
    preserve_paragraphs: bool = True  # 段落構造を保持
    punctuation_break: bool = True    # 句読点での改行
    optimize_spacing: bool = True     # 空白行の最適化
    word_wrap: bool = True           # 単語境界での折り返し
    
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
        width = self.resolution.width
        effective_width = width * (1.0 - self.margin_ratio * 2)
        avg_char_width = self.font.size * self.char_width_ratio
        max_chars = int(effective_width / avg_char_width)
        return max(max_chars, 10)  # 最小10文字保証
    
    def _calculate_max_lines_per_screen(self) -> int:
        """画面の最大行数を計算"""
        height = self.resolution.height
        effective_height = height * (1.0 - self.margin_ratio * 2)
        line_height = self.font.size * self.line_spacing
        max_lines = int(effective_height / line_height)
        return max(max_lines, 1)  # 最小1行保証
    
    # 既存コード互換性のためのプロパティ
    @property
    def resolution_tuple(self) -> Tuple[int, int]:
        """既存コード互換性: resolution as tuple"""
        return self.resolution.to_tuple()
    
    @property
    def font_size(self) -> int:
        """既存コード互換性: font_size直接アクセス"""
        return self.font.size
    
    # ファクトリメソッド
    @classmethod
    def create_mobile_portrait(cls, font_size: int = 64) -> 'DisplayConfig':
        """モバイル縦画面用の設定を作成"""
        return cls(
            resolution=Resolution.from_preset(ResolutionPreset.MOBILE_PORTRAIT),
            font=FontConfig(size=font_size),
            margin_ratio=0.1,
            line_spacing=1.4
        )
    
    @classmethod
    def create_desktop(cls, font_size: int = 48) -> 'DisplayConfig':
        """デスクトップ用の設定を作成"""
        return cls(
            resolution=Resolution.from_preset(ResolutionPreset.DESKTOP_HD),
            font=FontConfig(size=font_size),
            margin_ratio=0.15,
            line_spacing=1.5
        )
    
    @classmethod
    def create_mobile_landscape(cls, font_size: int = 48) -> 'DisplayConfig':
        """モバイル横画面用の設定を作成"""
        return cls(
            resolution=Resolution.from_preset(ResolutionPreset.MOBILE_LANDSCAPE),
            font=FontConfig(size=font_size),
            margin_ratio=0.1,
            line_spacing=1.3
        )
    
    @classmethod
    def from_legacy_params(cls, resolution: Tuple[int, int], font_size: int = 64) -> 'DisplayConfig':
        """既存のパラメータ形式から作成（互換性維持）"""
        return cls(
            resolution=Resolution(width=resolution[0], height=resolution[1]),
            font=FontConfig(size=font_size)
        )