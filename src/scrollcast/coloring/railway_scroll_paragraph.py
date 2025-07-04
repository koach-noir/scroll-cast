"""
Railway Scroll Paragraph Template (New Architecture)
段落単位で一括表示する鉄道方向幕風スクロールエフェクト - ASS生成特化版
"""

from typing import List, Dict, Any
from .base import BaseTemplate, SubtitleTemplate, TemplateParameter, TimingInfo
from ..boxing import FormattedText


class RailwayScrollParagraphTemplate(BaseTemplate):
    """段落単位で一括表示する鉄道方向幕風スクロールエフェクトテンプレート（ASS生成特化）"""
    
    @property
    def template_info(self) -> SubtitleTemplate:
        return SubtitleTemplate(
            name="railway_scroll_paragraph",
            description="段落単位で一括表示する鉄道方向幕風1行フロー（下→中央→上 フェードイン・アウト）",
            parameters={
                "fade_in_duration": TemplateParameter(
                    name="fade_in_duration",
                    type=float,
                    default=0.8,
                    description="フェードイン時間（秒）",
                    min_value=0.2,
                    max_value=2.0
                ),
                "pause_duration": TemplateParameter(
                    name="pause_duration",
                    type=float,
                    default=2.0,
                    description="中央での一時停止時間（秒）",
                    min_value=0.5,
                    max_value=5.0
                ),
                "fade_out_duration": TemplateParameter(
                    name="fade_out_duration",
                    type=float,
                    default=0.8,
                    description="フェードアウト時間（秒）",
                    min_value=0.2,
                    max_value=2.0
                ),
                "paragraph_interval": TemplateParameter(
                    name="paragraph_interval",
                    type=float,
                    default=0.5,
                    description="段落間の間隔時間（秒）",
                    min_value=0.0,
                    max_value=2.0
                ),
                "empty_line_pause": TemplateParameter(
                    name="empty_line_pause",
                    type=float,
                    default=1.0,
                    description="空行での一時停止時間（秒）",
                    min_value=0.0,
                    max_value=3.0
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
        # パラメータ検証
        params = self.validate_parameters(**kwargs)
        
        # 解像度取得
        resolution = params.get('resolution', (1080, 1920))
        
        # ASSヘッダー生成
        ass_content = self.generate_ass_header(resolution=resolution, **{k: v for k, v in params.items() if k != 'resolution'})
        
        # 各段落のDialogue行を生成
        dialogue_lines = self._generate_dialogue_lines(formatted_text, params)
        
        # 完全なASS内容を構築
        ass_content += "\n".join(dialogue_lines)
        
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
        
        paragraph_groups = self._create_paragraph_groups(formatted_text)
        if not paragraph_groups:
            return 0.0
        
        line_start_delay = params.get('line_start_delay', 0.0)
        
        if line_start_delay == 0.0:
            # デフォルト動作：同時開始の場合
            fade_in = params['fade_in_duration']
            pause = params['pause_duration']
            fade_out = params['fade_out_duration']
            paragraph_interval = params['paragraph_interval']
            
            # 1段落あたりの時間
            single_paragraph_time = fade_in + pause + fade_out
            
            # 総時間計算（段落間隔を含む）
            total_time = len(paragraph_groups) * single_paragraph_time + (len(paragraph_groups) - 1) * paragraph_interval
            
        else:
            # 行遅延がある場合：実際のパラグラフタイミング計算を使用
            paragraph_timings = self._calculate_paragraph_timings(formatted_text, params)
            
            if paragraph_timings:
                # 各段落内の全行の完了時間を計算
                max_end_time = 0.0
                
                for group_index, group in enumerate(paragraph_groups):
                    if group_index < len(paragraph_timings):
                        base_timing = paragraph_timings[group_index]
                        
                        # この段落の各行の完了時間をチェック
                        for line_index in range(len(group)):
                            line_start_offset = self._calculate_line_start_offset(
                                line_index, group, line_start_delay,
                                params['fade_in_duration'], params['pause_duration'], params['fade_out_duration']
                            )
                            
                            # 行の個別タイミングを計算
                            line_timing = self._calculate_line_individual_timings(
                                base_timing, line_start_offset, params
                            )
                            
                            # この行の完了時間（fade_out終了時間）
                            line_end_time = line_timing['fade_out'].end_time
                            max_end_time = max(max_end_time, line_end_time)
                
                total_time = max_end_time
            else:
                total_time = 0.0
        
        # 空行の時間を追加（実際の計算ベース）
        if formatted_text.empty_line_positions:
            empty_timings = self._calculate_empty_line_timings(formatted_text, params)
            if empty_timings:
                max_empty_end = max(timing.end_time for timing in empty_timings)
                total_time = max(total_time, max_empty_end)
        
        return total_time
    
    def _create_paragraph_groups(self, formatted_text: FormattedText) -> List[List[str]]:
        """段落をグループ化
        
        Args:
            formatted_text: 整形済みテキスト
        
        Returns:
            段落グループのリスト（各グループは行のリスト）
        """
        groups = []
        current_group = []
        
        for i, line in enumerate(formatted_text.lines):
            # 段落区切りを検出
            if i in formatted_text.paragraph_breaks and current_group:
                groups.append(current_group)
                current_group = []
            
            # テキスト行のみをグループに追加
            if (i < len(formatted_text.line_types) and 
                formatted_text.line_types[i] == FormattedText.LINE_TYPE_TEXT and
                line.strip()):
                current_group.append(line)
        
        # 最後のグループを追加
        if current_group:
            groups.append(current_group)
        
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
        
        # 位置設定
        resolution = params.get('resolution', (1080, 1920))
        center_x = resolution[0] // 2
        center_y = resolution[1] // 2
        start_y = center_y + 200  # 下からの開始位置
        end_y = center_y - 200    # 上への終了位置
        line_spacing = params['line_spacing']
        
        # 段落グループを作成
        paragraph_groups = self._create_paragraph_groups(formatted_text)
        
        # タイミング計算
        paragraph_timings = self._calculate_paragraph_timings(formatted_text, params)
        
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
            
            # 各行のエフェクトを生成
            for line_index, line in enumerate(group):
                line_y = line_positions[line_index]
                start_line_y = start_y + line_index * line_spacing
                end_line_y = end_y + line_index * line_spacing
                
                # 行の開始遅延を計算
                line_start_offset = self._calculate_line_start_offset(
                    line_index, group, params['line_start_delay'], 
                    params['fade_in_duration'], params['pause_duration'], params['fade_out_duration']
                )
                
                # 各行の個別タイミングを計算
                line_timing_set = self._calculate_line_individual_timings(
                    timing_set, line_start_offset, params
                )
                
                # Phase 1: フェードイン（下→中央）
                fade_in_text = self._create_fade_in_effect(
                    line, center_x, start_line_y, line_y, 
                    params['fade_in_duration'] * 1000, 0.0  # オフセットはタイミングで調整
                )
                fade_in_line = self.create_dialogue_line(fade_in_text, line_timing_set['fade_in'])
                dialogue_lines.append(fade_in_line)
                
                # Phase 2: 中央での一時停止
                pause_text = self._create_pause_effect(line, center_x, line_y, 0.0)
                pause_line = self.create_dialogue_line(pause_text, line_timing_set['pause'])
                pause_line = pause_line.replace(f"Dialogue: 0,", f"Dialogue: 1,")  # レイヤー変更
                dialogue_lines.append(pause_line)
                
                # Phase 3: フェードアウト（中央→上）
                fade_out_text = self._create_fade_out_effect(
                    line, center_x, line_y, end_line_y, 
                    params['fade_out_duration'] * 1000, 0.0  # オフセットはタイミングで調整
                )
                fade_out_line = self.create_dialogue_line(fade_out_text, line_timing_set['fade_out'])
                fade_out_line = fade_out_line.replace(f"Dialogue: 0,", f"Dialogue: 2,")  # レイヤー変更
                dialogue_lines.append(fade_out_line)
        
        # 空行の処理
        empty_timings = self._calculate_empty_line_timings(formatted_text, params)
        for empty_timing in empty_timings:
            # 空行は透明なテキストとして表示
            empty_text = f"{{\\alpha&HFF&\\pos({center_x},{center_y})}} "  # 完全透明
            empty_line = self.create_dialogue_line(empty_text, empty_timing)
            empty_line = empty_line.replace(f"Dialogue: 0,", f"Dialogue: 3,")  # 別レイヤー
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
        
        # 基本時間
        fade_in_duration = params['fade_in_duration']
        pause_duration = params['pause_duration']
        fade_out_duration = params['fade_out_duration']
        paragraph_interval = params['paragraph_interval']
        
        # 複雑さによる調整
        reading_speed_multiplier = formatted_text.get_timing_hint('reading_speed_multiplier', 1.0)
        
        for group_index, group in enumerate(paragraph_groups):
            # 段落の複雑さを計算（行数と文字数を考慮）
            paragraph_complexity = self._calculate_paragraph_complexity(group, formatted_text)
            adjusted_pause = pause_duration * paragraph_complexity * reading_speed_multiplier
            
            # Phase 1: フェードイン
            fade_in_timing = TimingInfo(
                start_time=current_time,
                end_time=current_time + fade_in_duration,
                layer=0
            )
            current_time += fade_in_duration
            
            # Phase 2: 一時停止
            pause_timing = TimingInfo(
                start_time=current_time,
                end_time=current_time + adjusted_pause,
                layer=1
            )
            current_time += adjusted_pause
            
            # Phase 3: フェードアウト
            fade_out_timing = TimingInfo(
                start_time=current_time,
                end_time=current_time + fade_out_duration,
                layer=2
            )
            current_time += fade_out_duration
            
            # 段落間隔
            if group_index < len(paragraph_groups) - 1:
                current_time += paragraph_interval
            
            timings.append({
                'fade_in': fade_in_timing,
                'pause': pause_timing,
                'fade_out': fade_out_timing
            })
        
        return timings
    
    def _calculate_paragraph_complexity(self, paragraph_group: List[str], formatted_text: FormattedText) -> float:
        """段落の複雑さを計算
        
        Args:
            paragraph_group: 段落内の行リスト
            formatted_text: 整形済みテキスト
        
        Returns:
            複雑さ指数（1.0が標準）
        """
        if not paragraph_group:
            return 1.0
        
        complexity = 1.0
        
        # 行数による調整
        line_count = len(paragraph_group)
        if line_count > 1:
            complexity *= (1.0 + (line_count - 1) * 0.2)  # 行数が多いほど複雑
        
        # 文字数による調整
        total_chars = sum(len(line) for line in paragraph_group)
        if total_chars > 50:
            complexity *= 1.2
        elif total_chars > 100:
            complexity *= 1.4
        
        # 句読点による調整
        punctuation_count = sum(line.count(p) for line in paragraph_group for p in '。、！？.!?,:;')
        if punctuation_count > 3:
            complexity *= 1.1
        
        return complexity
    
    def _calculate_empty_line_timings(self, formatted_text: FormattedText, params: dict) -> List[TimingInfo]:
        """空行のタイミングを計算"""
        empty_timings = []
        
        if not formatted_text.empty_line_positions:
            return empty_timings
        
        empty_pause = params['empty_line_pause']
        
        # 段落タイミングを基に空行の適切な時間を計算
        paragraph_timings = self._calculate_paragraph_timings(formatted_text, params)
        
        for i, empty_pos in enumerate(formatted_text.empty_line_positions):
            # 段落インデックスに基づく適切な時間計算
            if i < len(paragraph_timings):
                # 対応する段落の終了時間を基準にする
                base_timing = paragraph_timings[i]['fade_out']
                start_time = base_timing.end_time
            else:
                # 段落数を超える場合は最後の段落の終了後
                if paragraph_timings:
                    last_timing = paragraph_timings[-1]['fade_out']
                    start_time = last_timing.end_time + (i - len(paragraph_timings) + 1) * empty_pause
                else:
                    start_time = empty_pos * 2.0  # フォールバック
            
            timing = TimingInfo(
                start_time=start_time,
                end_time=start_time + empty_pause,
                layer=3
            )
            empty_timings.append(timing)
        
        return empty_timings
    
    def _calculate_line_start_offset(self, line_index: int, paragraph_group: List[str],
                                   line_start_delay: float, fade_in_duration: float,
                                   pause_duration: float, fade_out_duration: float) -> float:
        """行の開始遅延時間を計算
        
        Args:
            line_index: 段落内の行インデックス（0から開始）
            paragraph_group: 段落内の行リスト
            line_start_delay: 遅延設定値（ms）
            fade_in_duration: フェードイン時間（秒）
            pause_duration: 一時停止時間（秒）
            fade_out_duration: フェードアウト時間（秒）
        
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
            # 負値：上の行のフェードイン完了後に開始（期待される順次実行）
            accumulated_offset = 0.0
            
            # railway_scrollでは順次実行 = 前行のフェードイン完了後に次行開始
            single_fade_in_duration = fade_in_duration * 1000  # ms
            
            # 前の行のフェードイン完了時間を累積計算
            accumulated_offset = line_index * single_fade_in_duration
            
            return accumulated_offset
    
    def _calculate_line_individual_timings(self, base_timing_set: Dict[str, TimingInfo], 
                                         line_start_offset_ms: float, 
                                         params: dict) -> Dict[str, TimingInfo]:
        """各行の個別タイミングを計算
        
        Args:
            base_timing_set: 段落のベースタイミング
            line_start_offset_ms: 行の開始遅延（ミリ秒）
            params: パラメータ
        
        Returns:
            行の個別タイミング辞書
        """
        offset_seconds = line_start_offset_ms / 1000.0
        
        # 各フェーズの時間
        fade_in_duration = params['fade_in_duration']
        pause_duration = params['pause_duration'] 
        fade_out_duration = params['fade_out_duration']
        
        # ベースタイミングの開始時間にオフセットを加算
        base_start = base_timing_set['fade_in'].start_time
        line_start_time = base_start + offset_seconds
        
        # 各フェーズのタイミングを計算
        fade_in_timing = TimingInfo(
            start_time=line_start_time,
            end_time=line_start_time + fade_in_duration,
            layer=0
        )
        
        pause_timing = TimingInfo(
            start_time=line_start_time + fade_in_duration,
            end_time=line_start_time + fade_in_duration + pause_duration,
            layer=1
        )
        
        fade_out_timing = TimingInfo(
            start_time=line_start_time + fade_in_duration + pause_duration,
            end_time=line_start_time + fade_in_duration + pause_duration + fade_out_duration,
            layer=2
        )
        
        return {
            'fade_in': fade_in_timing,
            'pause': pause_timing,
            'fade_out': fade_out_timing
        }
    
    def _create_fade_in_effect(self, text: str, center_x: int, start_y: int, 
                              center_y: int, duration_ms: float, start_offset_ms: float = 0.0) -> str:
        """フェードインエフェクトを作成
        
        Args:
            text: 表示テキスト
            center_x: 中央X座標
            start_y: 開始Y座標
            center_y: 中央Y座標
            duration_ms: 時間（ミリ秒）
            start_offset_ms: 開始時間オフセット（ミリ秒）（現在は使用されない、タイミングで制御）
        
        Returns:
            ASS効果付きテキスト
        """
        duration_ms = int(duration_ms)
        
        # タイミングで制御するため、エフェクト内のオフセットは0から開始
        return (f"{{\\move({center_x},{start_y},{center_x},{center_y})"
                f"\\alpha&HFF&\\t(0,{duration_ms},\\alpha&H00&)}}{text}")
    
    def _create_pause_effect(self, text: str, center_x: int, center_y: int, start_offset_ms: float = 0.0) -> str:
        """一時停止エフェクトを作成
        
        Args:
            text: 表示テキスト
            center_x: 中央X座標
            center_y: 中央Y座標
            start_offset_ms: 開始時間オフセット（ミリ秒）（一時停止では使用されないが一貫性のため）
        
        Returns:
            ASS効果付きテキスト
        """
        # 一時停止は位置固定なので、オフセットは使用しない
        return f"{{\\pos({center_x},{center_y})\\alpha&H00&}}{text}"
    
    def _create_fade_out_effect(self, text: str, center_x: int, center_y: int, 
                               end_y: int, duration_ms: float, start_offset_ms: float = 0.0) -> str:
        """フェードアウトエフェクトを作成
        
        Args:
            text: 表示テキスト
            center_x: 中央X座標
            center_y: 中央Y座標
            end_y: 終了Y座標
            duration_ms: 時間（ミリ秒）
            start_offset_ms: 開始時間オフセット（ミリ秒）（現在は使用されない、タイミングで制御）
        
        Returns:
            ASS効果付きテキスト
        """
        duration_ms = int(duration_ms)
        
        # タイミングで制御するため、エフェクト内のオフセットは0から開始
        return (f"{{\\move({center_x},{center_y},{center_x},{end_y})"
                f"\\alpha&H00&\\t(0,{duration_ms},\\alpha&HFF&)}}{text}")