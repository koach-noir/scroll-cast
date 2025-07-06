"""
プラグイン型テンプレートシステム
Plugin-based template system for scalable interaction implementation
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json


@dataclass
class PluginConfig:
    """プラグイン設定"""
    name: str
    version: str = "1.0.0"
    dependencies: List[str] = field(default_factory=list)
    config_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemplateConfig:
    """テンプレート設定"""
    template_name: str
    navigation_unit: str  # "sentence", "line", "paragraph"
    required_plugins: List[str] = field(default_factory=list)
    plugin_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """設定をJSON化可能な辞書に変換"""
        return {
            "template_name": self.template_name,
            "navigation_unit": self.navigation_unit,
            "required_plugins": self.required_plugins,
            "plugin_configs": self.plugin_configs
        }


class InteractionPlugin(ABC):
    """インタラクションプラグインの基底クラス"""
    
    def __init__(self, config: PluginConfig):
        self.config = config
        self.name = config.name
        self.dependencies = config.dependencies
    
    @abstractmethod
    def get_javascript_module(self) -> str:
        """JavaScriptモジュールコードを返す"""
        pass
    
    @abstractmethod
    def get_css_styles(self) -> str:
        """CSSスタイルを返す"""
        pass
    
    def validate_dependencies(self, available_plugins: List[str]) -> bool:
        """依存関係の検証"""
        return all(dep in available_plugins for dep in self.dependencies)


class AutoPlayPlugin(InteractionPlugin):
    """シンプル自動再生プラグイン（インタラクション機能なし）"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
    
    def get_javascript_module(self) -> str:
        return """
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
                // タイミングデータからタイムラインイベントを構築
                if (!this.config.timingData) return;
                
                this.config.timingData.forEach((sequenceData, index) => {
                    // 実際のstart_timeを使用（ミリ秒単位）
                    const startTime = sequenceData.start_time || 0;
                    
                    this.timeline.push({
                        time: startTime,
                        type: 'sequence_start',
                        index: index,
                        data: sequenceData
                    });
                });
                
                // 総時間を最後の要素の終了時間で計算
                if (this.config.timingData.length > 0) {
                    const lastSequence = this.config.timingData[this.config.timingData.length - 1];
                    const lastStartTime = lastSequence.start_time || 0;
                    const lastDuration = lastSequence.duration || 8000;
                    this.totalDuration = lastStartTime + lastDuration;
                } else {
                    this.totalDuration = 0;
                }
            },
            
            setupAutoPlay: function() {
                window.addEventListener('load', () => {
                    setTimeout(() => {
                        this.start();
                    }, this.config.initial_delay || 500);
                });
            },
            
            start: function() {
                if (this.timeline.length === 0) return;
                
                this.state.isPlaying = true;
                this.state.startTime = performance.now();
                this.tick();
            },
            
            tick: function() {
                if (!this.state.isPlaying) return;
                
                const currentTime = performance.now();
                this.state.globalTime = currentTime - this.state.startTime;
                
                // タイムラインイベントの処理
                this.processTimelineEvents(this.state.globalTime);
                
                // 継続的な時間更新
                if (this.state.globalTime < this.totalDuration) {
                    requestAnimationFrame(() => this.tick());
                } else {
                    this.state.isPlaying = false;
                    this.dispatchEvent('timeline_complete');
                }
            },
            
            processTimelineEvents: function(currentTime) {
                // 未実行のイベントを検索して実行
                this.timeline.forEach(event => {
                    if (!event.executed && currentTime >= event.time) {
                        event.executed = true;
                        
                        if (event.type === 'sequence_start') {
                            this.dispatchEvent('sequence_start', {
                                index: event.index,
                                data: event.data,
                                globalTime: currentTime
                            });
                        }
                    }
                });
            },
            
            dispatchEvent: function(eventType, detail = {}) {
                window.dispatchEvent(new CustomEvent(eventType, {
                    detail: { ...detail, source: 'auto_play' }
                }));
            },
            
            getState: function() {
                return {
                    ...this.state,
                    progress: this.totalDuration ? this.state.globalTime / this.totalDuration : 0
                };
            }
        };
        """
    
    def get_css_styles(self) -> str:
        return """
        /* Auto Play Plugin Styles */
        .auto-play-indicator {
            position: fixed;
            top: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
            z-index: 1000;
        }
        """


