"""
Railway Scroll Template (New Architecture)
鉄道方向幕風スクロールエフェクト - ASS生成特化版
"""

from typing import List
from .base import BaseTemplate, SubtitleTemplate, TemplateParameter, TimingInfo
from ..boxing import FormattedText


class RailwayScrollTemplate(BaseTemplate):
    """鉄道方向幕風スクロールエフェクトテンプレート（ASS生成特化）"""
    
    @property
    def template_info(self) -> SubtitleTemplate:
        return SubtitleTemplate(
            name="railway_scroll",
            description="鉄道方向幕風1行フロー（下→中央→上 フェードイン・アウト）",
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
                "overlap_duration": TemplateParameter(
                    name="overlap_duration",
                    type=float,
                    default=0.4,
                    description="次行との重複時間（秒）",
                    min_value=0.0,
                    max_value=1.0
                ),
                "empty_line_pause": TemplateParameter(
                    name="empty_line_pause",
                    type=float,
                    default=1.0,
                    description="空行での一時停止時間（秒）",
                    min_value=0.0,
                    max_value=3.0
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
        
        # 各行のDialogue行を生成
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
        
        text_lines = formatted_text.get_text_lines()
        if not text_lines:
            return 0.0
        
        # 各フェーズの時間
        fade_in = params['fade_in_duration']
        pause = params['pause_duration']
        fade_out = params['fade_out_duration']
        overlap = params['overlap_duration']
        
        # 1行あたりの時間（重複を除く）
        single_line_time = fade_in + pause + fade_out - overlap
        
        # 総時間計算
        total_time = len(text_lines) * single_line_time + overlap
        
        # 空行の時間を追加
        if formatted_text.empty_line_positions:
            empty_pause = params['empty_line_pause']
            total_time += len(formatted_text.empty_line_positions) * empty_pause
        
        return total_time
    
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
        
        # タイミング計算
        timings = self._calculate_railway_timings(formatted_text, params)
        
        # テキスト行のみを処理
        text_lines = formatted_text.get_text_lines()
        timing_index = 0
        
        for line in text_lines:
            if not line.strip():
                continue
            
            if timing_index >= len(timings):
                break
            
            timing_set = timings[timing_index]
            timing_index += 1
            
            # Phase 1: フェードイン（下→中央）
            fade_in_text = self._create_fade_in_effect(
                line, center_x, start_y, center_y, params['fade_in_duration'] * 1000
            )
            fade_in_line = self.create_dialogue_line(fade_in_text, timing_set['fade_in'])
            dialogue_lines.append(fade_in_line)
            
            # Phase 2: 中央での一時停止
            pause_text = self._create_pause_effect(line, center_x, center_y)
            pause_line = self.create_dialogue_line(pause_text, timing_set['pause'])
            pause_line = pause_line.replace(f"Dialogue: 0,", f"Dialogue: 1,")  # レイヤー変更
            dialogue_lines.append(pause_line)
            
            # Phase 3: フェードアウト（中央→上）
            fade_out_text = self._create_fade_out_effect(
                line, center_x, center_y, end_y, params['fade_out_duration'] * 1000
            )
            fade_out_line = self.create_dialogue_line(fade_out_text, timing_set['fade_out'])
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
    
    def _calculate_railway_timings(self, formatted_text: FormattedText, params: dict) -> List[dict]:
        """鉄道方向幕用のタイミングを計算
        
        Args:
            formatted_text: 整形済みテキスト
            params: パラメータ
        
        Returns:
            各行のタイミング辞書のリスト
        """
        text_lines = formatted_text.get_text_lines()
        timings = []
        current_time = 0.0
        
        # 基本時間
        fade_in_duration = params['fade_in_duration']
        pause_duration = params['pause_duration']
        fade_out_duration = params['fade_out_duration']
        overlap_duration = params['overlap_duration']
        
        # 複雑さによる調整
        line_complexities = formatted_text.get_timing_hint('line_complexities', [1.0] * len(text_lines))
        reading_speed_multiplier = formatted_text.get_timing_hint('reading_speed_multiplier', 1.0)
        
        for i, line in enumerate(text_lines):
            if not line.strip():
                continue
            
            # 複雑さを考慮した調整
            complexity = line_complexities[i] if i < len(line_complexities) else 1.0
            adjusted_pause = pause_duration * complexity * reading_speed_multiplier
            
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
            
            # 次の行は重複して開始
            current_time += fade_out_duration - overlap_duration
            
            timings.append({
                'fade_in': fade_in_timing,
                'pause': pause_timing,
                'fade_out': fade_out_timing
            })
        
        return timings
    
    def _calculate_empty_line_timings(self, formatted_text: FormattedText, params: dict) -> List[TimingInfo]:
        """空行のタイミングを計算"""
        empty_timings = []
        
        if not formatted_text.empty_line_positions:
            return empty_timings
        
        empty_pause = params['empty_line_pause']
        
        # 簡単な実装：空行は固定時間で表示
        for i, empty_pos in enumerate(formatted_text.empty_line_positions):
            # 空行の表示時間を計算（適切な位置に挿入）
            start_time = empty_pos * 2.0  # 簡易計算
            timing = TimingInfo(
                start_time=start_time,
                end_time=start_time + empty_pause,
                layer=3
            )
            empty_timings.append(timing)
        
        return empty_timings
    
    def _create_fade_in_effect(self, text: str, center_x: int, start_y: int, 
                              center_y: int, duration_ms: float) -> str:
        """フェードインエフェクトを作成
        
        Args:
            text: 表示テキスト
            center_x: 中央X座標
            start_y: 開始Y座標
            center_y: 中央Y座標
            duration_ms: 時間（ミリ秒）
        
        Returns:
            ASS効果付きテキスト
        """
        duration_ms = int(duration_ms)
        return (f"{{\\move({center_x},{start_y},{center_x},{center_y})"
                f"\\alpha&HFF&\\t(0,{duration_ms},\\alpha&H00&)}}{text}")
    
    def _create_pause_effect(self, text: str, center_x: int, center_y: int) -> str:
        """一時停止エフェクトを作成
        
        Args:
            text: 表示テキスト
            center_x: 中央X座標
            center_y: 中央Y座標
        
        Returns:
            ASS効果付きテキスト
        """
        return f"{{\\pos({center_x},{center_y})\\alpha&H00&}}{text}"
    
    def _create_fade_out_effect(self, text: str, center_x: int, center_y: int, 
                               end_y: int, duration_ms: float) -> str:
        """フェードアウトエフェクトを作成
        
        Args:
            text: 表示テキスト
            center_x: 中央X座標
            center_y: 中央Y座標
            end_y: 終了Y座標
            duration_ms: 時間（ミリ秒）
        
        Returns:
            ASS効果付きテキスト
        """
        duration_ms = int(duration_ms)
        return (f"{{\\move({center_x},{center_y},{center_x},{end_y})"
                f"\\alpha&H00&\\t(0,{duration_ms},\\alpha&HFF&)}}{text}")