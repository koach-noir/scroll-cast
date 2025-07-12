"""
TypewriterFillScreen Template
typewriter_fill_screen - ASS生成特化版
"""

from typing import List
from .base import BaseTemplate, SubtitleTemplate, TemplateParameter, TimingInfo
from ..boxing import FormattedText
from ..utils.debug_logger import coloring_logger


class TypewriterFillScreenTemplate(BaseTemplate):
    """typewriter_fill_screenテンプレート（ASS生成特化）"""
    
    def __init__(self):
        super().__init__()
        self.logger = coloring_logger("typewriter_fill_screen")
    
    @property
    def template_info(self) -> SubtitleTemplate:
        return SubtitleTemplate(
            name="typewriter_fill_screen",
            description="typewriter_fill_screenアニメーション効果",
            parameters={
                "duration": TemplateParameter(
                    name="duration",
                    type=float,
                    default=8.0,
                    description="アニメーション継続時間（秒）",
                    min_value=1.0,
                    max_value=30.0
                ),
                "delay": TemplateParameter(
                    name="delay",
                    type=float,
                    default=0.5,
                    description="行間の遅延時間（秒）",
                    min_value=0.0,
                    max_value=5.0
                ),
                "font_size": TemplateParameter(
                    name="font_size",
                    type=int,
                    default=64,
                    description="フォントサイズ",
                    min_value=24,
                    max_value=120
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
        
        # パラメータ検証
        params = self.validate_parameters(**kwargs)
        self.logger.processing_step("パラメータ検証", f"duration={params['duration']}")
        
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
        text_lines = formatted_text.get_text_lines()
        
        duration = params['duration']
        delay = params['delay']
        
        # 基本計算: 最後の行の開始時間 + 表示時間
        total_time = len(text_lines) * delay + duration
        
        self.logger.processing_step("時間計算", f"{len(text_lines)}行 × {delay}s + {duration}s = {total_time}s")
        
        return total_time
    
    def _generate_dialogue_lines(self, formatted_text: FormattedText, params: dict) -> List[str]:
        """各行のDialogue行を生成 - 画面縦サイズいっぱいに行を敷き詰める"""
        text_lines = formatted_text.get_text_lines()
        dialogue_lines = []
        
        duration = params['duration']
        delay = params['delay']
        font_size = params['font_size']
        
        # 画面解像度と行数計算
        screen_height = 1080
        line_height = font_size * 1.2
        lines_per_screen = int(screen_height / line_height)
        
        for i, line in enumerate(text_lines):
            if not line.strip():
                continue
            
            # 画面内の行位置計算（画面がいっぱいになったら0から再開）
            line_position_in_screen = i % lines_per_screen
            screen_number = i // lines_per_screen
            
            # Y座標計算（上端から下端まで敷き詰め）
            y_position = (line_position_in_screen * line_height) + (font_size // 2)
            
            # タイミング計算
            start_time = i * delay
            end_time = start_time + duration
            
            # 画面クリア効果（新しい画面の最初の行の時）
            if line_position_in_screen == 0 and screen_number > 0:
                # 前の画面をクリア
                clear_time = start_time - 0.1
                clear_effect = f"{{\\pos(960,540)\\fs{font_size}\\an5\\c&H000000&\\alpha&H00&}}"
                clear_timing = TimingInfo(start_time=clear_time, end_time=start_time, layer=10)
                clear_dialogue = self.create_dialogue_line(clear_effect, clear_timing)
                dialogue_lines.append(clear_dialogue)
            
            # ASS効果生成
            ass_effect = self._generate_ass_effect_with_position(line, font_size, y_position, start_time, duration)
            
            # TimingInfo作成
            timing = TimingInfo(start_time=start_time, end_time=end_time, layer=0)
            
            # Dialogue行作成
            dialogue_line = self.create_dialogue_line(ass_effect, timing)
            dialogue_lines.append(dialogue_line)
        
        return dialogue_lines
    
    def _generate_ass_effect_with_position(self, text: str, font_size: int, y_position: float, start_time: float, duration: float) -> str:
        """指定されたY座標での位置固定ASS効果を生成"""
        duration_ms = int(duration * 1000)
        screen_width = 960  # 中央位置
        
        return (
            f"{{\\pos({screen_width},{int(y_position)})\\fs{font_size}\\an5\\c&HFFFFFF&"
            f"\\fad(200,200)}}"
            f"{text}"
        )
