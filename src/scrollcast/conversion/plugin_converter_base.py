"""
Base class for Plugin-based ASS to HTML converters
プラグイン型ASS→HTML変換共通基底クラス
"""

import re
from abc import ABC, abstractmethod
from typing import Dict, Any
from .utils import ASSMetadata, HTMLTemplateBuilder
from .plugin_system import TemplateConfig, TemplateComposer


class PluginConverterBase(ABC):
    """プラグイン型ASS→HTML変換の共通基底クラス"""
    
    def __init__(self):
        self.metadata: ASSMetadata = ASSMetadata()
        self.total_duration_ms = 0
        self.template_composer = TemplateComposer()
    
    @abstractmethod
    def get_template_config(self) -> TemplateConfig:
        """テンプレート固有のプラグイン設定を返す"""
        pass
    
    @abstractmethod
    def parse_ass_file(self, ass_file_path: str) -> None:
        """ASSファイルを解析（テンプレート固有実装）"""
        pass
    
    @abstractmethod
    def _get_timing_data_json(self) -> str:
        """タイミングデータのJSON文字列を返す"""
        pass
    
    @abstractmethod
    def _build_template_html(self) -> str:
        """テンプレート固有HTML"""
        pass
    
    @abstractmethod
    def _build_ui_elements_html(self) -> str:
        """UI要素HTML"""
        pass
    
    @abstractmethod
    def _get_template_title(self) -> str:
        """HTMLタイトルを返す"""
        pass
    
    @abstractmethod
    def _get_responsive_css_class(self) -> str:
        """レスポンシブCSS用のクラス名を返す"""
        pass
    
    @abstractmethod
    def _get_print_template_name(self) -> str:
        """ログ出力用のテンプレート名を返す"""
        pass
    
    @abstractmethod
    def _get_data_count(self) -> int:
        """要素数を返す"""
        pass
    
    def read_ass_file_content(self, ass_file_path: str) -> str:
        """ASSファイルの内容を読み込む（共通処理）"""
        with open(ass_file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def remove_ass_tags(self, text_with_tags: str) -> str:
        """ASSタグを除去（統一処理）"""
        return re.sub(r'\{[^}]*\}', '', text_with_tags).strip()
    
    def generate_html(self, output_path: str) -> None:
        """HTMLファイルを生成（共通処理）"""
        if self._get_data_count() == 0:
            raise ValueError("解析データが未設定です。parse_ass_file()を先に実行してください。")
        
        # プラグイン設定を取得
        template_config = self.get_template_config()
        
        # タイミングデータを取得
        timing_data = self._get_timing_data_json()
        
        # プラグインシステムでJavaScript/CSSを生成
        composed_result = self.template_composer.compose_template(template_config, timing_data)
        
        # HTMLコンテンツを構築
        html_content = self._build_html_content(composed_result)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _build_html_content(self, composed_result: Dict[str, str]) -> str:
        """HTML/CSS/JavaScriptを統合したコンテンツを生成（共通処理）"""
        title = HTMLTemplateBuilder.build_head(self._get_template_title())
        base_css = HTMLTemplateBuilder.build_base_css_minimal()
        ui_css = HTMLTemplateBuilder.build_ui_elements_css()
        
        # レスポンシブCSS設定
        responsive_css = self._build_responsive_css()
        
        template_html = self._build_template_html()
        ui_html = self._build_ui_elements_html()
        
        return f"""<!DOCTYPE html>
<html lang="ja">
{title}
    <!-- ScrollCast Shared Styles -->
    <link rel="stylesheet" href="shared/scrollcast-styles.css">
    <style>
{base_css}
        
{responsive_css}
        
{composed_result['css']}
        
{ui_css}
    </style>
</head>
<body>
{template_html}
    
{ui_html}
    
    <!-- ScrollCast Core Library -->
    <script src="shared/scrollcast-core.js"></script>
    <script>
{composed_result['javascript']}
    </script>
</body>
</html>"""
    
    def _build_responsive_css(self) -> str:
        """レスポンシブCSS設定（共通処理）"""
        css_class = self._get_responsive_css_class()
        
        # SimpleRoleの場合は追加のCSS設定
        additional_css = ""
        if css_class == "role-container":
            additional_css = """
                max-width: 800px;
                margin: 0 auto;"""
        elif css_class == "railway-container":
            additional_css = """
                max-width: 600px;"""
        elif css_class == "typewriter-container":
            additional_css = """
                max-width: 600px;"""
        
        return f"""
        .{css_class} {{
            font-size: {self.metadata.responsive_font_size}vw;
            font-family: {self.metadata.font_family}, sans-serif;
        }}
        
        /* デスクトップ表示での固定サイズ */
        @media (min-width: 768px) {{
            .{css_class} {{
                font-size: {self.metadata.font_size}px;{additional_css}
            }}
        }}
        """
    
    def convert_ass_to_html(self, ass_file_path: str, html_output_path: str) -> None:
        """ASS→HTML変換の一括処理（共通処理）"""
        self.parse_ass_file(ass_file_path)
        self.generate_html(html_output_path)
        
        template_name = self._get_print_template_name()
        print(f"✅ {template_name} ASS→HTML変換完了:")
        print(f"   入力: {ass_file_path}")
        print(f"   出力: {html_output_path}")
        print(f"   総時間: {self.total_duration_ms}ms")
        print(f"   要素数: {self._get_data_count()}")
        print(f"   プラグイン: {', '.join(self.get_template_config().required_plugins)}")