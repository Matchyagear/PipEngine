import React, { useEffect, useRef } from 'react';

const TradingViewMiniWidget = ({ symbol = 'NASDAQ:AAPL', height = '100%', width = '100%' }) => {
    const containerRef = useRef(null);

    useEffect(() => {
        if (!containerRef.current) return;

        // Clear any existing content
        containerRef.current.innerHTML = '';

        // Create the exact structure from TradingView
        const widgetContainer = document.createElement('div');
        widgetContainer.className = 'tradingview-widget-container';
        widgetContainer.style.height = typeof height === 'number' ? `${height}px` : height;
        widgetContainer.style.width = typeof width === 'number' ? `${width}px` : width;

        // Widget content div
        const widgetDiv = document.createElement('div');
        widgetDiv.className = 'tradingview-widget-container__widget';

        // Copyright div
        const copyrightDiv = document.createElement('div');
        copyrightDiv.className = 'tradingview-widget-copyright';
        copyrightDiv.innerHTML = `<a href="https://www.tradingview.com/symbols/${symbol}/" rel="noopener nofollow" target="_blank"><span class="blue-text">${symbol} chart by TradingView</span></a>`;

        // Script with configuration
        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js';
        script.async = true;

        // Configuration object - optimized for container sizing
        const config = {
            "symbol": symbol,
            "chartOnly": false,
            "dateRange": "1D",
            "noTimeScale": false,
            "colorTheme": "dark",
            "isTransparent": false,
            "locale": "en",
            "width": "100%",
            "autosize": false,
            "height": typeof height === 'number' ? height : parseInt(height) || 100
        };

        script.innerHTML = JSON.stringify(config);

        // Assemble the widget
        widgetContainer.appendChild(widgetDiv);
        widgetContainer.appendChild(copyrightDiv);
        widgetContainer.appendChild(script);

        // Add to DOM
        containerRef.current.appendChild(widgetContainer);

        console.log('🧪 MINI WIDGET: Created for', symbol);

        return () => {
            if (containerRef.current) {
                containerRef.current.innerHTML = '';
            }
        };
    }, [symbol, height, width]);

    return (
        <div
            ref={containerRef}
            style={{
                width: typeof width === 'number' ? `${width}px` : width,
                height: typeof height === 'number' ? `${height}px` : height,
                minHeight: '100px'
            }}
        />
    );
};

export default TradingViewMiniWidget;
