"""
Simple Role Template (New Architecture)
シンプルロール映画エンドロール風エフェクト - ASS生成特化版
"""

from typing import List
from dataclasses import dataclass
from .base import BaseTemplate, SubtitleTemplate, TemplateParameter, TimingInfo
from ..boxing import FormattedText


@dataclass
class SimpleRoleTimingInfo(TimingInfo):
    """SimpleRole用タイミング情報"""
    text: str = ""
    style_overrides: dict = None
    metadata: dict = None
    
    def __post_init__(self):
        if self.style_overrides is None:
            self.style_overrides = {}
        if self.metadata is None:
            self.metadata = {}


class SimpleRoleTemplate(BaseTemplate):
    """シンプルロール映画エンドロール風エフェクトテンプレート（ASS生成特化）"""
    
    @property
    def template_info(self) -> SubtitleTemplate:
        return SubtitleTemplate(
            name="simple_role",
            description="映画エンドロール風1行連続フロー（下→上 連続表示）",
            parameters={
                "animation_duration": TemplateParameter(
                    name="animation_duration",
                    type=float,
                    default=8.0,
                    description="画面通過時間（秒）",
                    min_value=4.0,
                    max_value=15.0
                ),
                "line_interval": TemplateParameter(
                    name="line_interval",
                    type=float,
                    default=0.2,
                    description="行間間隔時間（秒）",
                    min_value=0.1,
                    max_value=2.0
                ),
                "font_size": TemplateParameter(
                    name="font_size",
                    type=int,
                    default=36,
                    description="フォントサイズ",
                    min_value=24,
                    max_value=72
                ),
                "scroll_speed": TemplateParameter(
                    name="scroll_speed",
                    type=float,
                    default=1.0,
                    description="スクロール速度倍率",
                    min_value=0.5,
                    max_value=2.0
                )
            }
        )
    
    def generate_timing_data(self, formatted_texts: List[FormattedText], **kwargs) -> List[SimpleRoleTimingInfo]:
        """SimpleRole用タイミングデータ生成"""
        # パラメータ取得
        animation_duration = kwargs.get('animation_duration', 8.0)
        line_interval = kwargs.get('line_interval', 0.2)
        scroll_speed = kwargs.get('scroll_speed', 1.0)
        
        # 実際のアニメーション時間を計算
        actual_animation_duration = animation_duration / scroll_speed
        
        timing_data = []
        current_time = 0.0
        
        # すべてのFormattedTextからテキスト行を取得
        for formatted_text in formatted_texts:
            text_lines = formatted_text.get_text_lines()
            
            for i, line_text in enumerate(text_lines):
                # 各行は画面通過時間分表示
                start_time = current_time
                end_time = start_time + actual_animation_duration
                
                timing_info = SimpleRoleTimingInfo(
                    start_time=start_time,
                    end_time=end_time,
                    text=line_text,
                    style_overrides={
                        'alignment': 5,  # 中央揃え
                        'margin_v': 960,  # 1080pの中央
                        'layer': 0,
                        'effect': 'simple_role_scroll'
                    },
                    metadata={
                        'line_index': len(timing_data),
                        'animation_duration': actual_animation_duration,
                        'scroll_speed': scroll_speed
                    }
                )
                
                timing_data.append(timing_info)
                
                # 次の行開始時間
                current_time += line_interval
        
        return timing_data
    
    def generate_ass_dialogue_lines(self, timing_data: List[SimpleRoleTimingInfo], **kwargs) -> List[str]:
        """ASS Dialogue行生成（SimpleRole固有）"""
        font_size = kwargs.get('font_size', 36)
        animation_duration = kwargs.get('animation_duration', 8.0)
        scroll_speed = kwargs.get('scroll_speed', 1.0)
        
        # 実際のアニメーション時間
        actual_duration = animation_duration / scroll_speed
        actual_duration_ms = int(actual_duration * 1000)
        
        dialogue_lines = []
        
        for timing in timing_data:
            start_time = self._format_time(timing.start_time)
            end_time = self._format_time(timing.end_time)
            
            # SimpleRole用ASSタグ
            # 画面下から上への移動アニメーション
            ass_text = (
                f"{{\\pos(960,1200)\\fs{font_size}\\an5\\c&HFFFFFF&"
                f"\\move(960,1200,960,-120,0,{actual_duration_ms})}}"
                f"{timing.text}"
            )
            
            dialogue_line = (
                f"Dialogue: {timing.style_overrides.get('layer', 0)},"
                f"{start_time},{end_time},"
                f"Default,,0,0,0,,"
                f"{ass_text}"
            )
            
            dialogue_lines.append(dialogue_line)
        
        return dialogue_lines
    
    def _format_time(self, seconds: float) -> str:
        """秒をASS時間形式に変換"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:05.2f}"
    
    def generate_ass_from_formatted(self, formatted_text: FormattedText, **kwargs) -> str:
        """整形済みテキストからASS字幕を生成"""
        # タイミングデータ生成
        timing_data = self.generate_timing_data([formatted_text], **kwargs)
        
        # ASSヘッダー生成
        resolution = kwargs.get('resolution', (1080, 1920))
        header = self.generate_ass_header(resolution, **kwargs)
        
        # Dialogue行生成
        dialogue_lines = self.generate_ass_dialogue_lines(timing_data, **kwargs)
        
        # 完全なASS内容を組み立て
        ass_content = header + "\n[Events]\n"
        ass_content += "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        
        for dialogue in dialogue_lines:
            ass_content += dialogue + "\n"
        
        return ass_content
    
    def calculate_total_duration(self, formatted_text: FormattedText, **kwargs) -> float:
        """総再生時間を計算"""
        line_interval = kwargs.get('line_interval', 0.2)
        animation_duration = kwargs.get('animation_duration', 8.0)
        scroll_speed = kwargs.get('scroll_speed', 1.0)
        
        # テキスト行のみを取得
        lines = formatted_text.get_text_lines()
        num_lines = len(lines)
        
        if num_lines == 0:
            return 0.0
        
        # 実際のアニメーション時間
        actual_animation_duration = animation_duration / scroll_speed
        
        # 最後の行が完全に通過するまでの時間
        total_duration = (num_lines - 1) * line_interval + actual_animation_duration
        
        return total_duration