class TypewriterDisplayPlugin(InteractionPlugin):
    """Web Animation API ベースタイプライター表示プラグイン"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
    
    def get_javascript_module(self) -> str:
        return """
        window.TypewriterDisplayPlugin = {
            name: 'typewriter_display',
            
            initialize: function(config) {
                this.config = config;
                this.sentences = document.querySelectorAll('.typewriter-sentence');
                this.currentSentenceIndex = 0;
                this.setupDisplayHandlers();
                this.initializeDisplay();
            },
            
            setupDisplayHandlers: function() {
                // シンプル自動再生イベントのリスナー
                window.addEventListener('sequence_start', (event) => {
                    this.playSequence(event.detail.index, event.detail.data);
                });
            },
            
            initializeDisplay: function() {
                // 全ての文を非表示に初期化
                this.sentences.forEach((sentence, index) => {
                    sentence.classList.remove('active');
                    const chars = sentence.querySelectorAll('.typewriter-char');
                    chars.forEach(char => {
                        char.style.opacity = '0';
                    });
                });
            },
            
            playSequence: function(sequenceIndex, sequenceData) {
                if (sequenceIndex >= this.sentences.length) return;
                
                // 前の文を非表示
                if (this.currentSentenceIndex < this.sentences.length && this.currentSentenceIndex !== sequenceIndex) {
                    this.sentences[this.currentSentenceIndex].classList.remove('active');
                }
                
                // 新しい文を表示
                this.currentSentenceIndex = sequenceIndex;
                const currentSentence = this.sentences[this.currentSentenceIndex];
                if (currentSentence) {
                    currentSentence.classList.add('active');
                    this.animateCharactersWithWebAPI(currentSentence, sequenceData, sequenceIndex);
                }
            },
            
            animateCharactersWithWebAPI: function(sentence, sequenceData, sequenceIndex) {
                const chars = sentence.querySelectorAll('.typewriter-char');
                
                // 既存の文を非表示
                if (this.currentSentenceIndex < this.sentences.length && this.currentSentenceIndex !== sequenceIndex) {
                    this.sentences[this.currentSentenceIndex].classList.remove('active');
                }
                
                if (!sequenceData.chars) return;
                
                // 各文字のWeb Animation API アニメーションを作成
                sequenceData.chars.forEach((charTiming, charIndex) => {
                    if (charIndex >= chars.length) return;
                    
                    const char = chars[charIndex];
                    const animationId = `sentence-${sequenceIndex}-char-${charIndex}`;
                    
                    // 初期状態を設定
                    char.style.opacity = '0';
                    
                    // Web Animation API でアニメーション作成
                    const animation = char.animate([
                        { opacity: 0, offset: 0 },
                        { opacity: 1, offset: 1 }
                    ], {
                        duration: charTiming.fade_duration || 200,
                        delay: charTiming.start || 0,
                        fill: 'forwards',
                        easing: 'ease-in-out'
                    });
                    
                    // アニメーションのシンプル管理
                    
                    // アニメーション完了後の処理
                    animation.addEventListener('finish', () => {
                        char.style.opacity = '1';
                        char.classList.add('visible');
                    });
                });
            }
        };
        """
    
    def get_css_styles(self) -> str:
        return """
        /* Typewriter Display Plugin Styles */
        .typewriter-container {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-weight: bold;
            text-align: center;
            width: 90%;
            max-width: 400px;
            line-height: 1.4;
        }
        
        .typewriter-sentence {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            white-space: normal;
            word-wrap: break-word;
            max-width: 100%;
            opacity: 1;
            display: none;
        }
        
        .typewriter-sentence.active {
            display: block;
        }
        
        .typewriter-char {
            opacity: 0;
        }
        
        .typewriter-char.visible {
            opacity: 1;
        }
        """


class SimpleRoleDisplayPlugin(InteractionPlugin):
    """シンプルロール表示プラグイン（映画エンドロール風）"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
    
    def get_javascript_module(self) -> str:
        return """
        window.SimpleRoleDisplayPlugin = {
            name: 'simple_role_display',
            
            initialize: function(config) {
                this.config = config;
                this.state = {
                    currentLine: 0,
                    isDisplaying: false
                };
                this.totalLines = 0;
                this.setupDisplay();
                this.setupEventListeners();
            },
            
            setupDisplay: function() {
                // 行要素を取得
                this.lineElements = document.querySelectorAll('.text-line');
                this.totalLines = this.lineElements.length;
                
                // 初期状態で全ての行を非表示
                this.lineElements.forEach(line => {
                    line.style.display = 'none';
                });
                
                // コンテナの設定
                const container = document.querySelector('.role-container');
                if (container) {
                    container.style.overflow = 'hidden';
                    container.style.height = '100vh';
                }
            },
            
            setupEventListeners: function() {
                // シンプル自動再生イベント
                window.addEventListener('sequence_start', (event) => {
                    this.showLine(event.detail.index);
                });
            },
            
            showLine: function(lineIndex) {
                if (lineIndex < 0 || lineIndex >= this.totalLines) return;
                
                console.log(`[SimpleRole] Showing line ${lineIndex}:`, this.lineElements[lineIndex]?.textContent);
                
                // 前の行は隠さない（連続表示）
                
                // 新しい行を表示
                const currentLine = this.lineElements[lineIndex];
                if (currentLine) {
                    currentLine.style.display = 'block';
                    currentLine.style.position = 'fixed';
                    currentLine.style.left = '50%';
                    currentLine.style.zIndex = '100';
                    
                    // エンドロール風アニメーション（連続表示）
                    currentLine.style.transform = 'translate(-50%, 0) translateY(100vh)';
                    currentLine.style.opacity = '1';
                    
                    // アニメーション開始
                    setTimeout(() => {
                        currentLine.style.transition = 'transform 8s linear';
                        currentLine.style.transform = 'translate(-50%, 0) translateY(-100vh)';
                        
                        // 画面を完全に通過した後に非表示
                        setTimeout(() => {
                            currentLine.style.display = 'none';
                            currentLine.style.transition = '';
                            currentLine.style.transform = '';
                        }, 8000);
                    }, 50);
                }
                
                this.state.currentLine = lineIndex;
            },
            
            getState: function() {
                return {
                    currentLine: this.state.currentLine,
                    totalLines: this.totalLines,
                    isDisplaying: this.state.isDisplaying
                };
            }
        };
        """
    
    def get_css_styles(self) -> str:
        return """
        /* Simple Role Display Plugin Styles */
        .role-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            z-index: 10;
        }
        
        .text-line {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            white-space: nowrap;
            font-weight: bold;
            text-align: center;
            font-size: 3vw;
            color: #ffffff;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
            display: none;
            z-index: 11;
        }
        
        /* デスクトップ表示での固定サイズ */
        @media (min-width: 768px) {
            .text-line {
                font-size: 36px;
            }
        }
        """


