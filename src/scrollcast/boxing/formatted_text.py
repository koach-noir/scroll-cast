"""
Formatted Text
整形済みテキストの構造化データ
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class FormattedText:
    """整形済みテキストの構造化データクラス"""
    
    # 基本データ
    original_text: str  # 元のテキスト
    lines: List[str]  # 整形後の行リスト
    
    # 構造情報
    line_types: List[str] = field(default_factory=list)  # 各行のタイプ
    paragraph_breaks: List[int] = field(default_factory=list)  # 段落区切りの行番号
    empty_line_positions: List[int] = field(default_factory=list)  # 空行の位置
    
    # メタデータ
    language: str = 'auto'  # 検出された言語
    total_chars: int = 0  # 総文字数
    total_display_width: float = 0.0  # 総表示幅
    
    # テンプレート用ヒント
    timing_hints: Dict[str, Any] = field(default_factory=dict)
    
    # 行タイプの定数
    LINE_TYPE_TEXT = 'text'
    LINE_TYPE_EMPTY = 'empty'
    LINE_TYPE_PARAGRAPH_BREAK = 'paragraph_break'
    LINE_TYPE_PUNCTUATION_BREAK = 'punctuation_break'
    
    def __post_init__(self):
        """初期化後の処理"""
        if not self.line_types:
            self.line_types = [self.LINE_TYPE_TEXT] * len(self.lines)
        
        # 総文字数計算
        self.total_chars = sum(len(line) for line in self.lines)
        
        # 表示幅計算（必要に応じて）
        if self.total_display_width == 0.0:
            self.total_display_width = self._calculate_display_width()
    
    def _calculate_display_width(self) -> float:
        """総表示幅を計算"""
        from .text_utils import calculate_text_display_length
        return sum(calculate_text_display_length(line) for line in self.lines)
    
    def get_text_lines(self) -> List[str]:
        """テキスト行のみを取得（空行・区切り行を除く）"""
        return [
            line for i, line in enumerate(self.lines)
            if i < len(self.line_types) and self.line_types[i] == self.LINE_TYPE_TEXT
        ]
    
    def get_line_with_type(self, line_index: int) -> tuple[str, str]:
        """指定インデックスの行とタイプを取得"""
        if 0 <= line_index < len(self.lines):
            line = self.lines[line_index]
            line_type = (self.line_types[line_index] 
                        if line_index < len(self.line_types) 
                        else self.LINE_TYPE_TEXT)
            return line, line_type
        return "", self.LINE_TYPE_EMPTY
    
    def is_empty_line(self, line_index: int) -> bool:
        """指定インデックスが空行かどうか"""
        return line_index in self.empty_line_positions
    
    def is_paragraph_break(self, line_index: int) -> bool:
        """指定インデックスが段落区切りかどうか"""
        return line_index in self.paragraph_breaks
    
    def get_paragraph_groups(self) -> List[List[str]]:
        """段落ごとにグループ化した行リストを取得"""
        if not self.paragraph_breaks:
            return [self.get_text_lines()]
        
        paragraphs = []
        current_paragraph = []
        
        for i, line in enumerate(self.lines):
            if self.line_types[i] == self.LINE_TYPE_TEXT:
                current_paragraph.append(line)
            elif i in self.paragraph_breaks and current_paragraph:
                paragraphs.append(current_paragraph)
                current_paragraph = []
        
        # 最後の段落を追加
        if current_paragraph:
            paragraphs.append(current_paragraph)
        
        return paragraphs
    
    def get_timing_hint(self, key: str, default: Any = None) -> Any:
        """タイミングヒントを取得"""
        return self.timing_hints.get(key, default)
    
    def set_timing_hint(self, key: str, value: Any) -> None:
        """タイミングヒントを設定"""
        self.timing_hints[key] = value
    
    def add_line(self, line: str, line_type: str = None) -> None:
        """行を追加"""
        self.lines.append(line)
        self.line_types.append(line_type or self.LINE_TYPE_TEXT)
        
        # 空行の場合は位置を記録
        if not line.strip():
            self.empty_line_positions.append(len(self.lines) - 1)
    
    def insert_paragraph_break(self, after_line_index: int) -> None:
        """段落区切りを挿入"""
        if after_line_index not in self.paragraph_breaks:
            self.paragraph_breaks.append(after_line_index)
            self.paragraph_breaks.sort()
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        text_lines = self.get_text_lines()
        return {
            'total_lines': len(self.lines),
            'text_lines': len(text_lines),
            'empty_lines': len(self.empty_line_positions),
            'paragraph_breaks': len(self.paragraph_breaks),
            'total_chars': self.total_chars,
            'total_display_width': self.total_display_width,
            'average_line_length': (
                sum(len(line) for line in text_lines) / len(text_lines)
                if text_lines else 0
            ),
            'language': self.language
        }
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"FormattedText({len(self.lines)} lines, {self.total_chars} chars, lang={self.language})"
    
    def __repr__(self) -> str:
        """デバッグ用文字列表現"""
        return (f"FormattedText(lines={len(self.lines)}, "
                f"chars={self.total_chars}, "
                f"paragraphs={len(self.paragraph_breaks)}, "
                f"empty_lines={len(self.empty_line_positions)}, "
                f"language='{self.language}')")