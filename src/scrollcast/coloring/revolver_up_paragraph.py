"""
Revolver Up Paragraph Template (New Architecture)
段落単位で一括表示する回転式上昇エフェクト - ASS生成特化版
"""

from typing import List, Dict, Any
from .base import BaseTemplate, SubtitleTemplate, TemplateParameter, TimingInfo
from ..boxing import FormattedText


class RevolverUpParagraphTemplate(BaseTemplate):
    """段落単位で一括表示する回転式上昇エフェクトテンプレート（ASS生成特化）"""
    
    @property
    def template_info(self) -> SubtitleTemplate:
        return SubtitleTemplate(
            name="revolver_up_paragraph",
            description="段落単位ハイブリッド上昇エフェクト（鉄道幕風×エンドロール流れ）",
            parameters={
                "fade_in_duration": TemplateParameter(
                    name="fade_in_duration",
                    type=float,
                    default=0.6,
                    description="フェードイン時間（秒）",
                    min_value=0.2,
                    max_value=2.0
                ),
                "fade_out_duration": TemplateParameter(
                    name="fade_out_duration",
                    type=float,
                    default=0.6,
                    description="フェードアウト時間（秒）",
                    min_value=0.2,
                    max_value=2.0
                ),
                "display_duration": TemplateParameter(
                    name="display_duration",
                    type=float,
                    default=1.0,
                    description="中央表示時間（秒）",
                    min_value=0.3,
                    max_value=3.0
                ),
                "paragraph_interval": TemplateParameter(
                    name="paragraph_interval",
                    type=float,
                    default=0.8,
                    description="段落間の間隔時間（秒）",
                    min_value=0.0,
                    max_value=2.0
                ),
                "rise_distance": TemplateParameter(
                    name="rise_distance",
                    type=float,
                    default=150.0,
                    description="上昇距離（ピクセル）",
                    min_value=100.0,
                    max_value=400.0
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
                ),
                "line_interval": TemplateParameter(
                    name="line_interval",
                    type=float,
                    default=0.3,
                    description="行間間隔時間（秒）",
                    min_value=0.1,
                    max_value=1.0
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
            rotate_duration = params['rotate_duration']
            display_duration = params['display_duration']
            fade_duration = params['fade_duration']
            paragraph_interval = params['paragraph_interval']
            
            # 1段落あたりの時間
            single_paragraph_time = rotate_duration + display_duration + fade_duration
            
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
                                params['rotate_duration'], params['display_duration'], params['fade_duration']
                            )
                            
                            # 行の個別タイミングを計算
                            line_timing = self._calculate_line_individual_timings(
                                base_timing, line_start_offset, params
                            )
                            
                            # この行の完了時間（fade終了時間）
                            line_end_time = line_timing['fade'].end_time
                            max_end_time = max(max_end_time, line_end_time)
                
                total_time = max_end_time
            else:
                total_time = 0.0
        
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
        start_y = center_y + int(params['rise_distance'])
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
                
                # 行の開始遅延を計算
                line_start_offset = self._calculate_line_start_offset(
                    line_index, group, params['line_start_delay'], 
                    params['rotate_duration'], params['display_duration'], params['fade_duration']
                )
                
                # 各行の個別タイミングを計算
                line_timing_set = self._calculate_line_individual_timings(
                    timing_set, line_start_offset, params
                )
                
                # Phase 1: 回転しながら上昇
                rotate_text = self._create_rotate_up_effect(
                    line, center_x, start_line_y, line_y, 
                    params['rotate_duration'] * 1000, 
                    params['rotation_angle']
                )
                rotate_line = self.create_dialogue_line(rotate_text, line_timing_set['rotate'])
                dialogue_lines.append(rotate_line)
                
                # Phase 2: 中央での表示
                display_text = self._create_display_effect(line, center_x, line_y)
                display_line = self.create_dialogue_line(display_text, line_timing_set['display'])
                display_line = display_line.replace(f"Dialogue: 0,", f"Dialogue: 1,")  # レイヤー変更
                dialogue_lines.append(display_line)
                
                # Phase 3: フェードアウト
                fade_text = self._create_fade_out_effect(
                    line, center_x, line_y, params['fade_duration'] * 1000
                )
                fade_line = self.create_dialogue_line(fade_text, line_timing_set['fade'])
                fade_line = fade_line.replace(f"Dialogue: 0,", f"Dialogue: 2,")  # レイヤー変更
                dialogue_lines.append(fade_line)
        
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
        rotate_duration = params['rotate_duration']
        display_duration = params['display_duration']
        fade_duration = params['fade_duration']
        paragraph_interval = params['paragraph_interval']
        
        # 複雑さによる調整
        reading_speed_multiplier = formatted_text.get_timing_hint('reading_speed_multiplier', 1.0)
        
        for group_index, group in enumerate(paragraph_groups):
            # 段落の複雑さを計算（行数と文字数を考慮）
            paragraph_complexity = self._calculate_paragraph_complexity(group, formatted_text)
            adjusted_display = display_duration * paragraph_complexity * reading_speed_multiplier
            
            # Phase 1: 回転上昇
            rotate_timing = TimingInfo(
                start_time=current_time,
                end_time=current_time + rotate_duration,
                layer=0
            )
            current_time += rotate_duration
            
            # Phase 2: 表示
            display_timing = TimingInfo(
                start_time=current_time,
                end_time=current_time + adjusted_display,
                layer=1
            )
            current_time += adjusted_display
            
            # Phase 3: フェードアウト
            fade_timing = TimingInfo(
                start_time=current_time,
                end_time=current_time + fade_duration,
                layer=2
            )
            current_time += fade_duration
            
            # 段落間隔
            if group_index < len(paragraph_groups) - 1:
                current_time += paragraph_interval
            
            timings.append({
                'rotate': rotate_timing,
                'display': display_timing,
                'fade': fade_timing
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
    
    def _calculate_line_start_offset(self, line_index: int, paragraph_group: List[str],
                                   line_start_delay: float, rotate_duration: float,
                                   display_duration: float, fade_duration: float) -> float:
        """行の開始遅延時間を計算
        
        Args:
            line_index: 段落内の行インデックス（0から開始）
            paragraph_group: 段落内の行リスト
            line_start_delay: 遅延設定値（ms）
            rotate_duration: 回転時間（秒）
            display_duration: 表示時間（秒）
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
            # 負値：上の行の回転完了後に開始（期待される順次実行）
            accumulated_offset = 0.0
            
            # revolver_upでは順次実行 = 前行の回転完了後に次行開始
            single_rotate_duration = rotate_duration * 1000  # ms
            
            # 前の行の回転完了時間を累積計算
            accumulated_offset = line_index * single_rotate_duration
            
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
        rotate_duration = params['rotate_duration']
        display_duration = params['display_duration'] 
        fade_duration = params['fade_duration']
        
        # ベースタイミングの開始時間にオフセットを加算
        base_start = base_timing_set['rotate'].start_time
        line_start_time = base_start + offset_seconds
        
        # 各フェーズのタイミングを計算
        rotate_timing = TimingInfo(
            start_time=line_start_time,
            end_time=line_start_time + rotate_duration,
            layer=0
        )
        
        display_timing = TimingInfo(
            start_time=line_start_time + rotate_duration,
            end_time=line_start_time + rotate_duration + display_duration,
            layer=1
        )
        
        fade_timing = TimingInfo(
            start_time=line_start_time + rotate_duration + display_duration,
            end_time=line_start_time + rotate_duration + display_duration + fade_duration,
            layer=2
        )
        
        return {
            'rotate': rotate_timing,
            'display': display_timing,
            'fade': fade_timing
        }
    
    def _create_rotate_up_effect(self, text: str, center_x: int, start_y: int, 
                                center_y: int, duration_ms: float, angle: float) -> str:
        """回転上昇エフェクトを作成
        
        Args:
            text: 表示テキスト
            center_x: 中央X座標
            start_y: 開始Y座標
            center_y: 中央Y座標
            duration_ms: 時間（ミリ秒）
            angle: 回転角度
        
        Returns:
            ASS効果付きテキスト
        """
        duration_ms = int(duration_ms)
        return (f"{{\\move({center_x},{start_y},{center_x},{center_y})"
                f"\\alpha&HFF&\\t(0,{duration_ms},\\alpha&H00&\\frz{angle})}}{text}")
    
    def _create_display_effect(self, text: str, center_x: int, center_y: int) -> str:
        """表示エフェクトを作成
        
        Args:
            text: 表示テキスト
            center_x: 中央X座標
            center_y: 中央Y座標
        
        Returns:
            ASS効果付きテキスト
        """
        return f"{{\\pos({center_x},{center_y})\\alpha&H00&}}{text}"
    
    def _create_fade_out_effect(self, text: str, center_x: int, center_y: int, 
                               duration_ms: float) -> str:
        """フェードアウトエフェクトを作成
        
        Args:
            text: 表示テキスト
            center_x: 中央X座標
            center_y: 中央Y座標
            duration_ms: 時間（ミリ秒）
        
        Returns:
            ASS効果付きテキスト
        """
        duration_ms = int(duration_ms)
        return (f"{{\\pos({center_x},{center_y})"
                f"\\alpha&H00&\\t(0,{duration_ms},\\alpha&HFF&)}}{text}")