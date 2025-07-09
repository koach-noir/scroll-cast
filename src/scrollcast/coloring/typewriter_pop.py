"""
TypewriterPop Template
typewriter_pop - ASS生成特化版
"""

from typing import List
from .base import BaseTemplate, SubtitleTemplate, TemplateParameter, TimingInfo
from ..boxing import FormattedText
from ..utils.debug_logger import coloring_logger


class TypewriterPopTemplate(BaseTemplate):
    """typewriter_popテンプレート（ASS生成特化）"""
    
    def __init__(self):
        super().__init__()
        self.logger = coloring_logger("typewriter_pop")
    
    @property
    def template_info(self) -> SubtitleTemplate:
        return SubtitleTemplate(
            name="typewriter_pop",
            description="typewriter_popアニメーション効果",
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
        """各行のDialogue行を生成"""
        text_lines = formatted_text.get_text_lines()
        dialogue_lines = []
        
        duration = params['duration']
        delay = params['delay']
        font_size = params['font_size']
        
        for i, line in enumerate(text_lines):
            if not line.strip():
                continue
            
            # タイミング計算
            start_time = i * delay
            end_time = start_time + duration
            
            # ASS効果生成（TODO: テンプレート固有の効果を実装）
            ass_effect = self._generate_ass_effect(line, font_size, start_time, duration)
            
            # TimingInfo作成
            timing = TimingInfo(start_time=start_time, end_time=end_time, layer=0)
            
            # Dialogue行作成
            dialogue_line = self.create_dialogue_line(ass_effect, timing)
            dialogue_lines.append(dialogue_line)
        
        return dialogue_lines
    
    def _generate_ass_effect(self, text: str, font_size: int, start_time: float, duration: float) -> str:
        """ASS効果を生成（弾けて表示するアニメーション）"""
        duration_ms = int(duration * 1000)
        
        # 弾けて表示するアニメーション効果
        # 1. 小さくスケールダウンからスタート
        # 2. 大きくバウンスして表示
        # 3. 通常サイズに収束
        # 4. フェードアウト
        
        bounce_duration_ms = int(duration_ms * 0.3)  # 30%の時間でバウンス
        hold_duration_ms = int(duration_ms * 0.5)    # 50%の時間で保持
        fade_duration_ms = int(duration_ms * 0.2)    # 20%の時間でフェード
        
        return (
            f"{{\\pos(960,540)\\fs{font_size}\\an5\\c&HFFFFFF&"
            f"\\fscx0\\fscy0"  # 初期状態: スケール0
            f"\\t(0,{bounce_duration_ms//3},\\fscx150\\fscy150)"  # 拡大オーバーシュート
            f"\\t({bounce_duration_ms//3},{bounce_duration_ms*2//3},\\fscx80\\fscy80)"  # 縮小バウンス
            f"\\t({bounce_duration_ms*2//3},{bounce_duration_ms},\\fscx100\\fscy100)"  # 通常サイズに
            f"\\t({bounce_duration_ms + hold_duration_ms},{duration_ms},\\alpha&HFF&)"  # フェードアウト
            f"}}"
            f"{text}"
        )
