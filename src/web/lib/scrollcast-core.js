/*
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