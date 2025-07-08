"""
File Deployer for ScrollCast Assets
ScrollCast アセット配信システム
"""

import os
import shutil
import json
from typing import List, Dict, Set, Optional
from pathlib import Path


class FileDeployer:
    """ScrollCast アセットファイル配信クラス"""
    
    def __init__(self, web_source_dir: str = "src/web"):
        """
        Args:
            web_source_dir: Web静的ファイルソースディレクトリのパス
        """
        self.web_source_dir = web_source_dir
        self.deployed_assets: Set[str] = set()
        
    def deploy_shared_assets(self, output_dir: str) -> bool:
        """共通ライブラリファイルを配信
        
        Args:
            output_dir: 出力ディレクトリ (例: output-default/web)
            
        Returns:
            配信成功の可否
        """
        try:
            lib_dir = os.path.join(output_dir, "lib")
            os.makedirs(lib_dir, exist_ok=True)
            
            # 静的ファイルからlibディレクトリのファイルをコピー
            lib_source_dir = os.path.join(self.web_source_dir, "lib")
            
            for lib_file in ["scrollcast-styles.css", "scrollcast-core.js"]:
                source_path = os.path.join(lib_source_dir, lib_file)
                dest_path = os.path.join(lib_dir, lib_file)
                
                if os.path.exists(source_path):
                    shutil.copy2(source_path, dest_path)
                    self.deployed_assets.add(lib_file)
            
            
            print(f"✅ 共通ライブラリ配信完了: {lib_dir}")
            return True
            
        except Exception as e:
            print(f"❌ 共通アセット配信失敗: {e}")
            return False
    
    def deploy_plugin_files(self, output_dir: str, required_plugins: List[str]) -> bool:
        """必要なプラグインファイルを配信
        
        Args:
            output_dir: 出力ディレクトリ
            required_plugins: 必要なプラグイン名のリスト
            
        Returns:
            配信成功の可否
        """
        try:
            plugins_dir = os.path.join(output_dir, "plugins")
            os.makedirs(plugins_dir, exist_ok=True)
            plugins_source_dir = os.path.join(self.web_source_dir, "plugins")
            
            for plugin_name in required_plugins:
                plugin_file = f"{plugin_name.replace('_', '-')}-plugin.js"
                source_path = os.path.join(plugins_source_dir, plugin_file)
                dest_path = os.path.join(plugins_dir, plugin_file)
                
                if os.path.exists(source_path):
                    shutil.copy2(source_path, dest_path)
                    self.deployed_assets.add(plugin_file)
                else:
                    print(f"⚠️  プラグインファイルが見つかりません: {source_path}")
            
            print(f"✅ プラグインファイル配信完了: {len(required_plugins)}個")
            return True
            
        except Exception as e:
            print(f"❌ プラグインファイル配信失敗: {e}")
            return False
    
    def sync_template_assets(self, output_dir: str, template_category: str, template_name: str) -> bool:
        """テンプレート固有アセット(CSS/JS)を配信
        
        Args:
            output_dir: 出力ディレクトリ
            template_category: テンプレートカテゴリ (railway, scroll, typewriter)
            template_name: テンプレート名 (railway_scroll, scroll_role, etc.)
            
        Returns:
            配信成功の可否
        """
        try:
            # 出力先のテンプレートディレクトリ
            template_output_dir = os.path.join(output_dir, "templates", template_category, template_name)
            os.makedirs(template_output_dir, exist_ok=True)
            
            # ソースディレクトリ
            source_template_dir = os.path.join(self.web_source_dir, "templates", template_category, template_name)
            
            if not os.path.exists(source_template_dir):
                print(f"⚠️  テンプレートソースが見つかりません: {source_template_dir}")
                return False
            
            # sc-template.css と sc-template.js をコピー
            for asset_file in ["sc-template.css", "sc-template.js"]:
                source_path = os.path.join(source_template_dir, asset_file)
                if os.path.exists(source_path):
                    dest_path = os.path.join(template_output_dir, asset_file)
                    shutil.copy2(source_path, dest_path)
                    self.deployed_assets.add(f"templates/{template_category}/{template_name}/{asset_file}")
            
            # カテゴリ共通ファイル (sc-base.js) をコピー
            category_base_source = os.path.join(self.web_source_dir, "templates", template_category, "sc-base.js")
            if os.path.exists(category_base_source):
                category_output_dir = os.path.join(output_dir, "templates", template_category)
                os.makedirs(category_output_dir, exist_ok=True)
                dest_path = os.path.join(category_output_dir, "sc-base.js")
                shutil.copy2(category_base_source, dest_path)
                self.deployed_assets.add(f"templates/{template_category}/sc-base.js")
            
            print(f"✅ テンプレートアセット配信完了: {template_category}/{template_name}")
            return True
            
        except Exception as e:
            print(f"❌ テンプレートアセット配信失敗: {e}")
            return False
    
    def create_asset_manifest(self, output_dir: str) -> bool:
        """配信されたアセットのマニフェストファイルを作成
        
        Args:
            output_dir: 出力ディレクトリ
            
        Returns:
            作成成功の可否
        """
        try:
            manifest = {
                "deployed_assets": list(self.deployed_assets),
                "deployment_timestamp": os.path.getctime(output_dir) if os.path.exists(output_dir) else None,
                "total_files": len(self.deployed_assets)
            }
            
            manifest_path = os.path.join(output_dir, "asset-manifest.json")
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            print(f"✅ アセットマニフェスト作成完了: {manifest_path}")
            return True
            
        except Exception as e:
            print(f"❌ マニフェスト作成失敗: {e}")
            return False
    
