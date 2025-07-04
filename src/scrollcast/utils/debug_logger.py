"""
5層構造デバッグロガー
各層の処理状況を戦略的に監視・記録
"""

import logging
import os
from typing import Any, Optional
from enum import Enum


class LayerType(Enum):
    """5層構造の層タイプ"""
    ORCHESTRATOR = "orchestrator"
    CLI = "cli"
    RENDERING = "rendering" 
    COLORING = "coloring"
    BOXING = "boxing"
    PACKING = "packing"


class DebugLogger:
    """5層構造専用デバッグロガー"""
    
    def __init__(self, layer: LayerType, component_name: str):
        """
        Args:
            layer: 所属する層
            component_name: コンポーネント名
        """
        self.layer = layer
        self.component_name = component_name
        self.logger = logging.getLogger(f"{layer.value}.{component_name}")
        
        # デバッグレベルの設定（環境変数で制御）
        debug_level = os.getenv('SUBTITLE_DEBUG_LEVEL', 'WARNING')
        self.logger.setLevel(getattr(logging, debug_level.upper()))
        
        # ハンドラーが未設定の場合のみ追加
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'🏗️ [{layer.value.upper()}:{component_name}] %(levelname)s: %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def input_data(self, data: Any, description: str = "入力データ") -> None:
        """層への入力データをログ出力"""
        if isinstance(data, str):
            preview = data[:50] + "..." if len(data) > 50 else data
            self.logger.debug(f"📥 {description}: '{preview}'")
        else:
            self.logger.debug(f"📥 {description}: {type(data).__name__}")
    
    def output_data(self, data: Any, description: str = "出力データ") -> None:
        """層からの出力データをログ出力"""
        if isinstance(data, str):
            preview = data[:50] + "..." if len(data) > 50 else data
            self.logger.debug(f"📤 {description}: '{preview}'")
        else:
            self.logger.debug(f"📤 {description}: {type(data).__name__}")
    
    def processing_step(self, step_name: str, details: str = "") -> None:
        """処理ステップをログ出力"""
        message = f"⚙️ {step_name}"
        if details:
            message += f": {details}"
        self.logger.debug(message)
    
    def transformation(self, before: Any, after: Any, operation: str) -> None:
        """データ変換をログ出力"""
        if isinstance(before, str) and isinstance(after, str):
            before_preview = before[:30] + "..." if len(before) > 30 else before
            after_preview = after[:30] + "..." if len(after) > 30 else after
            self.logger.debug(f"🔄 {operation}: '{before_preview}' → '{after_preview}'")
        else:
            self.logger.debug(f"🔄 {operation}: {type(before).__name__} → {type(after).__name__}")
    
    def error_found(self, error_type: str, details: str) -> None:
        """エラー発見をログ出力"""
        self.logger.error(f"❌ {error_type}: {details}")
    
    def performance_metric(self, metric_name: str, value: float, unit: str = "") -> None:
        """パフォーマンス指標をログ出力"""
        self.logger.info(f"📊 {metric_name}: {value:.2f}{unit}")
    
    def layer_boundary(self, direction: str, target_layer: str, data_summary: str = "") -> None:
        """層間境界の通過をログ出力"""
        arrow = "→" if direction == "to" else "←"
        message = f"🏗️ {self.layer.value} {arrow} {target_layer}"
        if data_summary:
            message += f" ({data_summary})"
        self.logger.debug(message)


def get_layer_logger(layer: LayerType, component_name: str) -> DebugLogger:
    """5層構造デバッグロガーを取得
    
    Args:
        layer: 層タイプ
        component_name: コンポーネント名
        
    Returns:
        設定済みデバッグロガー
    """
    return DebugLogger(layer, component_name)


def enable_debug_logging():
    """デバッグログを有効化"""
    os.environ['SUBTITLE_DEBUG_LEVEL'] = 'DEBUG'


def disable_debug_logging():
    """デバッグログを無効化"""
    os.environ['SUBTITLE_DEBUG_LEVEL'] = 'WARNING'


# 各層用の便利関数
def boxing_logger(component_name: str) -> DebugLogger:
    """Boxing層用ロガー"""
    return get_layer_logger(LayerType.BOXING, component_name)


def coloring_logger(component_name: str) -> DebugLogger:
    """Coloring層用ロガー"""
    return get_layer_logger(LayerType.COLORING, component_name)


def packing_logger(component_name: str) -> DebugLogger:
    """Packing層用ロガー"""
    return get_layer_logger(LayerType.PACKING, component_name)


def rendering_logger(component_name: str) -> DebugLogger:
    """Rendering層用ロガー"""
    return get_layer_logger(LayerType.RENDERING, component_name)


def orchestrator_logger(component_name: str) -> DebugLogger:
    """Orchestrator層用ロガー"""
    return get_layer_logger(LayerType.ORCHESTRATOR, component_name)