# FloatingTimeJoystickPlugin removed for simple text flow


class PluginRegistry:
    """プラグイン登録・管理システム"""
    
    def __init__(self):
        self.plugins: Dict[str, InteractionPlugin] = {}
    
    def register_plugin(self, plugin: InteractionPlugin):
        """プラグインを登録"""
        self.plugins[plugin.name] = plugin
    
    def get_plugin(self, name: str) -> Optional[InteractionPlugin]:
        """プラグインを取得"""
        return self.plugins.get(name)
    
    def get_available_plugins(self) -> List[str]:
        """利用可能なプラグイン名一覧"""
        return list(self.plugins.keys())


class RailwayDisplayPlugin(InteractionPlugin):
    """Web Animation API ベース鉄道方向幕風表示プラグイン"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
    
    def get_javascript_module(self) -> str:
        return """
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
                // シンプル自動再生イベントのリスナー
                window.addEventListener('sequence_start', (event) => {
                    this.playSequence(event.detail.index, event.detail.data);
                });
            },
            
            initializeDisplay: function() {
                // 全ての行を初期状態にリセット
                this.lines.forEach(line => {
                    line.className = 'text-line';
                    // 初期位置: 下
                    line.style.transform = 'translate(-50%, -50%) translateY(100px)';
                    line.style.opacity = '0';
                });
            },
            
            playSequence: function(sequenceIndex, sequenceData) {
                if (sequenceIndex >= this.lines.length) return;
                
                // 現在の行を取得
                this.currentLineIndex = sequenceIndex;
                const currentLine = this.lines[this.currentLineIndex];
                if (!currentLine) return;
                
                // Railway scroll 3段階アニメーション (Web Animation API)
                this.animateRailwayLineWithWebAPI(currentLine, sequenceData, sequenceIndex);
            },
            
            animateRailwayLineWithWebAPI: function(line, sequenceData, sequenceIndex) {
                // シンプルアニメーション実行
                
                // 3段階のアニメーションを作成
                const phases = this.createRailwayAnimationPhases(line, sequenceData, sequenceIndex);
                
                // 各フェーズを順次実行
                phases.forEach(phase => {
                    const animationId = `line-${sequenceIndex}-${phase.name}`;
                    const animation = line.animate(phase.keyframes, phase.options);
                    
                    // シンプルアニメーション実行
                    
                    // フェーズ完了時の処理
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
                    // Phase 1: フェードイン (下→中央)
                    {
                        name: 'fade-in',
                        keyframes: [
                            { 
                                opacity: 0, 
                                transform: 'translate(-50%, -50%) translateY(100px)',
                                offset: 0 
                            },
                            { 
                                opacity: 1, 
                                transform: 'translate(-50%, -50%) translateY(0px)',
                                offset: 1 
                            }
                        ],
                        options: {
                            duration: fadeInDuration,
                            delay: fadeInStart,
                            fill: 'forwards',
                            easing: 'ease-in-out'
                        },
                        onFinish: (line) => {
                            line.style.opacity = '1';
                            line.style.transform = 'translate(-50%, -50%) translateY(0px)';
                        }
                    },
                    
                    // Phase 2: 静止表示 (中央)
                    {
                        name: 'static',
                        keyframes: [
                            { 
                                opacity: 1, 
                                transform: 'translate(-50%, -50%) translateY(0px)',
                                offset: 0 
                            },
                            { 
                                opacity: 1, 
                                transform: 'translate(-50%, -50%) translateY(0px)',
                                offset: 1 
                            }
                        ],
                        options: {
                            duration: staticDuration,
                            delay: staticStart,
                            fill: 'forwards',
                            easing: 'linear'
                        }
                    },
                    
                    // Phase 3: フェードアウト (中央→上)
                    {
                        name: 'fade-out',
                        keyframes: [
                            { 
                                opacity: 1, 
                                transform: 'translate(-50%, -50%) translateY(0px)',
                                offset: 0 
                            },
                            { 
                                opacity: 0, 
                                transform: 'translate(-50%, -50%) translateY(-100px)',
                                offset: 1 
                            }
                        ],
                        options: {
                            duration: fadeOutDuration,
                            delay: fadeOutStart,
                            fill: 'forwards',
                            easing: 'ease-in-out'
                        },
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
    
    def get_css_styles(self) -> str:
        return """
        /* Railway Display Plugin Styles */
        .railway-container {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-weight: bold;
            text-align: center;
            width: 90%;
            max-width: 400px;
            line-height: 1.4;
            height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .text-line {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) translateY(100px);  /* 初期位置: 下 */
            white-space: normal;
            word-wrap: break-word;
            max-width: 100%;
            opacity: 0;
            transition: all 0.8s ease-in-out;
        }
        
        /* Railway scroll phases */
        .text-line.fade-in {
            opacity: 1;
            transform: translate(-50%, -50%) translateY(0px);   /* 下→中央 */
        }
        
        .text-line.static {
            opacity: 1;
            transform: translate(-50%, -50%) translateY(0px);   /* 中央で静止 */
        }
        
        .text-line.fade-out {
            opacity: 0;
            transform: translate(-50%, -50%) translateY(-100px); /* 中央→上 */
        }
        """


class TemplateComposer:
    """プラグインを組み合わせてテンプレートを構築"""
    
    def __init__(self):
        self.plugin_registry = PluginRegistry()
        self._register_default_plugins()
    
    def _register_default_plugins(self):
        """デフォルトプラグインを登録（シンプルテキストフロー版）"""
        auto_play_config = PluginConfig(name="auto_play", dependencies=[])
        typewriter_config = PluginConfig(name="typewriter_display", dependencies=["auto_play"])
        railway_config = PluginConfig(name="railway_display", dependencies=["auto_play"])
        simple_role_config = PluginConfig(name="simple_role_display", dependencies=["auto_play"])
        
        self.plugin_registry.register_plugin(AutoPlayPlugin(auto_play_config))
        self.plugin_registry.register_plugin(TypewriterDisplayPlugin(typewriter_config))
        self.plugin_registry.register_plugin(RailwayDisplayPlugin(railway_config))
        self.plugin_registry.register_plugin(SimpleRoleDisplayPlugin(simple_role_config))
    
    def compose_template(self, template_config: TemplateConfig, timing_data: str) -> Dict[str, str]:
        """設定に基づいてプラグインを組み立て"""
        
        # 必要なプラグインを取得
        required_plugins = []
        for plugin_name in template_config.required_plugins:
            plugin = self.plugin_registry.get_plugin(plugin_name)
            if plugin:
                required_plugins.append(plugin)
            else:
                raise ValueError(f"Required plugin '{plugin_name}' not found")
        
        # 依存関係の検証
        available_plugin_names = [p.name for p in required_plugins]
        for plugin in required_plugins:
            if not plugin.validate_dependencies(available_plugin_names):
                raise ValueError(f"Plugin '{plugin.name}' dependencies not satisfied")
        
        # JavaScript/CSSを統合
        composed_js = self._compose_javascript_modules(required_plugins, template_config, timing_data)
        composed_css = self._compose_css_modules(required_plugins, template_config)
        
        return {
            "javascript": composed_js,
            "css": composed_css
        }
    
    def _compose_javascript_modules(self, plugins: List[InteractionPlugin], 
                                   config: TemplateConfig, timing_data: str) -> str:
        """JavaScriptモジュールを統合"""
        modules = []
        
        # 共有ライブラリに含まれるプラグインをスキップ（シンプル版はインタラクションなし）
        shared_plugins = ['auto_play']
        
        # プラグインモジュール（共有プラグイン以外のみ）
        for plugin in plugins:
            if plugin.name not in shared_plugins:
                modules.append(f"// {plugin.name} Plugin")
                modules.append(plugin.get_javascript_module())
        
        # 統合レイヤー
        integration_layer = f"""
        // Template Integration Layer
        document.addEventListener('DOMContentLoaded', function() {{
            // タイミングデータ
            const timingData = {timing_data};
            
            // テンプレート設定
            const templateConfig = {json.dumps(config.to_dict())};
            templateConfig.timingData = timingData;
            
            // プラグイン初期化
            {self._generate_plugin_initialization(plugins, config)}
            
            // グローバルコントローラー
            window.TemplateController = {{
                config: templateConfig,
                plugins: {{
                    {', '.join([f'{p.name}: window.{self._get_plugin_global_name(p)}' for p in plugins])}
                }}
            }};
        }});
        """
        
        modules.append(integration_layer)
        return "\n\n".join(modules)
    
    def _compose_css_modules(self, plugins: List[InteractionPlugin], 
                           config: TemplateConfig) -> str:
        """CSSモジュールを統合"""
        css_modules = []
        
        # 共有ライブラリに含まれるプラグインをスキップ（シンプル版はインタラクションなし）
        shared_plugins = ['auto_play']
        
        for plugin in plugins:
            if plugin.name not in shared_plugins:
                css_modules.append(f"/* {plugin.name} Plugin Styles */")
                css_modules.append(plugin.get_css_styles())
        
        return "\n\n".join(css_modules)
    
    def _generate_plugin_initialization(self, plugins: List[InteractionPlugin], 
                                      config: TemplateConfig) -> str:
        """プラグイン初期化コードを生成"""
        init_code = []
        
        for plugin in plugins:
            global_name = self._get_plugin_global_name(plugin)
            plugin_config = config.plugin_configs.get(plugin.name, {})
            
            init_code.append(f"""
            if (window.{global_name}) {{
                window.{global_name}.initialize({{
                    ...templateConfig,
                    ...{json.dumps(plugin_config)}
                }});
            }}""")
        
        return "\n".join(init_code)
    
    def _get_plugin_global_name(self, plugin: InteractionPlugin) -> str:
        """プラグインのグローバル変数名を取得"""
        # auto_play -> AutoPlayPlugin
        return f"{''.join(word.capitalize() for word in plugin.name.split('_'))}Plugin"