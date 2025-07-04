"""
Text Models
テキスト処理・構造化関連のデータモデル
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union
from enum import Enum


class TextSegmentType(Enum):
    """テキストセグメントのタイプ"""
    TEXT = "text"                    # 通常のテキスト
    EMPTY = "empty"                  # 空行
    PARAGRAPH_BREAK = "paragraph_break"   # 段落区切り
    PUNCTUATION_BREAK = "punctuation_break"  # 句読点での区切り
    TIMING_BREAK = "timing_break"    # タイミング調整用の区切り


class LanguageType(Enum):
    """サポート言語"""
    AUTO = "auto"
    JAPANESE = "ja"
    ENGLISH = "en"
    CHINESE = "zh"
    KOREAN = "ko"


@dataclass
class TextSegment:
    """テキストの最小構成単位"""
    content: str
    segment_type: TextSegmentType = TextSegmentType.TEXT
    
    # 表示特性
    display_width: float = 0.0      # 表示幅（文字数基準）
    char_count: int = 0             # 文字数
    
    # 位置情報
    line_index: int = 0             # 行インデックス
    position_in_line: int = 0       # 行内位置
    
    # タイミング情報
    complexity_factor: float = 1.0   # 複雑さ係数
    reading_time_hint: float = 0.0   # 推奨読み時間（秒）
    
    # メタデータ
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初期化後の処理"""
        if self.char_count == 0:
            self.char_count = len(self.content)
        
        if self.display_width == 0.0:
            self.display_width = self._calculate_display_width()
    
    def _calculate_display_width(self) -> float:
        """表示幅を計算"""
        width = 0.0
        for char in self.content:
            code = ord(char)
            # 全角文字判定
            if (0x3040 <= code <= 0x309F or    # ひらがな
                0x30A0 <= code <= 0x30FF or    # カタカナ
                0x4E00 <= code <= 0x9FAF or    # CJK統合漢字
                0xFF00 <= code <= 0xFFEF or    # 全角英数字・記号
                0xAC00 <= code <= 0xD7AF or    # 韓国語
                0x2000 <= code <= 0x206F or    # 一般句読点
                0x3000 <= code <= 0x303F):     # CJK記号・句読点
                width += 2.0
            else:
                width += 1.0
        return width
    
    def is_empty(self) -> bool:
        """空のセグメントかどうか"""
        return self.segment_type == TextSegmentType.EMPTY or not self.content.strip()
    
    def is_text(self) -> bool:
        """テキストセグメントかどうか"""
        return self.segment_type == TextSegmentType.TEXT
    
    def is_break(self) -> bool:
        """区切りセグメントかどうか"""
        return self.segment_type in [
            TextSegmentType.PARAGRAPH_BREAK,
            TextSegmentType.PUNCTUATION_BREAK,
            TextSegmentType.TIMING_BREAK
        ]


