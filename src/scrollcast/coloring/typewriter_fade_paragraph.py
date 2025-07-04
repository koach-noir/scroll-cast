"""
Typewriter Fade Paragraph Template (New Architecture)
段落単位で一括表示するタイプライター・フェード複合エフェクト - ASS生成特化版
"""

from typing import List, Dict
from .base import BaseTemplate, SubtitleTemplate, TemplateParameter, TimingInfo
from ..boxing import FormattedText
from ..utils.debug_logger import coloring_logger


class TypewriterFadeParagraphTemplate(BaseTemplate):
    """段落単位で一括表示するタイプライター・フェード複合エフェクトテンプレート（ASS生成特化）"""
    
    def __init__(self):
        super().__init__()
        self.logger = coloring_logger("typewriter_fade_paragraph")
    
    @property
    def template_info(self) -> SubtitleTemplate:
        return SubtitleTemplate(
            name="typewriter_fade_paragraph",
            description="段落単位で一括表示するタイプライター表示 + 各文字フェードインエフェクト",
            parameters={
                "char_interval": TemplateParameter(
                    name="char_interval",
                    type=float,
                    default=0.1,
                    description="文字表示間隔（秒）",
                    min_value=0.05,
                    max_value=1.0
                ),
                "fade_duration": TemplateParameter(
                    name="fade_duration",
                    type=float,
                    default=0.08,
                    description="各文字のフェード時間（秒）",
                    min_value=0.05,
                    max_value=0.5
                ),
                "pause_between_paragraphs": TemplateParameter(
                    name="pause_between_paragraphs",
                    type=float,
                    default=2.0,
                    description="段落間の間隔（秒）",
                    min_value=0.0,
                    max_value=5.0
                ),
                "reading_time_multiplier": TemplateParameter(
                    name="reading_time_multiplier",
                    type=float,
                    default=1.5,
                    description="段落表示後の読書時間倍率",
                    min_value=0.5,
                    max_value=5.0
                ),
                "line_spacing": TemplateParameter(
                    name="line_spacing",
                    type=int,
                    default=40,
                    description="段落内の行間スペース（ピクセル）",
                    min_value=20,
                    max_value=100
                ),
                "line_start_delay": TemplateParameter(
                    name="line_start_delay",
                    type=float,
                    default=0.0,
                    description="段落内行の開始遅延（ms）。正値=上行開始後の遅延、負値=上行完了後開始",
                    min_value=-5000.0,
                    max_value=5000.0
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
        
        # 各段落のDialogue行を生成
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
        timings = self._calculate_paragraph_timings(formatted_text, params)
        
        if not timings:
            return 0.0
        
        # 最後のタイミングの終了時間を返す
        max_end_time = max(timing['display'].end_time for timing in timings)
        
        return max_end_time
    
    def _create_paragraph_groups(self, formatted_text: FormattedText) -> List[List[str]]:
        """段落をグループ化
        
        Args:
            formatted_text: 整形済みテキスト
        
        Returns:
            段落グループのリスト（各グループは行のリスト）
        """
        self.logger.processing_step("段落グループ化開始", f"全{len(formatted_text.lines)}行")
        self.logger.input_data(f"段落区切り位置: {formatted_text.paragraph_breaks}", "段落情報")
        
        groups = []
        current_group = []
        
        for i, line in enumerate(formatted_text.lines):
            # 段落区切りを検出
            if i in formatted_text.paragraph_breaks and current_group:
                self.logger.processing_step(f"段落区切り検出", f"{i}行目, グループ{len(current_group)}行保存")
                groups.append(current_group)
                current_group = []
            
            # テキスト行のみをグループに追加
            if (i < len(formatted_text.line_types) and 
                formatted_text.line_types[i] == FormattedText.LINE_TYPE_TEXT and
                line.strip()):
                current_group.append(line)
                self.logger.processing_step(f"行{i}をグループに追加", f"'{line[:30]}...'")
        
        # 最後のグループを追加
        if current_group:
            self.logger.processing_step("最終グループ追加", f"{len(current_group)}行")
            groups.append(current_group)
        
        self.logger.processing_step("段落グループ化完了", f"{len(groups)}個のグループ作成")
        return groups
    
    def _generate_dialogue_lines(self, formatted_text: FormattedText, params: dict) -> List[str]:
        """Dialogue行を生成
        
        Args:
            formatted_text: 整形済みテキスト
            params: バリデーション済みパラメータ
        
        Returns:
            Dialogue行のリスト
        """
        dialogue_lines = []
        
        # 段落グループを作成
        paragraph_groups = self._create_paragraph_groups(formatted_text)
        
        # タイミング計算
        paragraph_timings = self._calculate_paragraph_timings(formatted_text, params)
        
        # 位置設定
        resolution = params.get('resolution', (1080, 1920))
        center_x = resolution[0] // 2
        center_y = resolution[1] // 2
        line_spacing = params['line_spacing']
        
        for group_index, group in enumerate(paragraph_groups):
            if group_index >= len(paragraph_timings):
                break
            
            timing_set = paragraph_timings[group_index]
            
            # 段落内の各行の位置計算
            total_lines = len(group)
            if total_lines == 1:
                line_positions = [center_y]
            else:
                # 複数行の場合は中央を基準に上下に配置
                total_height = (total_lines - 1) * line_spacing
                start_pos = center_y - total_height // 2
                line_positions = [start_pos + i * line_spacing for i in range(total_lines)]
            
            # 段落全体のタイプライター効果を生成
            for line_index, line in enumerate(group):
                line_y = line_positions[line_index]
                
                # 行の開始遅延を計算
                line_start_offset = self._calculate_line_start_offset(
                    line_index, group, params['line_start_delay'], 
                    params['char_interval'], params['fade_duration']
                )
                
                # タイプライター・フェード効果を作成（開始オフセット付き）
                typewriter_text = self._create_typewriter_fade_effect(
                    line, center_x, line_y, params['char_interval'], 
                    params['fade_duration'], line_start_offset
                )
                
                # Dialogue行を作成
                dialogue_line = self.create_dialogue_line(typewriter_text, timing_set['display'])
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
    
    def _calculate_paragraph_timings(self, formatted_text: FormattedText, params: dict) -> List[Dict[str, TimingInfo]]:
        """段落単位のタイミングを計算
        
        Args:
            formatted_text: 整形済みテキスト
            params: パラメータ
        
        Returns:
            各段落のタイミング辞書のリスト
        """
        paragraph_groups = self._create_paragraph_groups(formatted_text)
        timings = []
        current_time = 0.0
        
        char_interval = params['char_interval']
        fade_duration = params['fade_duration']
        pause_between_paragraphs = params['pause_between_paragraphs']
        reading_time_multiplier = params['reading_time_multiplier']
        
        # 複雑さによる調整
        reading_speed_multiplier = formatted_text.get_timing_hint('reading_speed_multiplier', 1.0)
        
        for group_index, group in enumerate(paragraph_groups):
            # 段落のタイプライター表示時間を計算
            paragraph_duration = self._calculate_paragraph_duration(
                group, char_interval, fade_duration, reading_time_multiplier, 
                params.get('line_start_delay', 0.0)
            )
            
            # 複雑さを考慮した調整
            adjusted_duration = paragraph_duration * reading_speed_multiplier
            
            # 段落の表示タイミング
            display_timing = TimingInfo(
                start_time=current_time,
                end_time=current_time + adjusted_duration,
                layer=0
            )
            
            timings.append({
                'display': display_timing
            })
            
            current_time += adjusted_duration
            
            # 段落間の間隔
            if group_index < len(paragraph_groups) - 1:
                current_time += pause_between_paragraphs
        
        return timings
    
    def _calculate_paragraph_duration(self, paragraph_group: List[str], 
                                    char_interval: float, fade_duration: float,
                                    reading_time_multiplier: float, 
                                    line_start_delay: float = 0.0) -> float:
        """段落の表示時間を計算
        
        Args:
            paragraph_group: 段落内の行リスト
            char_interval: 文字間隔（秒）
            fade_duration: フェード時間（秒）
            reading_time_multiplier: 読書時間倍率
            line_start_delay: 行間開始遅延（ms）
        
        Returns:
            段落の総表示時間（秒）
        """
        if not paragraph_group:
            return 0.0
        
        if line_start_delay == 0.0:
            # デフォルト動作：同時開始の場合
            max_line_duration = 0.0
            total_chars = 0
            
            for line in paragraph_group:
                clean_text = self._clean_text_for_karaoke(line)
                char_count = len(clean_text)
                total_chars += char_count
                
                # 行のタイプライター時間
                line_duration = char_count * char_interval + fade_duration
                max_line_duration = max(max_line_duration, line_duration)
            
            # 段落全体の表示時間 = タイプライター時間 + 読書時間
            reading_time = (total_chars / 200) * reading_time_multiplier
            total_duration = max_line_duration + reading_time
            
        else:
            # 行遅延がある場合：最後の行の完了時間を計算
            total_chars = 0
            last_line_end_time = 0.0
            
            for line_index, line in enumerate(paragraph_group):
                clean_text = self._clean_text_for_karaoke(line)
                char_count = len(clean_text)
                total_chars += char_count
                
                # この行の開始オフセット
                line_start_offset = self._calculate_line_start_offset(
                    line_index, paragraph_group, line_start_delay, 
                    char_interval, fade_duration
                )
                
                # 行のタイプライター時間
                line_duration = char_count * char_interval + fade_duration
                
                # この行の終了時間（秒）
                line_end_time = (line_start_offset / 1000.0) + line_duration
                last_line_end_time = max(last_line_end_time, line_end_time)
            
            # 読書時間を追加
            reading_time = (total_chars / 200) * reading_time_multiplier
            total_duration = last_line_end_time + reading_time
        
        return total_duration
    
    def _calculate_empty_line_timings(self, formatted_text: FormattedText, params: dict) -> List[TimingInfo]:
        """空行のタイミングを計算"""
        empty_timings = []
        
        if not formatted_text.empty_line_positions:
            return empty_timings
        
        pause_between_paragraphs = params['pause_between_paragraphs']
        
        # 段落タイミングを基に空行の適切な時間を計算
        paragraph_timings = self._calculate_paragraph_timings(formatted_text, params)
        
        for i, empty_pos in enumerate(formatted_text.empty_line_positions):
            # 段落インデックスに基づく適切な時間計算
            if i < len(paragraph_timings):
                # 対応する段落の終了時間を基準にする
                base_timing = paragraph_timings[i]['display']
                start_time = base_timing.end_time
            else:
                # 段落数を超える場合は最後の段落の終了後
                if paragraph_timings:
                    last_timing = paragraph_timings[-1]['display']
                    start_time = last_timing.end_time + (i - len(paragraph_timings) + 1) * pause_between_paragraphs
                else:
                    start_time = empty_pos * 2.0  # フォールバック
            
            timing = TimingInfo(
                start_time=start_time,
                end_time=start_time + pause_between_paragraphs,
                layer=1
            )
            empty_timings.append(timing)
        
        return empty_timings
    
    def _calculate_line_start_offset(self, line_index: int, paragraph_group: List[str],
                                   line_start_delay: float, char_interval: float, 
                                   fade_duration: float) -> float:
        """行の開始遅延時間を計算
        
        Args:
            line_index: 段落内の行インデックス（0から開始）
            paragraph_group: 段落内の行リスト
            line_start_delay: 遅延設定値（ms）
            char_interval: 文字間隔（秒）
            fade_duration: フェード時間（秒）
        
        Returns:
            開始時間オフセット（ミリ秒）
        """
        if line_index == 0:
            # 最初の行は常に遅延なし
            return 0.0
        
        if line_start_delay == 0.0:
            # デフォルト動作：同時開始
            return 0.0
        
        if line_start_delay > 0:
            # 正値：上の行開始から指定ms後に開始
            return line_index * line_start_delay
        
        else:
            # 負値：上の行のタイプライター効果完了後に開始
            accumulated_offset = 0.0
            
            for prev_line_idx in range(line_index):
                prev_line = paragraph_group[prev_line_idx]
                prev_clean_text = self._clean_text_for_karaoke(prev_line)
                
                # 前の行のタイプライター完了時間を計算
                prev_line_duration = len(prev_clean_text) * char_interval + fade_duration
                prev_line_duration_ms = prev_line_duration * 1000
                
                if prev_line_idx == 0:
                    # 最初の行
                    accumulated_offset = prev_line_duration_ms
                else:
                    # それ以降の行：前行完了後にさらに遅延
                    accumulated_offset += prev_line_duration_ms
            
            return accumulated_offset
    
    def _create_typewriter_fade_effect(self, text: str, center_x: int, center_y: int,
                                     char_interval: float, fade_duration: float, 
                                     start_offset_ms: float = 0.0) -> str:
        """タイプライター・フェード効果を作成
        
        Args:
            text: 表示テキスト
            center_x: 中央X座標
            center_y: 中央Y座標
            char_interval: 文字間隔（秒）
            fade_duration: フェード時間（秒）
            start_offset_ms: 開始時間オフセット（ミリ秒）
        
        Returns:
            ASS効果付きテキスト
        """
        clean_text = self._clean_text_for_karaoke(text)
        
        result_parts = []
        current_time_ms = start_offset_ms  # 開始オフセットを適用
        
        char_interval_ms = char_interval * 1000
        fade_duration_ms = fade_duration * 1000
        
        # 位置指定を追加
        position_tag = f"{{\\pos({center_x},{center_y})}}"
        result_parts.append(position_tag)
        
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