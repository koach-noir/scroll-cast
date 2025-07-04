"""
Text Utilities
テキスト処理関連のユーティリティ
"""

import os
import re
from typing import List, Optional, Tuple


def extract_text_from_markdown(file_path: str, fallback_text: str = "Default demo text.") -> str:
    """Markdownファイルからテキストブロックを抽出
    
    Args:
        file_path: Markdownファイルのパス
        fallback_text: ファイル読み込み失敗時のフォールバックテキスト
    
    Returns:
        抽出されたテキスト
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # ```text ブロックを抽出
        text_start = content.find('```text\n') + 8
        text_end = content.find('\n```', text_start)
        
        if text_start > 7 and text_end > text_start:
            text = content[text_start:text_end].strip()
            return text
        else:
            print(f"警告: テキストブロックが見つかりません: {file_path}")
            return fallback_text
        
    except Exception as e:
        print(f"テキストファイル読み込みエラー: {e}")
        return fallback_text


def split_text_to_sentences(text: str, max_sentences: Optional[int] = None) -> List[str]:
    """テキストを文に分割
    
    Args:
        text: 分割するテキスト
        max_sentences: 最大文数（Noneの場合は制限なし）
    
    Returns:
        文のリスト
    """
    sentences = text.split('. ')
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if max_sentences:
        sentences = sentences[:max_sentences]
    
    return sentences


def split_text_to_segments(text: str, max_segments: int = 6, 
                          max_words_per_segment: int = 8) -> List[str]:
    """テキストをセグメントに分割（鉄道方向幕風など）
    
    Args:
        text: 分割するテキスト
        max_segments: 最大セグメント数
        max_words_per_segment: セグメントあたりの最大単語数
    
    Returns:
        セグメントのリスト
    """
    sentences = split_text_to_sentences(text, max_segments)
    
    segments = []
    for sentence in sentences:
        words = sentence.split()
        if len(words) > max_words_per_segment:
            # 長い文は分割
            mid = len(words) // 2
            segments.append(' '.join(words[:mid]))
            if len(segments) < max_segments:
                segments.append(' '.join(words[mid:]))
        else:
            segments.append(sentence)
        
        if len(segments) >= max_segments:
            break
    
    return segments[:max_segments]


def clean_text_for_karaoke(text: str) -> str:
    """カラオケ効果用にテキストをクリーンアップ
    
    Args:
        text: クリーンアップするテキスト
    
    Returns:
        クリーンアップされたテキスト
    """
    return text.replace("\\n", "").replace("\\N", "").replace("\n", " ")


def truncate_text_for_display(text: str, max_length: int = 50) -> str:
    """表示用にテキストを切り詰め
    
    Args:
        text: 切り詰めるテキスト
        max_length: 最大長
        
    Returns:
        切り詰められたテキスト
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def calculate_character_width(char: str) -> float:
    """文字の表示幅を計算（全角=2.0、半角=1.0）
    
    Args:
        char: 計算する文字
        
    Returns:
        文字幅（全角=2.0、半角=1.0）
    """
    # 全角文字判定（Unicode範囲による）
    code = ord(char)
    
    # 日本語文字範囲
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


def calculate_text_display_length(text: str) -> float:
    """テキストの表示幅を計算
    
    Args:
        text: 計算するテキスト
        
    Returns:
        表示幅（文字幅の合計）
    """
    return sum(calculate_character_width(char) for char in text)


def calculate_max_chars_per_line(resolution: Tuple[int, int], font_size: int, 
                                margin_ratio: float = 0.1, char_width_ratio: float = 0.6) -> int:
    """画面解像度とフォントサイズから1行の最大文字数を計算
    
    Args:
        resolution: 画面解像度 (width, height)
        font_size: フォントサイズ（ピクセル）
        margin_ratio: 左右マージン比率（画面幅に対する）
        char_width_ratio: 文字幅比率（フォントサイズに対する平均文字幅）
        
    Returns:
        1行の最大文字数（半角文字基準）
    """
    width, height = resolution
    
    # 有効表示幅（マージンを除く）
    effective_width = width * (1.0 - margin_ratio * 2)
    
    # 平均文字幅（フォントサイズ × 文字幅比率）
    avg_char_width = font_size * char_width_ratio
    
    # 最大文字数計算（半角文字基準）
    max_chars = int(effective_width / avg_char_width)
    
    # 最小値の保証（短すぎる場合の対策）
    return max(max_chars, 10)


def calculate_max_lines_per_screen(resolution: Tuple[int, int], font_size: int,
                                  line_spacing: float = 1.4, margin_ratio: float = 0.1) -> int:
    """画面解像度とフォントサイズから最大行数を計算
    
    Args:
        resolution: 画面解像度 (width, height)
        font_size: フォントサイズ（ピクセル）
        line_spacing: 行間隔比率
        margin_ratio: 上下マージン比率
        
    Returns:
        最大行数
    """
    width, height = resolution
    
    # 有効表示高（マージンを除く）
    effective_height = height * (1.0 - margin_ratio * 2)
    
    # 1行の高さ（フォントサイズ × 行間隔）
    line_height = font_size * line_spacing
    
    # 最大行数計算
    max_lines = int(effective_height / line_height)
    
    # 最小値の保証
    return max(max_lines, 1)


