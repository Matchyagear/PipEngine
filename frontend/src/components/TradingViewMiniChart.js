import React, { useEffect, useMemo, useRef } from 'react';

// Lightweight wrapper that embeds TradingView's Mini Symbol Overview widget
// Docs: https://www.tradingview.com/widget/mini-symbol-overview/
// Usage: <TradingViewMiniChart symbol="AAPL" height={80} />
const TradingViewMiniChart = ({ symbol, height = 52, dateRange = '1D', theme = 'dark', scale = 1 }) => {
    const containerRef = useRef(null);

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
        // Hide extras for minimal footprint
        // No explicit settings needed; widget is minimal by default
    }), [symbol, height, dateRange, theme]);

    useEffect(() => {
        if (!containerRef.current) return;
        // Clear previous widget instance if any
        containerRef.current.innerHTML = '';

        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js';
        script.async = true;
        script.innerHTML = JSON.stringify(config);

        containerRef.current.appendChild(script);

        return () => {
            if (containerRef.current) {
                containerRef.current.innerHTML = '';
            }
        };
    }, [config]);

    return (
        <div className="w-full overflow-hidden rounded" style={{ height }}>
            <div style={{ transform: `scale(${scale})`, transformOrigin: 'top left' }}>
                <div ref={containerRef} style={{ width: '100%', height: internalHeight }} />
            </div>
        </div>
    );
};

export default TradingViewMiniChart;
