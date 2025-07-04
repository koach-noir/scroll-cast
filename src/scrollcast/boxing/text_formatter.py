"""
Text Formatter
テキスト解析・整形を担当するメインクラス
"""

import re
from typing import List, Tuple, Optional
from .display_config import DisplayConfig
from .formatted_text import FormattedText
from ..utils.debug_logger import boxing_logger


class TextFormatter:
    """テキスト解析・整形を担当するメインクラス"""
    
    def __init__(self, config: DisplayConfig):
        """
        Args:
            config: 表示設定
        """
        self.config = config
        self.logger = boxing_logger("text_formatter")
    
    def format_for_display(self, text: str) -> FormattedText:
        """テキストを表示用に整形
        
        Args:
            text: 入力テキスト
            
        Returns:
            整形済みテキスト
        """
        self.logger.input_data(text, "入力テキスト")
        
        # 1. 言語検出
        detected_language = self._detect_language(text)
        self.logger.processing_step("言語検出", f"検出言語: {detected_language}")
        
        # 2. 基本的な前処理
        normalized_text = self._normalize_text(text)
        self.logger.transformation(text, normalized_text, "テキスト正規化")
        
        # 3. 段落分割
        paragraphs = self._split_into_paragraphs(normalized_text)
        
        # 4. 各段落を処理
        all_lines = []
        line_types = []
        paragraph_breaks = []
        empty_line_positions = []
        
        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                # 空段落の場合
                if self.config.preserve_paragraphs:
                    all_lines.append("")
                    line_types.append(FormattedText.LINE_TYPE_EMPTY)
                    empty_line_positions.append(len(all_lines) - 1)
                continue
            
            # 段落内の行処理
            paragraph_lines = self._process_paragraph(paragraph, detected_language)
            
            # 段落間の区切り
            if i > 0 and all_lines and self.config.preserve_paragraphs:
                # 前の段落との間に区切りを追加
                if self.config.optimize_spacing:
                    all_lines.append("")
                    line_types.append(FormattedText.LINE_TYPE_PARAGRAPH_BREAK)
                    empty_line_positions.append(len(all_lines) - 1)
                    paragraph_breaks.append(len(all_lines) - 1)
            
            # 段落の行を追加
            for line in paragraph_lines:
                all_lines.append(line)
                line_types.append(FormattedText.LINE_TYPE_TEXT)
        
        # 5. FormattedTextオブジェクト作成
        formatted_text = FormattedText(
            original_text=text,
            lines=all_lines,
            line_types=line_types,
            paragraph_breaks=paragraph_breaks,
            empty_line_positions=empty_line_positions,
            language=detected_language
        )
        
        # 6. タイミングヒントを設定
        self._set_timing_hints(formatted_text)
        
        self.logger.output_data(f"行数: {len(formatted_text.lines)}", "整形結果")
        self.logger.layer_boundary("to", "coloring", f"{len(formatted_text.lines)}行")
        
        return formatted_text
    
    def _detect_language(self, text: str) -> str:
        """言語を検出
        
        Args:
            text: 入力テキスト
            
        Returns:
            検出された言語 ('en', 'ja', 'auto')
        """
        if self.config.language != 'auto':
            return self.config.language
        
        # 簡単な言語検出
        japanese_chars = sum(1 for char in text if self._is_japanese_char(char))
        ascii_chars = sum(1 for char in text if ord(char) < 128 and char.isalpha())
        
        total_chars = len([c for c in text if c.isalpha() or self._is_japanese_char(c)])
        
        if total_chars == 0:
            return 'en'  # デフォルト
        
        japanese_ratio = japanese_chars / total_chars
        
        if japanese_ratio > 0.1:  # 10%以上日本語文字があれば日本語
            return 'ja'
        else:
            return 'en'
    
    def _is_japanese_char(self, char: str) -> bool:
        """日本語文字かどうかを判定"""
        code = ord(char)
        return (0x3040 <= code <= 0x309F or    # ひらがな
                0x30A0 <= code <= 0x30FF or    # カタカナ
                0x4E00 <= code <= 0x9FAF)      # 漢字
    
    def _normalize_text(self, text: str) -> str:
        """テキストの正規化
        
        Args:
            text: 入力テキスト
            
        Returns:
            正規化されたテキスト
        """
        # 改行の統一
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 連続する空白の削除（行内）
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 行末の空白削除
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]
        
        return '\n'.join(lines)
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """テキストを段落に分割
        
        Args:
            text: 正規化済みテキスト
            
        Returns:
            段落のリスト
        """
        # 改行による段落分割
        paragraphs = text.split('\n\n')
        
        # 単一改行の場合も考慮
        if len(paragraphs) == 1:
            # 改行で分割して空行を探す
            lines = text.split('\n')
            current_paragraph = []
            paragraphs = []
            
            for line in lines:
                if line.strip():
                    current_paragraph.append(line)
                else:
                    if current_paragraph:
                        paragraphs.append('\n'.join(current_paragraph))
                        current_paragraph = []
                    if self.config.preserve_paragraphs:
                        paragraphs.append("")  # 空段落として保持
            
            if current_paragraph:
                paragraphs.append('\n'.join(current_paragraph))
        
        return paragraphs
    
    def _process_paragraph(self, paragraph: str, language: str) -> List[str]:
        """段落を処理して行リストに変換
        
        Args:
            paragraph: 段落テキスト
            language: 言語
            
        Returns:
            処理された行のリスト
        """
        if not paragraph.strip():
            return []
        
        # 句読点での分割
        if self.config.punctuation_break:
            sentences = self._split_by_punctuation(paragraph, language)
        else:
            sentences = [paragraph]
        
        # 各センテンスを行制限に合わせて分割
        lines = []
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            sentence_lines = self._split_sentence_to_lines(sentence)
            lines.extend(sentence_lines)
        
        return lines
    
    def _split_by_punctuation(self, text: str, language: str) -> List[str]:
        """句読点でテキストを分割
        
        Args:
            text: 分割するテキスト
            language: 言語
            
        Returns:
            分割されたセンテンスのリスト
        """
        if language == 'ja':
            # 日本語の句読点で分割
            pattern = r'([。！？]+)'
            parts = re.split(pattern, text)
        else:
            # 英語の句読点で分割
            pattern = r'([.!?]+)'
            parts = re.split(pattern, text)
        
        sentences = []
        current = ""
        
        for part in parts:
            if part.strip():
                current += part
                # 句読点で終わっている場合
                if (language == 'ja' and any(p in part for p in ['。', '！', '？']) or
                    language == 'en' and any(p in part for p in ['.', '!', '?'])):
                    sentences.append(current.strip())
                    current = ""
        
        # 残りがあれば追加
        if current.strip():
            sentences.append(current.strip())
        
        return [s for s in sentences if s.strip()]
    
    def _split_sentence_to_lines(self, sentence: str) -> List[str]:
        """センテンスを行に分割
        
        Args:
            sentence: 分割するセンテンス
            
        Returns:
            分割された行のリスト
        """
        if not sentence.strip():
            return []
        
        lines = []
        remaining = sentence.strip()
        
        while remaining:
            line, remaining = self._extract_line_with_constraints(
                remaining, 
                self.config.max_chars_per_line,
                self.config.word_wrap
            )
            
            if line:
                lines.append(line)
            else:
                # 安全な文字幅考慮フォールバック処理
                safe_line, remaining = self._safe_fallback_split(remaining, self.config.max_chars_per_line)
                if safe_line:
                    lines.append(safe_line)
                else:
                    # 最後の手段: 単一文字ずつでも進める
                    lines.append(remaining[0] if remaining else "")
                    remaining = remaining[1:] if len(remaining) > 1 else ""
        
        return lines
    
    def _safe_fallback_split(self, text: str, max_chars: int) -> Tuple[str, str]:
        """文字幅を考慮した安全な分割処理
        
        Args:
            text: 処理するテキスト
            max_chars: 最大文字数
            
        Returns:
            (抽出された行, 残りのテキスト)
        """
        if not text:
            return "", ""
            
        # 文字幅を考慮して安全に分割
        current_width = 0.0
        split_pos = 0
        
        for i, char in enumerate(text):
            char_width = self._calculate_character_width(char)
            if current_width + char_width > max_chars:
                break
            current_width += char_width
            split_pos = i + 1
        
        # 最低1文字は進める
        if split_pos == 0 and text:
            split_pos = 1
            
        line_text = text[:split_pos].strip()
        remaining_text = text[split_pos:].strip()
        
        return line_text, remaining_text
    
    def _extract_line_with_constraints(self, text: str, max_chars: int, preserve_words: bool) -> Tuple[str, str]:
        """制約内で1行分のテキストを抽出
        
        Args:
            text: 処理するテキスト
            max_chars: 最大文字数
            preserve_words: 単語境界を保持するか
            
        Returns:
            (抽出された行, 残りのテキスト)
        """
        if not text:
            return "", ""
        
        
        # 表示幅を考慮した分割
        current_width = 0.0
        current_pos = 0
        
        for i, char in enumerate(text):
            char_width = self._calculate_character_width(char)
            
            if current_width + char_width > max_chars:
                current_pos = i
                break
            
            current_width += char_width
            current_pos = i + 1
        else:
            # 文字列の最後まで処理した場合
            return text, ""
        
        # 単語境界を保持する場合の調整
        if preserve_words and current_pos > 0:
            line_candidate = text[:current_pos]
            
            if self.config.language == 'en' or self._is_mainly_english(line_candidate):
                # 英語の場合：単語境界で調整
                space_pos = line_candidate.rfind(' ')
                if space_pos > 0 and space_pos < current_pos - 1:
                    current_pos = space_pos + 1
            else:
                # 日本語の場合：適切な切れ目で調整
                current_pos = self._adjust_japanese_break_point(text, current_pos)
        
        line_text = text[:current_pos].strip()
        remaining_text = text[current_pos:].strip()
        
        return line_text, remaining_text
    
    def _calculate_character_width(self, char: str) -> float:
        """文字の表示幅を計算"""
        code = ord(char)
        
        # 全角文字判定
        if (0x3040 <= code <= 0x309F or    # ひらがな
            0x30A0 <= code <= 0x30FF or    # カタカナ
            0x4E00 <= code <= 0x9FAF or    # CJK統合漢字
            0xFF00 <= code <= 0xFFEF):     # 全角英数字・記号
            return 2.0
        
        # 韓国語文字
        if 0xAC00 <= code <= 0xD7AF:
            return 2.0
        
        # その他の全角記号類
        if (0x2000 <= code <= 0x206F or    # 一般句読点
            0x3000 <= code <= 0x303F):     # CJK記号・句読点
            return 2.0
        
        # デフォルトは半角
        return 1.0
    
    def _is_mainly_english(self, text: str) -> bool:
        """テキストが主に英語かどうかを判定"""
        if not text:
            return False
        ascii_count = sum(1 for char in text if ord(char) < 128)
        return ascii_count / len(text) > 0.7
    
    def _adjust_japanese_break_point(self, text: str, pos: int) -> int:
        """日本語テキストの改行位置を調整"""
        # 現在位置から前方に検索（最大10文字）
        search_start = max(0, pos - 10)
        for i in range(pos - 1, search_start - 1, -1):
            if i < len(text) and text[i] in self.config.japanese_break_chars:
                return i + 1
        
        return pos
    
    def _set_timing_hints(self, formatted_text: FormattedText) -> None:
        """タイミングヒントを設定
        
        Args:
            formatted_text: 整形済みテキスト
        """
        text_lines = formatted_text.get_text_lines()
        
        # 基本的なタイミング情報
        formatted_text.set_timing_hint('line_count', len(text_lines))
        formatted_text.set_timing_hint('paragraph_count', len(formatted_text.paragraph_breaks) + 1)
        formatted_text.set_timing_hint('has_empty_lines', len(formatted_text.empty_line_positions) > 0)
        
        # 言語固有のタイミング調整
        if formatted_text.language == 'ja':
            # 日本語は読みやすさを考慮してゆっくり
            formatted_text.set_timing_hint('reading_speed_multiplier', 1.2)
        else:
            # 英語は標準速度
            formatted_text.set_timing_hint('reading_speed_multiplier', 1.0)
        
        # 行ごとの複雑さ評価
        line_complexities = []
        for line in text_lines:
            complexity = self._calculate_line_complexity(line, formatted_text.language)
            line_complexities.append(complexity)
        
        formatted_text.set_timing_hint('line_complexities', line_complexities)
        formatted_text.set_timing_hint('average_complexity', 
                                      sum(line_complexities) / len(line_complexities) if line_complexities else 1.0)
    
    def _calculate_line_complexity(self, line: str, language: str) -> float:
        """行の複雑さを計算（表示時間調整用）
        
        Args:
            line: 行テキスト
            language: 言語
            
        Returns:
            複雑さ指数（1.0が標準）
        """
        if not line:
            return 1.0
        
        complexity = 1.0
        
        # 文字数による調整
        char_count = len(line)
        if char_count > self.config.max_chars_per_line * 0.8:
            complexity *= 1.2  # 長い行は少し長めに表示
        
        # 表示幅による調整
        display_width = sum(self._calculate_character_width(char) for char in line)
        if display_width > self.config.max_chars_per_line * 0.9:
            complexity *= 1.1
        
        # 句読点による調整
        if language == 'ja':
            punctuation_count = sum(1 for char in line if char in '。、！？')
        else:
            punctuation_count = sum(1 for char in line if char in '.!?,:;')
        
        if punctuation_count > 2:
            complexity *= 1.1  # 句読点が多い行は少し長めに
        
        return complexity