@dataclass
class TextContent:
    """生テキストコンテンツ"""
    original_text: str
    language: LanguageType = LanguageType.AUTO
    
    # 検出された言語情報
    detected_language: Optional[LanguageType] = None
    language_confidence: float = 0.0
    
    # 基本統計
    total_chars: int = 0
    total_display_width: float = 0.0
    
    # 構造情報
    paragraph_count: int = 0
    sentence_count: int = 0
    
    # 処理オプション
    preserve_formatting: bool = True
    normalize_whitespace: bool = True
    
    # メタデータ
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初期化後の処理"""
        if self.total_chars == 0:
            self.total_chars = len(self.original_text)
        
        if self.detected_language is None:
            self.detected_language = self._detect_language()
        
        if self.paragraph_count == 0:
            self.paragraph_count = self._count_paragraphs()
    
    def _detect_language(self) -> LanguageType:
        """言語を自動検出"""
        if self.language != LanguageType.AUTO:
            return self.language
        
        text = self.original_text
        if not text:
            return LanguageType.ENGLISH
        
        # 各言語の文字数をカウント
        japanese_chars = sum(1 for char in text if self._is_japanese_char(char))
        chinese_chars = sum(1 for char in text if self._is_chinese_char(char))
        korean_chars = sum(1 for char in text if self._is_korean_char(char))
        ascii_chars = sum(1 for char in text if ord(char) < 128 and char.isalpha())
        
        total_chars = len([c for c in text if c.isalpha() or self._is_cjk_char(c)])
        
        if total_chars == 0:
            return LanguageType.ENGLISH
        
        # 最も多い言語を選択
        japanese_ratio = japanese_chars / total_chars
        chinese_ratio = chinese_chars / total_chars
        korean_ratio = korean_chars / total_chars
        
        if japanese_ratio > 0.1:
            self.language_confidence = japanese_ratio
            return LanguageType.JAPANESE
        elif chinese_ratio > 0.1:
            self.language_confidence = chinese_ratio
            return LanguageType.CHINESE
        elif korean_ratio > 0.1:
            self.language_confidence = korean_ratio
            return LanguageType.KOREAN
        else:
            self.language_confidence = ascii_chars / total_chars if total_chars > 0 else 0.0
            return LanguageType.ENGLISH
    
    def _is_japanese_char(self, char: str) -> bool:
        """日本語文字かどうかを判定"""
        code = ord(char)
        return (0x3040 <= code <= 0x309F or    # ひらがな
                0x30A0 <= code <= 0x30FF)      # カタカナ
    
    def _is_chinese_char(self, char: str) -> bool:
        """中国語文字かどうかを判定"""
        code = ord(char)
        return 0x4E00 <= code <= 0x9FAF        # CJK統合漢字
    
    def _is_korean_char(self, char: str) -> bool:
        """韓国語文字かどうかを判定"""
        code = ord(char)
        return 0xAC00 <= code <= 0xD7AF        # ハングル音節
    
    def _is_cjk_char(self, char: str) -> bool:
        """CJK文字かどうかを判定"""
        return (self._is_japanese_char(char) or 
                self._is_chinese_char(char) or 
                self._is_korean_char(char))
    
    def _count_paragraphs(self) -> int:
        """段落数をカウント"""
        paragraphs = self.original_text.split('\n\n')
        return len([p for p in paragraphs if p.strip()])
    
    def get_language_info(self) -> Dict[str, Any]:
        """言語情報を取得"""
        return {
            'original_language': self.language.value,
            'detected_language': self.detected_language.value if self.detected_language else None,
            'confidence': self.language_confidence,
            'is_auto_detected': self.language == LanguageType.AUTO
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            'total_chars': self.total_chars,
            'total_display_width': self.total_display_width,
            'paragraph_count': self.paragraph_count,
            'sentence_count': self.sentence_count,
            'language_info': self.get_language_info(),
            'preserve_formatting': self.preserve_formatting,
            'normalize_whitespace': self.normalize_whitespace
        }


@dataclass
class FormattedText:
    """整形済みテキストの統一データモデル"""
    
    # 元データ参照
    source_content: TextContent
    
    # 整形結果
    segments: List[TextSegment] = field(default_factory=list)
    lines: List[str] = field(default_factory=list)
    
    # 構造情報
    line_types: List[TextSegmentType] = field(default_factory=list)
    paragraph_breaks: List[int] = field(default_factory=list)
    empty_line_positions: List[int] = field(default_factory=list)
    
    # 表示設定参照
    display_config_used: Optional[Any] = None  # DisplayConfigの参照
    
    # 計算済み統計
    total_lines: int = 0
    text_lines_count: int = 0
    total_display_width: float = 0.0
    
    # タイミング・複雑さ情報
    timing_hints: Dict[str, Any] = field(default_factory=dict)
    line_complexities: List[float] = field(default_factory=list)
    
    # 互換性のための定数
    LINE_TYPE_TEXT = TextSegmentType.TEXT
    LINE_TYPE_EMPTY = TextSegmentType.EMPTY
    LINE_TYPE_PARAGRAPH_BREAK = TextSegmentType.PARAGRAPH_BREAK
    LINE_TYPE_PUNCTUATION_BREAK = TextSegmentType.PUNCTUATION_BREAK
    
    def __post_init__(self):
        """初期化後の処理"""
        if not self.lines and self.segments:
            self._rebuild_lines_from_segments()
        
        if not self.line_types and self.lines:
            self._rebuild_line_types()
        
        self._update_statistics()
    
    def _rebuild_lines_from_segments(self):
        """セグメントから行リストを再構築"""
        lines = []
        current_line = ""
        current_line_index = 0
        
        for segment in self.segments:
            if segment.line_index != current_line_index:
                # 新しい行
                if current_line or segment.is_empty():
                    lines.append(current_line)
                current_line = segment.content
                current_line_index = segment.line_index
            else:
                # 同じ行内のセグメント
                current_line += segment.content
        
        # 最後の行を追加
        if current_line or not lines:
            lines.append(current_line)
        
        self.lines = lines
    
    def _rebuild_line_types(self):
        """行タイプリストを再構築"""
        line_types = []
        for i, line in enumerate(self.lines):
            if not line.strip():
                line_types.append(TextSegmentType.EMPTY)
                if i not in self.empty_line_positions:
                    self.empty_line_positions.append(i)
            else:
                line_types.append(TextSegmentType.TEXT)
        self.line_types = line_types
    
    def _update_statistics(self):
        """統計情報を更新"""
        self.total_lines = len(self.lines)
        self.text_lines_count = len(self.get_text_lines())
        self.total_display_width = sum(
            segment.display_width for segment in self.segments
        )
    
    # 既存インターフェース互換性メソッド
    def get_text_lines(self) -> List[str]:
        """テキスト行のみを取得（空行・区切り行を除く）"""
        return [
            line for i, line in enumerate(self.lines)
            if i < len(self.line_types) and self.line_types[i] == TextSegmentType.TEXT
        ]
    
    def get_line_with_type(self, line_index: int) -> Tuple[str, str]:
        """指定インデックスの行とタイプを取得"""
        if 0 <= line_index < len(self.lines):
            line = self.lines[line_index]
            line_type = (self.line_types[line_index] 
                        if line_index < len(self.line_types) 
                        else TextSegmentType.TEXT)
            return line, line_type.value
        return "", TextSegmentType.EMPTY.value
    
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
            if (i < len(self.line_types) and 
                self.line_types[i] == TextSegmentType.TEXT):
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
    
    def add_line(self, line: str, line_type: Union[TextSegmentType, str] = None) -> None:
        """行を追加"""
        self.lines.append(line)
        
        # 型変換
        if isinstance(line_type, str):
            try:
                line_type = TextSegmentType(line_type)
            except ValueError:
                line_type = TextSegmentType.TEXT
        elif line_type is None:
            line_type = TextSegmentType.TEXT
        
        self.line_types.append(line_type)
        
        # 空行の場合は位置を記録
        if not line.strip():
            self.empty_line_positions.append(len(self.lines) - 1)
        
        # セグメントも追加
        segment = TextSegment(
            content=line,
            segment_type=line_type,
            line_index=len(self.lines) - 1
        )
        self.segments.append(segment)
    
    def insert_paragraph_break(self, after_line_index: int) -> None:
        """段落区切りを挿入"""
        if after_line_index not in self.paragraph_breaks:
            self.paragraph_breaks.append(after_line_index)
            self.paragraph_breaks.sort()
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        text_lines = self.get_text_lines()
        return {
            'total_lines': self.total_lines,
            'text_lines': self.text_lines_count,
            'empty_lines': len(self.empty_line_positions),
            'paragraph_breaks': len(self.paragraph_breaks),
            'total_chars': sum(len(line) for line in self.lines),
            'total_display_width': self.total_display_width,
            'average_line_length': (
                sum(len(line) for line in text_lines) / len(text_lines)
                if text_lines else 0
            ),
            'language': self.source_content.detected_language.value if self.source_content.detected_language else 'auto',
            'segment_count': len(self.segments),
            'line_complexities': self.line_complexities
        }
    
    # 新しい拡張メソッド
    def get_segments_by_type(self, segment_type: TextSegmentType) -> List[TextSegment]:
        """指定タイプのセグメントを取得"""
        return [s for s in self.segments if s.segment_type == segment_type]
    
    def get_segments_by_line(self, line_index: int) -> List[TextSegment]:
        """指定行のセグメントを取得"""
        return [s for s in self.segments if s.line_index == line_index]
    
    def calculate_total_reading_time(self, base_time_per_char: float = 0.1) -> float:
        """総読み時間を計算"""
        total_time = 0.0
        for segment in self.segments:
            if segment.is_text():
                if segment.reading_time_hint > 0:
                    total_time += segment.reading_time_hint
                else:
                    total_time += segment.char_count * base_time_per_char * segment.complexity_factor
        return total_time
    
    def optimize_for_timing(self, target_time_per_line: float = 2.0) -> None:
        """タイミング最適化用の処理"""
        text_segments = self.get_segments_by_type(TextSegmentType.TEXT)
        
        for segment in text_segments:
            # 複雑さに基づく読み時間の設定
            estimated_time = segment.char_count * 0.1 * segment.complexity_factor
            segment.reading_time_hint = min(estimated_time, target_time_per_line)
        
        # 行ごとの複雑さを更新
        self.line_complexities = []
        for i in range(self.total_lines):
            line_segments = self.get_segments_by_line(i)
            avg_complexity = (
                sum(s.complexity_factor for s in line_segments) / len(line_segments)
                if line_segments else 1.0
            )
            self.line_complexities.append(avg_complexity)
    
    # 互換性のための従来インターフェース
    @property
    def original_text(self) -> str:
        """元テキスト（互換性）"""
        return self.source_content.original_text
    
    @property
    def language(self) -> str:
        """言語（互換性）"""
        return self.source_content.detected_language.value if self.source_content.detected_language else 'auto'
    
    @property
    def total_chars(self) -> int:
        """総文字数（互換性）"""
        return sum(len(line) for line in self.lines)
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"FormattedText({self.total_lines} lines, {self.total_chars} chars, lang={self.language})"
    
    def __repr__(self) -> str:
        """デバッグ用文字列表現"""
        return (f"FormattedText(lines={self.total_lines}, "
                f"chars={self.total_chars}, "
                f"segments={len(self.segments)}, "
                f"paragraphs={len(self.paragraph_breaks)}, "
                f"empty_lines={len(self.empty_line_positions)}, "
                f"language='{self.language}')")


# ファクトリー関数
def create_text_content(text: str, language: str = "auto", **kwargs) -> TextContent:
    """TextContentを作成"""
    lang_enum = LanguageType.AUTO
    if language in LanguageType.__members__.values():
        lang_enum = LanguageType(language)
    elif language.upper() in LanguageType.__members__:
        lang_enum = LanguageType.__members__[language.upper()]
    
    return TextContent(
        original_text=text,
        language=lang_enum,
        **kwargs
    )


def create_formatted_text_from_legacy(original_text: str, lines: List[str], 
                                     line_types: List[str] = None,
                                     paragraph_breaks: List[int] = None,
                                     empty_line_positions: List[int] = None,
                                     language: str = 'auto',
                                     timing_hints: Dict[str, Any] = None) -> FormattedText:
    """既存のFormattedTextインターフェースから新しいモデルを作成"""
    
    # TextContentを作成
    source_content = create_text_content(original_text, language)
    
    # セグメントを作成
    segments = []
    for i, line in enumerate(lines):
        line_type_str = line_types[i] if line_types and i < len(line_types) else "text"
        try:
            segment_type = TextSegmentType(line_type_str)
        except ValueError:
            segment_type = TextSegmentType.TEXT
        
        segment = TextSegment(
            content=line,
            segment_type=segment_type,
            line_index=i
        )
        segments.append(segment)
    
    # FormattedTextを作成
    formatted_text = FormattedText(
        source_content=source_content,
        segments=segments,
        lines=lines,
        line_types=[TextSegmentType(lt) if isinstance(lt, str) else lt 
                   for lt in (line_types or [TextSegmentType.TEXT] * len(lines))],
        paragraph_breaks=paragraph_breaks or [],
        empty_line_positions=empty_line_positions or [],
        timing_hints=timing_hints or {}
    )
    
    return formatted_text