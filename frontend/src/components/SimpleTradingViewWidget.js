import React, { useEffect, useRef } from 'react';

const SimpleTradingViewWidget = ({ symbol = 'AAPL', width = '100%', height = 80 }) => {
    const containerRef = useRef(null);

    useEffect(() => {
        if (!containerRef.current) return;

        // Clear any existing content
        containerRef.current.innerHTML = '';

        // Create the widget script directly
        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js';
        script.async = true;
        
        // Widget configuration as text content
        script.text = JSON.stringify({
            "symbol": symbol,
            "width": width,
            "height": height,
            "locale": "en",
            "dateRange": "12M",
            "colorTheme": "dark",
            "isTransparent": true,
            "autosize": false,
            "largeChartUrl": ""
        });

        // Create container div
        const widgetContainer = document.createElement('div');
        widgetContainer.className = 'tradingview-widget-container';
        widgetContainer.style.height = height + 'px';
        widgetContainer.style.width = width;
        
        // Append script to container
        widgetContainer.appendChild(script);
        
        // Append to DOM
        containerRef.current.appendChild(widgetContainer);

        console.log('🧪 SIMPLE WIDGET: Created for', symbol);

        return () => {
            if (containerRef.current) {
                containerRef.current.innerHTML = '';
            }
        };
    }, [symbol, width, height]);

    return (
        <div 
            ref={containerRef} 
            style={{ 
                width: width, 
                height: height + 'px',
                backgroundColor: '#1f2937',
                border: '1px solid #374151',
                borderRadius: '4px'
            }}
        />
    );
};

export default SimpleTradingViewWidget;
