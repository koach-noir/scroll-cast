"""
Typewriter Fade Template (New Architecture)
タイプライター・フェード複合エフェクト - ASS生成特化版
"""

from typing import List
from .base import BaseTemplate, SubtitleTemplate, TemplateParameter, TimingInfo
from ..boxing import FormattedText
from ..utils.debug_logger import coloring_logger


class TypewriterFadeTemplate(BaseTemplate):
    """タイプライター・フェード複合エフェクトテンプレート（ASS生成特化）"""
    
    def __init__(self):
        super().__init__()
        self.logger = coloring_logger("typewriter_fade")
    
    @property
    def template_info(self) -> SubtitleTemplate:
        return SubtitleTemplate(
            name="typewriter_fade",
            description="タイプライター表示 + 各文字フェードインエフェクト",
            parameters={
                "char_interval": TemplateParameter(
                    name="char_interval",
                    type=float,
                    default=0.15,
                    description="文字表示間隔（秒）",
                    min_value=0.05,
                    max_value=1.0
                ),
                "fade_duration": TemplateParameter(
                    name="fade_duration",
                    type=float,
                    default=0.1,
                    description="各文字のフェード時間（秒）",
                    min_value=0.05,
                    max_value=0.5
                ),
                "pause_between_lines": TemplateParameter(
                    name="pause_between_lines",
                    type=float,
                    default=1.0,
                    description="行間の間隔（秒）",
                    min_value=0.0,
                    max_value=3.0
                ),
                "pause_between_paragraphs": TemplateParameter(
                    name="pause_between_paragraphs",
                    type=float,
                    default=2.0,
                    description="段落間の間隔（秒）",
                    min_value=0.0,
                    max_value=5.0
                )
            }
        )
    
    def generate_ass_from_formatted(self, formatted_text: FormattedText, **kwargs) -> str:
        """整形済みテキストからASS字幕を生成
        
        Args:
            formatted_text: 整形済みテキスト
            **kwargs: テンプレートパラメータ
        
        Returns:
            完全なASS字幕内容
        """
        self.logger.layer_boundary("from", "boxing", f"{len(formatted_text.lines)}行受信")
        self.logger.input_data(f"行数: {len(formatted_text.lines)}", "整形済みテキスト")
        
        # パラメータ検証
        params = self.validate_parameters(**kwargs)
        self.logger.processing_step("パラメータ検証", f"char_interval={params['char_interval']}")
        
        # 解像度取得
        resolution = params.get('resolution', (1080, 1920))
        
        # ASSヘッダー生成
        ass_content = self.generate_ass_header(resolution=resolution, **{k: v for k, v in params.items() if k != 'resolution'})
        
        # 各行のDialogue行を生成
        dialogue_lines = self._generate_dialogue_lines(formatted_text, params)
        
        # 完全なASS内容を構築
        ass_content += "\n".join(dialogue_lines)
        
        self.logger.output_data(f"ASS行数: {len(dialogue_lines)}", "生成されたASS")
        self.logger.layer_boundary("to", "packing", f"{len(dialogue_lines)}行のDialogue")
        
        return ass_content
    
    def calculate_total_duration(self, formatted_text: FormattedText, **kwargs) -> float:
        """総再生時間を計算
        
        Args:
            formatted_text: 整形済みテキスト
            **kwargs: テンプレートパラメータ
        
        Returns:
            総時間（秒）
        """
        params = self.validate_parameters(**kwargs)
        
        # 実際にASSファイル生成で使用されるタイミング計算を使用
        timings = self._calculate_typewriter_timings(formatted_text, params)
        
        if not timings:
            return 0.0
        
        # 最後のタイミングの終了時間を返す
        max_end_time = max(timing.end_time for timing in timings)
        
        return max_end_time
    
    def _generate_dialogue_lines(self, formatted_text: FormattedText, params: dict) -> List[str]:
        """Dialogue行を生成
        
        Args:
            formatted_text: 整形済みテキスト
            params: バリデーション済みパラメータ
        
        Returns:
            Dialogue行のリスト
        """
        dialogue_lines = []
        
        # タイミング計算
        timings = self._calculate_typewriter_timings(formatted_text, params)
        
        # テキスト行のみを処理
        text_lines = formatted_text.get_text_lines()
        
        for i, line in enumerate(text_lines):
            if not line.strip():
                continue
            
            if i >= len(timings):
                break
            
            timing = timings[i]
            
            # タイプライター・フェード効果を作成
            typewriter_text = self._create_typewriter_fade_effect(
                line, params['char_interval'], params['fade_duration']
            )
            
            # Dialogue行を作成
            dialogue_line = self.create_dialogue_line(typewriter_text, timing)
            dialogue_lines.append(dialogue_line)
        
        # 空行の処理
        empty_timings = self._calculate_empty_line_timings(formatted_text, params)
        for empty_timing in empty_timings:
            # 空行は透明なスペースとして表示
            resolution = params.get('resolution', (1080, 1920))
            center_x = resolution[0] // 2
            center_y = resolution[1] // 2
            empty_text = f"{{\\alpha&HFF&\\pos({center_x},{center_y})}} "  # 完全透明
            empty_line = self.create_dialogue_line(empty_text, empty_timing)
            empty_line = empty_line.replace(f"Dialogue: 0,", f"Dialogue: 1,")  # 別レイヤー
            dialogue_lines.append(empty_line)
        
        return dialogue_lines
    
    def _calculate_typewriter_timings(self, formatted_text: FormattedText, params: dict) -> List[TimingInfo]:
        """タイプライター用のタイミングを計算
        
        Args:
            formatted_text: 整形済みテキスト
            params: パラメータ
        
        Returns:
            各行のタイミング情報リスト
        """
        text_lines = formatted_text.get_text_lines()
        timings = []
        current_time = 0.0
        
        char_interval = params['char_interval']
        fade_duration = params['fade_duration']
        pause_between_lines = params['pause_between_lines']
        pause_between_paragraphs = params['pause_between_paragraphs']
        
        # 複雑さによる調整
        line_complexities = formatted_text.get_timing_hint('line_complexities', [1.0] * len(text_lines))
        reading_speed_multiplier = formatted_text.get_timing_hint('reading_speed_multiplier', 1.0)
        
        for i, line in enumerate(text_lines):
            if not line.strip():
                continue
            
            # 複雑さを考慮した調整
            complexity = line_complexities[i] if i < len(line_complexities) else 1.0
            adjusted_char_interval = char_interval * complexity * reading_speed_multiplier
            
            # 行の表示時間を計算
            line_duration = self._calculate_line_duration(line, adjusted_char_interval, fade_duration)
            
            timing = TimingInfo(
                start_time=current_time,
                end_time=current_time + line_duration,
                layer=0
            )
            timings.append(timing)
            
            current_time += line_duration
            
            # 行間の間隔
            if i < len(text_lines) - 1:  # 最後の行以外
                if formatted_text.is_paragraph_break(i):
                    current_time += pause_between_paragraphs
                else:
                    current_time += pause_between_lines
        
        return timings
    
    def _calculate_empty_line_timings(self, formatted_text: FormattedText, params: dict) -> List[TimingInfo]:
        """空行のタイミングを計算"""
        empty_timings = []
        
        if not formatted_text.empty_line_positions:
            return empty_timings
        
        pause_between_paragraphs = params['pause_between_paragraphs']
        
        # 空行は段落間の間隔として扱う
        for i, empty_pos in enumerate(formatted_text.empty_line_positions):
            # 空行の表示時間を計算（適切な位置に挿入）
            start_time = empty_pos * 2.0  # 簡易計算
            timing = TimingInfo(
                start_time=start_time,
                end_time=start_time + pause_between_paragraphs,
                layer=1
            )
            empty_timings.append(timing)
        
        return empty_timings
    
    def _calculate_line_duration(self, line: str, char_interval: float, fade_duration: float) -> float:
        """行の表示時間を計算
        
        Args:
            line: 行テキスト
            char_interval: 文字間隔（秒）
            fade_duration: フェード時間（秒）
        
        Returns:
            行の総表示時間（秒）
        """
        # 制御文字を除外した実際の文字数
        clean_text = self._clean_text_for_karaoke(line)
        char_count = len(clean_text)
        
        # 総時間 = 文字数 × 間隔 + フェード時間
        return char_count * char_interval + fade_duration
    
    def _create_typewriter_fade_effect(self, text: str, char_interval: float, fade_duration: float) -> str:
        """タイプライター・フェード効果を作成
        
        Args:
            text: 表示テキスト
            char_interval: 文字間隔（秒）
            fade_duration: フェード時間（秒）
        
        Returns:
            ASS効果付きテキスト
        """
        clean_text = self._clean_text_for_karaoke(text)
        
        result_parts = []
        current_time_ms = 0.0
        
        char_interval_ms = char_interval * 1000
        fade_duration_ms = fade_duration * 1000
        
        for i, char in enumerate(clean_text):
            # 文字表示間隔（ASSのkaraokeは10ms単位）
            duration_centiseconds = int(char_interval_ms // 10)
            
            # 各文字のフェードイン開始時間と終了時間
            fade_start = int(current_time_ms)
            fade_end = int(current_time_ms + fade_duration_ms)
            
            # 文字ごとのフェードイン効果
            char_with_fade = (f"{{\\k{duration_centiseconds}"
                            f"\\alpha&HFF&\\t({fade_start},{fade_end},\\alpha&H00&)}}{char}")
            result_parts.append(char_with_fade)
            
            current_time_ms += char_interval_ms
        
        return "".join(result_parts)
    
    def _clean_text_for_karaoke(self, text: str) -> str:
        """カラオケ効果用にテキストをクリーンアップ
        
        Args:
            text: クリーンアップするテキスト
        
        Returns:
            クリーンアップされたテキスト
        """
        # 制御文字を削除し、改行をスペースに変換
        cleaned = text.replace("\\n", " ").replace("\\N", " ").replace("\n", " ")
        
        # 連続する空白を単一のスペースに変換
        import re
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        result = cleaned.strip()
        
        # 重要なテキスト変換をログに記録
        if text != result:
            self.logger.transformation(text, result, "カラオケ用テキストクリーンアップ")
        
        return result