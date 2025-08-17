import React, { useEffect, useMemo, useRef, useState } from 'react';

// Global script loading state to prevent duplicate script loads
let tradingViewScriptLoaded = false;
let tradingViewScriptLoading = false;
const tradingViewLoadPromise = (() => {
    let resolvePromise;
    const promise = new Promise((resolve) => {
        resolvePromise = resolve;
    });
    promise.resolve = resolvePromise;
    return promise;
})();

// Lightweight wrapper that embeds TradingView's Mini Symbol Overview widget
// Enhanced with error handling and script loading management
const TradingViewMiniChart = ({ symbol, height = 52, dateRange = '1D', theme = 'dark', scale = 1 }) => {
    console.log('🧪 TradingViewMiniChart: Rendering widget for', symbol);
    const containerRef = useRef(null);
    const [isReady, setIsReady] = useState(false);
    const [hasError, setHasError] = useState(false);
    const mountedRef = useRef(true);

    // Render the widget at a larger internal height, then scale down to target height
    const internalHeight = Math.max(40, Math.round(height / Math.max(0.1, scale)));

    const config = useMemo(() => ({
        symbol: (symbol || 'AAPL').toUpperCase(),
        width: '100%',
        height: internalHeight,
        locale: 'en',
        dateRange,
        colorTheme: theme,
        isTransparent: true,
        autosize: true,
        // Optional fine-tuning colors
        trendLineColor: '#22c55e',
        underLineColor: theme === 'dark' ? 'rgba(34,197,94,0.12)' : 'rgba(34,197,94,0.15)',
        lineColor: '#22c55e',
    }), [symbol, internalHeight, dateRange, theme]);

    // Function to load TradingView script once globally
    const loadTradingViewScript = () => {
        if (tradingViewScriptLoaded) {
            return Promise.resolve();
        }

        if (tradingViewScriptLoading) {
            return tradingViewLoadPromise;
        }

        tradingViewScriptLoading = true;

        return new Promise((resolve, reject) => {
            // Check if script already exists
            const existingScript = document.querySelector('script[src*="tradingview.com"]');
            if (existingScript) {
                tradingViewScriptLoaded = true;
                tradingViewLoadPromise.resolve();
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.type = 'text/javascript';
            script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js';
            script.async = true;

            script.onload = () => {
                console.log('🧪 TradingView: External script loaded successfully');
                tradingViewScriptLoaded = true;
                tradingViewLoadPromise.resolve();
                resolve();
            };

            script.onerror = () => {
                console.warn('🧪 TradingView: Failed to load external script');
                tradingViewScriptLoading = false;
                reject(new Error('Failed to load TradingView script'));
            };

            // Add error handling for cross-origin issues
            window.addEventListener('error', (event) => {
                if (event.filename && event.filename.includes('tradingview')) {
                    // Suppress TradingView script errors in console
                    event.preventDefault();
                    return false;
                }
            });

            document.head.appendChild(script);
        });
    };

    useEffect(() => {
        mountedRef.current = true;

        const initializeWidget = async () => {
            if (!containerRef.current || !mountedRef.current) return;

            try {
                setHasError(false);

                // Load TradingView script first
                await loadTradingViewScript();

                if (!mountedRef.current) return;

                // Clear previous widget instance
                if (containerRef.current) {
                    containerRef.current.innerHTML = '';
                }

                // Create widget container with delay to ensure script is ready
                setTimeout(() => {
                    if (!containerRef.current || !mountedRef.current) return;

                    try {
                        const widgetScript = document.createElement('script');
                        widgetScript.type = 'text/javascript';
                        widgetScript.innerHTML = JSON.stringify(config);

                        // Create widget container div
                        const widgetDiv = document.createElement('div');
                        widgetDiv.className = 'tradingview-widget-container';

                        widgetDiv.appendChild(widgetScript);
                        containerRef.current.appendChild(widgetDiv);

                        if (mountedRef.current) {
                            setIsReady(true);
                        }
                    } catch (error) {
                        console.warn('TradingView widget creation error:', error);
                        if (mountedRef.current) {
                            setHasError(true);
                        }
                    }
                }, 100);

            } catch (error) {
                console.warn('TradingView script loading error:', error);
                if (mountedRef.current) {
                    setHasError(true);
                }
            }
        };

        initializeWidget();

        return () => {
            mountedRef.current = false;
            if (containerRef.current) {
                try {
                    containerRef.current.innerHTML = '';
                } catch (error) {
                    // Silently handle cleanup errors
                }
            }
        };
    }, [config]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            mountedRef.current = false;
        };
    }, []);

    if (hasError) {
        return (
            <div className="w-full flex items-center justify-center bg-gray-800/20 border border-gray-700 rounded" style={{ height }}>
                <div className="text-center text-gray-500 text-xs">
                    <div className="mb-1">📈</div>
                    <div>{symbol}</div>
                </div>
            </div>
        );
    }

    if (!isReady) {
        return (
            <div className="w-full flex items-center justify-center bg-gray-800/20 border border-gray-700 rounded" style={{ height }}>
                <div className="text-center text-gray-500 text-xs">
                    <div className="animate-pulse mb-1">📊</div>
                    <div>Loading...</div>
                </div>
            </div>
        );
    }

    return (
        <div className="w-full overflow-hidden rounded" style={{ height }}>
            <div style={{ transform: `scale(${scale})`, transformOrigin: 'top left' }}>
                <div ref={containerRef} style={{ width: '100%', height: internalHeight }} />
            </div>
        </div>
    );
};

export default TradingViewMiniChart;
