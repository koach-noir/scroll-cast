"""
Revolver Up Template (New Architecture)
回転式上昇エフェクト - ASS生成特化版
"""

from typing import List
from .base import BaseTemplate, SubtitleTemplate, TemplateParameter, TimingInfo
from ..boxing import FormattedText


class RevolverUpTemplate(BaseTemplate):
    """回転式上昇エフェクトテンプレート（ASS生成特化）"""
    
    @property
    def template_info(self) -> SubtitleTemplate:
        return SubtitleTemplate(
            name="revolver_up",
            description="中央開始エンドロール風（中央一時停止付き連続スクロール）",
            parameters={
                "animation_duration": TemplateParameter(
                    name="animation_duration",
                    type=float,
                    default=6.0,
                    description="画面通過時間（秒）",
                    min_value=3.0,
                    max_value=12.0
                ),
                "pause_duration": TemplateParameter(
                    name="pause_duration",
                    type=float,
                    default=1.5,
                    description="中央での一時停止時間（秒）",
                    min_value=0.5,
                    max_value=3.0
                ),
                "line_interval": TemplateParameter(
                    name="line_interval",
                    type=float,
                    default=0.2,
                    description="行間間隔時間（秒）",
                    min_value=0.1,
                    max_value=1.0
                ),
                "scroll_speed": TemplateParameter(
                    name="scroll_speed",
                    type=float,
                    default=1.0,
                    description="スクロール速度倍率",
                    min_value=0.5,
                    max_value=2.0
                ),
                "pause_position": TemplateParameter(
                    name="pause_position",
                    type=float,
                    default=0.5,
                    description="一時停止位置（0.0=中央下, 0.5=中央, 1.0=中央上）",
                    min_value=0.0,
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
        
        animation_duration = params['animation_duration']
        pause_duration = params['pause_duration']
        line_interval = params['line_interval']
        scroll_speed = params['scroll_speed']
        
        # 実際のアニメーション時間
        actual_animation_duration = animation_duration / scroll_speed
        
        # エンドロール式計算：最後の行が完全に画面を通過するまで
        total_time = (len(text_lines) - 1) * line_interval + actual_animation_duration + pause_duration
        
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
        pause_position = params['pause_position']
        
        # 一時停止位置を計算（中央から上下に調整）
        pause_y = int(center_y + (pause_position - 0.5) * 200)  # ±100px範囲
        
        # タイミング計算
        timings = self._calculate_continuous_timings(formatted_text, params)
        
        # テキスト行のみを処理
        text_lines = formatted_text.get_text_lines()
        
        for i, line in enumerate(text_lines):
            if not line.strip() or i >= len(timings):
                continue
            
            timing_set = timings[i]
            
            # 連続スクロール（中央開始→一時停止→上昇消失）
            scroll_text = self._create_continuous_scroll_effect(
                line, center_x, pause_y, 
                params['animation_duration'], params['pause_duration'], params['scroll_speed']
            )
            scroll_line = self.create_dialogue_line(scroll_text, timing_set)
            dialogue_lines.append(scroll_line)
        
        return dialogue_lines
    
    def _calculate_continuous_timings(self, formatted_text: FormattedText, params: dict) -> List[TimingInfo]:
        """連続スクロールタイミングを計算
        
        Args:
            formatted_text: 整形済みテキスト
            params: パラメータ
        
        Returns:
            各行のタイミング情報のリスト
        """
        text_lines = formatted_text.get_text_lines()
        timings = []
        current_time = 0.0
        
        animation_duration = params['animation_duration']
        pause_duration = params['pause_duration']
        line_interval = params['line_interval']
        scroll_speed = params['scroll_speed']
        
        # 実際のアニメーション時間
        actual_animation_duration = animation_duration / scroll_speed
        
        # 複雑さによる調整
        line_complexities = formatted_text.get_timing_hint('line_complexities', [1.0] * len(text_lines))
        reading_speed_multiplier = formatted_text.get_timing_hint('reading_speed_multiplier', 1.0)
        
        for i, line in enumerate(text_lines):
            if not line.strip():
                continue
            
            # 複雑さを考慮した調整
            complexity = line_complexities[i] if i < len(line_complexities) else 1.0
            adjusted_pause = pause_duration * complexity * reading_speed_multiplier
            
            # 各行の総表示時間
            total_line_duration = actual_animation_duration + adjusted_pause
            
            timing = TimingInfo(
                start_time=current_time,
                end_time=current_time + total_line_duration,
                layer=0
            )
            
            timings.append(timing)
            
            # 次の行はエンドロール風に短い間隔で開始
            current_time += line_interval
        
        return timings
    
    def _create_continuous_scroll_effect(self, text: str, center_x: int, pause_y: int, 
                                        animation_duration: float, pause_duration: float, 
                                        scroll_speed: float) -> str:
        """連続スクロールエフェクトを作成（中央開始→一時停止→上昇消失）
        
        Args:
            text: 表示テキスト
            center_x: 中央X座標
            pause_y: 一時停止Y座標
            animation_duration: アニメーション総時間（秒）
            pause_duration: 一時停止時間（秒）
            scroll_speed: スクロール速度倍率
        
        Returns:
            ASS効果付きテキスト
        """
        # 実際の時間計算
        actual_animation_duration = animation_duration / scroll_speed
        scroll_duration = actual_animation_duration - pause_duration
        
        # 時間をミリ秒に変換
        pause_duration_ms = int(pause_duration * 1000)
        scroll_duration_ms = int(scroll_duration * 1000)
        total_duration_ms = int(actual_animation_duration * 1000)
        
        # 位置計算
        start_y = pause_y  # 中央から開始
        end_y = pause_y - 300  # 上に消失
        
        # ASSエフェクト：中央出現→一時停止→上昇消失
        ass_text = (
            f"{{\\pos({center_x},{start_y})\\alpha&H00&"  # 中央に出現
            f"\\t(0,{pause_duration_ms},\\alpha&H00&)"  # 一時停止
            f"\\t({pause_duration_ms},{total_duration_ms},\\move({center_x},{start_y},{center_x},{end_y})\\alpha&HFF&)"  # 上昇消失
            f"}}{text}"
        )
        
        return ass_text