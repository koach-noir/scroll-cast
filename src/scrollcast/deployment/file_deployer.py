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
    
    def __init__(self, template_source_dir: str = "src/templates"):
        """
        Args:
            template_source_dir: テンプレートソースディレクトリのパス
        """
        self.template_source_dir = template_source_dir
        self.deployed_assets: Set[str] = set()
        
    def deploy_shared_assets(self, output_dir: str) -> bool:
        """共通ライブラリファイルを配信
        
        Args:
            output_dir: 出力ディレクトリ (例: contents/html)
            
        Returns:
            配信成功の可否
        """
        try:
            shared_dir = os.path.join(output_dir, "shared")
            os.makedirs(shared_dir, exist_ok=True)
            
            # 既存のscrollcast-styles.cssは保持
            styles_path = os.path.join(shared_dir, "scrollcast-styles.css")
            if not os.path.exists(styles_path):
                # assetsからコピー（存在する場合）
                source_styles = os.path.join("assets", "scrollcast-styles.css")
                if os.path.exists(source_styles):
                    shutil.copy2(source_styles, styles_path)
            
            # scrollcast-core.js を生成（軽量コア）
            core_js_content = self._generate_core_js()
            core_js_path = os.path.join(shared_dir, "scrollcast-core.js")
            with open(core_js_path, 'w', encoding='utf-8') as f:
                f.write(core_js_content)
            
            self.deployed_assets.add("scrollcast-core.js")
            
            print(f"✅ 共通アセット配信完了: {shared_dir}")
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
            assets_dir = os.path.join(output_dir, "assets")
            os.makedirs(assets_dir, exist_ok=True)
            
            for plugin_name in required_plugins:
                plugin_content = self._get_plugin_javascript(plugin_name)
                if plugin_content:
                    plugin_file = f"{plugin_name.replace('_', '-')}-plugin.js"
                    plugin_path = os.path.join(assets_dir, plugin_file)
                    
                    with open(plugin_path, 'w', encoding='utf-8') as f:
                        f.write(plugin_content)
                    
                    self.deployed_assets.add(plugin_file)
            
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
            source_template_dir = os.path.join(self.template_source_dir, template_category, template_name)
            
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
            category_base_source = os.path.join(self.template_source_dir, template_category, "sc-base.js")
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
    
    def _generate_core_js(self) -> str:
        """軽量なScrollCastコアJavaScriptを生成"""
        return """/*
 * ScrollCast Core Library
 * 軽量なコアライブラリ - プラグインシステム基盤
 */

window.ScrollCastCore = {
    version: '2.0.0',
    plugins: {},
    
    registerPlugin: function(name, plugin) {
        this.plugins[name] = plugin;
        console.log(`[ScrollCast] Plugin registered: ${name}`);
    },
    
    initializePlugins: function(config) {
        for (const pluginName of config.required_plugins || []) {
            const plugin = this.plugins[pluginName] || window[this._getPluginGlobalName(pluginName)];
            if (plugin && plugin.initialize) {
                try {
                    plugin.initialize({
                        ...config,
                        ...config.plugin_configs[pluginName]
                    });
                    console.log(`[ScrollCast] Plugin initialized: ${pluginName}`);
                } catch (error) {
                    console.error(`[ScrollCast] Plugin initialization failed: ${pluginName}`, error);
                }
            } else {
                console.warn(`[ScrollCast] Plugin not found: ${pluginName}`);
            }
        }
    },
    
    _getPluginGlobalName: function(pluginName) {
        // auto_play -> AutoPlayPlugin
        return pluginName.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join('') + 'Plugin';
    }
};

// Global utility functions
window.dispatchSequenceEvent = function(eventType, data) {
    window.dispatchEvent(new CustomEvent(eventType, { detail: data }));
};
"""
    
    def _get_plugin_javascript(self, plugin_name: str) -> Optional[str]:
        """プラグイン名に対応するJavaScriptコードを取得"""
        plugins = {
            "auto_play": self._get_auto_play_plugin_js(),
            "railway_display": self._get_railway_display_plugin_js(),
            "simple_role_display": self._get_simple_role_display_plugin_js(),
            "typewriter_display": self._get_typewriter_display_plugin_js()
        }
        
        return plugins.get(plugin_name)
    
    def _get_auto_play_plugin_js(self) -> str:
        """AutoPlayプラグインのJavaScriptコード"""
        return """/*
 * ScrollCast Auto Play Plugin
 * 自動再生機能プラグイン
 */

window.AutoPlayPlugin = {
    name: 'auto_play',
    
    initialize: function(config) {
        this.config = config;
        this.state = {
            isPlaying: false,
            globalTime: 0,
            startTime: null
        };
        this.timeline = [];
        this.setupTimeline();
        this.setupAutoPlay();
    },
    
    setupTimeline: function() {
        if (!this.config.timingData) return;
        
        this.config.timingData.forEach((sequenceData, index) => {
            const startTime = sequenceData.start_time || 0;
            
            this.timeline.push({
                time: startTime,
                type: 'sequence_start',
                index: index,
                data: sequenceData
            });
        });
        
        this.timeline.sort((a, b) => a.time - b.time);
    },
    
    setupAutoPlay: function() {
        const initialDelay = this.config.initial_delay || 1000;
        
        if (this.config.auto_start) {
            setTimeout(() => {
                this.startPlayback();
            }, initialDelay);
        }
        
        document.addEventListener('click', () => {
            if (this.state.isPlaying) {
                this.pausePlayback();
            } else {
                this.startPlayback();
            }
        });
    },
    
    startPlayback: function() {
        if (this.state.isPlaying) return;
        
        this.state.isPlaying = true;
        this.state.startTime = Date.now() - this.state.globalTime;
        this.updateLoop();
    },
    
    pausePlayback: function() {
        this.state.isPlaying = false;
    },
    
    updateLoop: function() {
        if (!this.state.isPlaying) return;
        
        this.state.globalTime = Date.now() - this.state.startTime;
        
        this.timeline.forEach(event => {
            if (event.time <= this.state.globalTime && !event.triggered) {
                event.triggered = true;
                window.dispatchEvent(new CustomEvent(event.type, {
                    detail: { index: event.index, data: event.data }
                }));
            }
        });
        
        requestAnimationFrame(() => this.updateLoop());
    }
};
"""
    
    def _get_railway_display_plugin_js(self) -> str:
        """Railway Displayプラグインのコード"""
        return """/*
 * ScrollCast Railway Display Plugin
 * 鉄道方向幕風表示プラグイン
 */

window.RailwayDisplayPlugin = {
    name: 'railway_display',
    
    initialize: function(config) {
        this.config = config;
        this.lines = document.querySelectorAll('.text-line');
        this.currentLineIndex = 0;
        this.activeAnimations = new Map();
        this.setupDisplayHandlers();
        this.initializeDisplay();
    },
    
    setupDisplayHandlers: function() {
        window.addEventListener('sequence_start', (event) => {
            this.playSequence(event.detail.index, event.detail.data);
        });
    },
    
    initializeDisplay: function() {
        this.lines.forEach(line => {
            line.className = 'text-line';
            line.style.transform = 'translate(-50%, -50%) translateY(100px)';
            line.style.opacity = '0';
        });
    },
    
    playSequence: function(sequenceIndex, sequenceData) {
        if (sequenceIndex >= this.lines.length) return;
        
        this.currentLineIndex = sequenceIndex;
        const currentLine = this.lines[this.currentLineIndex];
        if (!currentLine) return;
        
        this.animateRailwayLineWithWebAPI(currentLine, sequenceData, sequenceIndex);
    },
    
    animateRailwayLineWithWebAPI: function(line, sequenceData, sequenceIndex) {
        const phases = this.createRailwayAnimationPhases(line, sequenceData, sequenceIndex);
        
        phases.forEach(phase => {
            const animation = line.animate(phase.keyframes, phase.options);
            
            animation.addEventListener('finish', () => {
                if (phase.onFinish) {
                    phase.onFinish(line);
                }
            });
        });
    },
    
    createRailwayAnimationPhases: function(line, sequenceData, sequenceIndex) {
        const fadeInDuration = sequenceData.fade_in_duration || 800;
        const staticDuration = sequenceData.static_duration || 2000;
        const fadeOutDuration = sequenceData.fade_out_duration || 800;
        const fadeInStart = sequenceData.fade_in_start || 0;
        const staticStart = sequenceData.static_start || fadeInDuration;
        const fadeOutStart = sequenceData.fade_out_start || (staticStart + staticDuration);
        
        return [
            {
                name: 'fade-in',
                keyframes: [
                    { opacity: 0, transform: 'translate(-50%, -50%) translateY(100px)', offset: 0 },
                    { opacity: 1, transform: 'translate(-50%, -50%) translateY(0px)', offset: 1 }
                ],
                options: { duration: fadeInDuration, delay: fadeInStart, fill: 'forwards', easing: 'ease-in-out' },
                onFinish: (line) => {
                    line.style.opacity = '1';
                    line.style.transform = 'translate(-50%, -50%) translateY(0px)';
                }
            },
            {
                name: 'static',
                keyframes: [
                    { opacity: 1, transform: 'translate(-50%, -50%) translateY(0px)', offset: 0 },
                    { opacity: 1, transform: 'translate(-50%, -50%) translateY(0px)', offset: 1 }
                ],
                options: { duration: staticDuration, delay: staticStart, fill: 'forwards', easing: 'linear' }
            },
            {
                name: 'fade-out',
                keyframes: [
                    { opacity: 1, transform: 'translate(-50%, -50%) translateY(0px)', offset: 0 },
                    { opacity: 0, transform: 'translate(-50%, -50%) translateY(-100px)', offset: 1 }
                ],
                options: { duration: fadeOutDuration, delay: fadeOutStart, fill: 'forwards', easing: 'ease-in-out' },
                onFinish: (line) => {
                    line.style.opacity = '0';
                    line.style.transform = 'translate(-50%, -50%) translateY(100px)';
                    line.className = 'text-line';
                }
            }
        ];
    }
};
"""
    
    def _get_simple_role_display_plugin_js(self) -> str:
        """Simple Role Displayプラグインのコード"""
        return """/*
 * ScrollCast Simple Role Display Plugin  
 * シンプルロール（エンドロール風）表示プラグイン
 */

window.SimpleRoleDisplayPlugin = {
    name: 'simple_role_display',
    
    initialize: function(config) {
        this.config = config;
        this.lines = document.querySelectorAll('.text-line');
        this.setupDisplayHandlers();
        this.initializeDisplay();
    },
    
    setupDisplayHandlers: function() {
        window.addEventListener('sequence_start', (event) => {
            this.playSequence(event.detail.index, event.detail.data);
        });
    },
    
    initializeDisplay: function() {
        this.lines.forEach(line => {
            line.style.opacity = '0';
            line.style.transform = 'translateY(100vh)';
        });
    },
    
    playSequence: function(sequenceIndex, sequenceData) {
        if (sequenceIndex >= this.lines.length) return;
        
        const line = this.lines[sequenceIndex];
        if (!line) return;
        
        this.animateScrollLine(line, sequenceData);
    },
    
    animateScrollLine: function(line, sequenceData) {
        const duration = sequenceData.duration || 8000;
        
        line.style.display = 'block';
        line.style.position = 'fixed';
        line.style.left = '50%';
        line.style.top = '50%';
        line.style.zIndex = '100';
        line.style.transform = 'translate(-50%, -50%) translateY(100vh)';
        line.style.opacity = '1';
        
        // エンドロール風アニメーション開始
        setTimeout(() => {
            line.style.transition = 'transform 8s linear';
            line.style.transform = 'translate(-50%, -50%) translateY(-100vh)';
            
            // 画面を完全に通過した後に非表示
            setTimeout(() => {
                line.style.display = 'none';
                line.style.transition = '';
                line.style.transform = '';
            }, 8000);
        }, 50);
    }
};
"""
    
    def _get_typewriter_display_plugin_js(self) -> str:
        """Typewriter Displayプラグインのコード"""
        return """/*
 * ScrollCast Typewriter Display Plugin
 * タイプライター表示プラグイン  
 */

window.TypewriterDisplayPlugin = {
    name: 'typewriter_display',
    
    initialize: function(config) {
        console.log('[DEBUG] TypewriterDisplayPlugin.initialize() called with config:', config);
        this.config = config;
        this.sentences = document.querySelectorAll('.text-container[data-template="typewriter"] .text-sentence, .text-container[data-template="typewriter"] .typewriter-sentence, .typewriter-sentence');
        console.log('[DEBUG] Found', this.sentences.length, 'sentence elements');
        this.setupDisplayHandlers();
        this.initializeDisplay();
        console.log('[DEBUG] TypewriterDisplayPlugin initialization complete');
    },
    
    setupDisplayHandlers: function() {
        console.log('[DEBUG] setupDisplayHandlers() called');
        window.addEventListener('sequence_start', (event) => {
            console.log('[DEBUG] sequence_start event received:', event.detail);
            this.playSequence(event.detail.index, event.detail.data);
        });
        console.log('[DEBUG] Event listeners set up');
    },
    
    initializeDisplay: function() {
        this.sentences.forEach(sentence => {
            sentence.style.display = 'none';
            const chars = sentence.querySelectorAll('.text-char, .typewriter-char');
            chars.forEach(char => {
                char.style.opacity = '0';
                char.style.transform = 'scale(0.8)';
            });
        });
    },
    
    playSequence: function(sequenceIndex, sequenceData) {
        console.log('[DEBUG] playSequence() called with index:', sequenceIndex);
        if (sequenceIndex >= this.sentences.length) {
            console.log('[DEBUG] Invalid sequence index:', sequenceIndex, 'total sentences:', this.sentences.length);
            return;
        }
        
        const sentence = this.sentences[sequenceIndex];
        if (!sentence) {
            console.log('[DEBUG] No sentence element found at index:', sequenceIndex);
            return;
        }
        
        console.log('[DEBUG] Animating sentence:', sentence.textContent);
        this.animateTypewriter(sentence, sequenceData);
    },
    
    animateTypewriter: function(sentence, sequenceData) {
        console.log('[DEBUG] Starting typewriter animation for sentence:', sentence.textContent);
        console.log('[DEBUG] Full sequenceData:', sequenceData);
        
        // Clear all previous sentences before starting new one
        this.clearPreviousSentences(sentence);
        
        sentence.style.display = 'block';
        sentence.classList.add('active');
        
        const chars = sentence.querySelectorAll('.typewriter-char');
        const characterTimings = sequenceData.character_timings || sequenceData.chars || [];
        
        console.log('[DEBUG] Found', chars.length, 'characters, timings length:', characterTimings.length);
        console.log('[DEBUG] Character timings:', characterTimings);
        
        characterTimings.forEach((timing, index) => {
            if (index < chars.length) {
                const delay = timing.start || timing.fade_start_ms || index * 100;
                console.log('[DEBUG] Setting timeout for char', index, 'at', delay, 'ms');
                setTimeout(() => {
                    chars[index].style.opacity = '1';
                    chars[index].style.transform = 'scale(1)';
                    chars[index].classList.add('visible');
                    console.log('[DEBUG] Character', index, 'displayed:', chars[index].textContent);
                }, delay);
            }
        });
    },
    
    clearPreviousSentences: function(currentSentence) {
        console.log('[DEBUG] Clearing previous sentences');
        this.sentences.forEach(sentence => {
            if (sentence !== currentSentence) {
                sentence.style.display = 'none';
                sentence.classList.remove('active');
                const chars = sentence.querySelectorAll('.text-char, .typewriter-char');
                chars.forEach(char => {
                    char.style.opacity = '0';
                    char.style.transform = 'scale(0.8)';
                    char.classList.remove('visible');
                });
            }
        });
    }
};
"""