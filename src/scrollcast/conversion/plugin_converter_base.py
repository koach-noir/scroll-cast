"""
Base class for Plugin-based ASS to HTML converters
プラグイン型ASS→HTML変換共通基底クラス
"""

import re
import os
from abc import ABC, abstractmethod
from typing import Dict, Any
from .utils import ASSMetadata, HTMLTemplateBuilder
from .plugin_system import TemplateConfig, TemplateComposer
from ..deployment.file_deployer import FileDeployer


class PluginConverterBase(ABC):
    """プラグイン型ASS→HTML変換の共通基底クラス"""
    
    def __init__(self):
        self.metadata: ASSMetadata = ASSMetadata()
        self.total_duration_ms = 0
        self.template_composer = TemplateComposer()
        self.file_deployer = FileDeployer()
    
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
        
        # 必要なアセットファイルを配信
        output_dir = os.path.dirname(output_path)
        self._deploy_required_assets(output_dir, template_config)
        
        # HTMLコンテンツを構築（外部参照版）
        html_content = self._build_html_content_with_external_js(template_config, timing_data)
        
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
        if "scroll" in css_class:
            additional_css = """
                max-width: 800px;
                margin: 0 auto;"""
        elif "railway" in css_class:
            additional_css = """
                max-width: 600px;"""
        elif "typewriter" in css_class:
            additional_css = """
                max-width: 600px;"""
        
        return f"""
        {css_class} {{
            font-size: {self.metadata.responsive_font_size}vw;
            font-family: {self.metadata.font_family}, sans-serif;
        }}
        
        /* デスクトップ表示での固定サイズ */
        @media (min-width: 768px) {{
            {css_class} {{
                font-size: {self.metadata.font_size}px;{additional_css}
            }}
        }}
        """
    
    def _deploy_required_assets(self, output_dir: str, template_config: TemplateConfig) -> None:
        """必要なアセットファイルを配信"""
        try:
            # 共通アセットを配信
            self.file_deployer.deploy_shared_assets(output_dir)
            
            # 必要なプラグインファイルを配信
            self.file_deployer.deploy_plugin_files(output_dir, template_config.required_plugins)
            
            # テンプレート固有アセットを配信
            template_category = self._get_template_category()
            template_name = self._get_template_name()
            if template_category and template_name:
                self.file_deployer.sync_template_assets(output_dir, template_category, template_name)
            
            # アセットマニフェストを作成
            self.file_deployer.create_asset_manifest(output_dir)
            
        except Exception as e:
            print(f"⚠️  アセット配信で警告: {e}")
    
    def _generate_template_css_links(self) -> str:
        """テンプレート固有のCSS外部参照リンクを生成"""
        template_category = self._get_template_category()
        template_name = self._get_template_name()
        
        if not template_category or not template_name:
            return ""
        
        css_path = f"templates/{template_category}/{template_name}/sc-template.css"
        return f'    <!-- Template Specific Styles -->\n    <link rel="stylesheet" href="{css_path}">'
    
    def _build_html_content_with_external_js(self, template_config: TemplateConfig, timing_data: str) -> str:
        """外部JavaScript参照版のHTMLコンテンツを生成"""
        title = HTMLTemplateBuilder.build_head(self._get_template_title())
        base_css = HTMLTemplateBuilder.build_base_css_minimal()
        ui_css = HTMLTemplateBuilder.build_ui_elements_css()
        
        # レスポンシブCSS設定
        responsive_css = self._build_responsive_css()
        
        template_html = self._build_template_html()
        ui_html = self._build_ui_elements_html()
        
        # プラグイン用の外部スクリプト参照を生成
        plugin_scripts = self._generate_plugin_script_tags(template_config.required_plugins)
        
        # テンプレート用の外部CSS参照を生成
        template_css_links = self._generate_template_css_links()
        
        # テンプレート設定をJSON化
        import json
        config_json = json.dumps(template_config.to_dict(), ensure_ascii=False, indent=4)
        
        return f"""<!DOCTYPE html>
<html lang="ja">
{title}
    <!-- ScrollCast Shared Styles -->
    <link rel="stylesheet" href="shared/scrollcast-styles.css">
{template_css_links}
    <style>
{base_css}
        
{responsive_css}
        
{ui_css}
    </style>
</head>
<body>
{template_html}
    
{ui_html}
    
    <!-- ScrollCast Core Library -->
    <script src="shared/scrollcast-core.js"></script>
{plugin_scripts}
    
    <script>
        // Template Integration Layer
        document.addEventListener('DOMContentLoaded', function() {{
            // タイミングデータ
            const timingData = {timing_data};
            
            // テンプレート設定
            const templateConfig = {config_json};
            templateConfig.timingData = timingData;
            
            // ScrollCastコアで全プラグインを初期化
            if (window.ScrollCastCore) {{
                window.ScrollCastCore.initializePlugins(templateConfig);
            }}
        }});
    </script>
</body>
</html>"""
    
    def _generate_plugin_script_tags(self, required_plugins: list) -> str:
        """プラグイン用のスクリプトタグを生成"""
        script_tags = []
        for plugin_name in required_plugins:
            plugin_file = f"{plugin_name.replace('_', '-')}-plugin.js"
            script_tags.append(f'    <script src="assets/{plugin_file}"></script>')
        return '\n'.join(script_tags)
    
    def _get_template_category(self) -> str:
        """テンプレートカテゴリを取得（サブクラスでオーバーライド）"""
        template_name = self.get_template_config().template_name
        if "typewriter" in template_name:
            return "typewriter"
        elif "railway" in template_name:
            return "railway"
        elif "simple_role" in template_name:
            return "scroll"
        return ""
    
    def _get_template_name(self) -> str:
        """テンプレート名を取得（サブクラスでオーバーライド）"""
        template_name = self.get_template_config().template_name
        if template_name == "typewriter_fade":
            return "typewriter_fade"
        elif template_name == "railway_scroll":
            return "railway_scroll"
        elif template_name == "simple_role":
            return "scroll_role"
        return ""
    
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