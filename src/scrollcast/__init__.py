"""
Subtitle Generator - A Python library for generating ASS subtitle files
"""

__version__ = "0.1.0"
__author__ = "Claude Code Team"

# 既存API（互換性維持）
# from .generator import SubtitleGenerator  # 削除済み
# from .presets import StylePresets  # 削除済み
# from .parsers import SubtitleParser  # 削除済み
# from .ffmpeg_integration import FFmpegProcessor  # 削除済み
# from .resolution_presets import ResolutionPresets, DynamicPositioning  # 削除済み
# SimpleModernEffectsは新しいテンプレートシステムに置き換え済み
# 互換性のため、必要に応じて後で追加

# 新しいAPI  
from .orchestrator.template_engine import TemplateEngine
from .rendering.video_generator import VideoGenerator
from .packing.ass_builder import ASSBuilder

__all__ = [
    # 既存API
    # "SubtitleGenerator",  # 削除済み 
    # "StylePresets",  # 削除済み 
    # "SubtitleParser",  # 削除済み 
    # "FFmpegProcessor",  # 削除済み
    # "ResolutionPresets",  # 削除済み
    # "DynamicPositioning",  # 削除済み
    # "SimpleModernEffects",  # 新テンプレートシステムに置き換え済み
    # 新しいAPI
    "TemplateEngine",
    "VideoGenerator", 
    "ASSBuilder",
]

# 便利関数
def generate_video(template: str, text: str, output_path: str, **kwargs):
    """字幕動画を生成する便利関数
    
    Args:
        template: テンプレート名
        text: テキスト
        output_path: 出力パス
        **kwargs: テンプレート固有のパラメータ
    
    Returns:
        bool: 成功の可否
    """
    engine = TemplateEngine()
    return engine.generate_video(template, text, output_path, **kwargs)

def list_templates():
    """利用可能なテンプレート一覧を取得
    
    Returns:
        List[str]: テンプレート名のリスト
    """
    engine = TemplateEngine()
    return engine.list_templates()