def split_text_with_constraints(text: str, max_chars_per_line: int, max_lines: int,
                               preserve_words: bool = True) -> List[str]:
    """文字数・行数制限でテキストを分割
    
    Args:
        text: 分割するテキスト
        max_chars_per_line: 1行の最大文字数（半角基準）
        max_lines: 最大行数
        preserve_words: 単語境界を保持するか
        
    Returns:
        分割されたテキスト行のリスト
    """
    if not text.strip():
        return []
    
    lines = []
    remaining_text = text.strip()
    
    # 最大行数まで処理
    for line_num in range(max_lines):
        if not remaining_text:
            break
            
        # 1行分のテキストを抽出
        line_text, remaining_text = _extract_line_with_constraints(
            remaining_text, max_chars_per_line, preserve_words
        )
        
        if line_text:
            lines.append(line_text)
    
    return lines


def _extract_line_with_constraints(text: str, max_chars: int, preserve_words: bool) -> Tuple[str, str]:
    """制約内で1行分のテキストを抽出
    
    Args:
        text: 処理するテキスト
        max_chars: 最大文字数（半角基準）
        preserve_words: 単語境界を保持するか
        
    Returns:
        (抽出された行, 残りのテキスト)
    """
    if not text:
        return "", ""
    
    # 現在の表示幅を追跡
    current_width = 0.0
    current_pos = 0
    
    # 文字ごとに幅を計算
    for i, char in enumerate(text):
        char_width = calculate_character_width(char)
        
        # 制限を超える場合
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
        # 日本語と英語で異なる処理
        line_candidate = text[:current_pos]
        
        # 英語の場合：単語境界で調整
        if _is_english_text(line_candidate):
            # 単語の途中で切れている場合、前の単語境界まで戻る
            space_pos = line_candidate.rfind(' ')
            if space_pos > 0 and space_pos < current_pos - 1:
                current_pos = space_pos + 1
        
        # 日本語の場合：句読点や助詞で調整
        else:
            current_pos = _adjust_japanese_break_point(text, current_pos)
    
    line_text = text[:current_pos].strip()
    remaining_text = text[current_pos:].strip()
    
    return line_text, remaining_text


def _is_english_text(text: str) -> bool:
    """テキストが主に英語かどうかを判定
    
    Args:
        text: 判定するテキスト
        
    Returns:
        英語テキストかどうか
    """
    # ASCII文字の割合で判定
    ascii_count = sum(1 for char in text if ord(char) < 128)
    return ascii_count / len(text) > 0.7 if text else False


def _adjust_japanese_break_point(text: str, pos: int) -> int:
    """日本語テキストの改行位置を調整
    
    Args:
        text: テキスト
        pos: 現在の位置
        
    Returns:
        調整された位置
    """
    # 句読点や助詞の後で改行するよう調整
    adjustment_chars = ['。', '、', 'の', 'に', 'は', 'が', 'を', 'で', 'と']
    
    # 現在位置から前方に検索（最大10文字）
    search_start = max(0, pos - 10)
    for i in range(pos - 1, search_start - 1, -1):
        if i < len(text) and text[i] in adjustment_chars:
            return i + 1
    
    return pos


def smart_text_split_for_template(text: str, resolution: Tuple[int, int], font_size: int,
                                 template_type: str = "single") -> List[str]:
    """テンプレート用のスマートテキスト分割
    
    Args:
        text: 分割するテキスト
        resolution: 画面解像度
        font_size: フォントサイズ
        template_type: テンプレートタイプ ("single", "sentences", "segments")
        
    Returns:
        分割されたテキストのリスト
    """
    # 画面制約を計算
    max_chars_per_line = calculate_max_chars_per_line(resolution, font_size)
    max_lines = calculate_max_lines_per_screen(resolution, font_size)
    
    if template_type == "single":
        # テキスト全体をそのまま返す（制限なし）
        # 長すぎるテキストは事前にBaseTemplateでチェック済み
        return text
    
    elif template_type == "sentences":
        # センテンス単位で分割（制限緩和）
        sentences = split_text_to_sentences(text, None)  # 制限なし
        result = []
        
        for sentence in sentences:
            lines = split_text_with_constraints(sentence, max_chars_per_line, 2)
            if lines:
                result.append(' '.join(lines))
        
        return result  # 制限なし
    
    elif template_type == "segments":
        # セグメント用に分割（制限緩和）
        segments = split_text_to_segments(text, 1000, 1000)  # 実質制限なし
        result = []
        
        for segment in segments:
            # セグメントをそのまま使用
            result.append(segment)
        
        return result  # 制限なし
    
    else:
        # デフォルト処理
        lines = split_text_with_constraints(text, max_chars_per_line, max_lines)
        return lines if lines else [text]