import React, { useEffect, useMemo, useRef } from 'react';

// Lightweight wrapper that embeds TradingView's Mini Symbol Overview widget
// Docs: https://www.tradingview.com/widget/mini-symbol-overview/
// Usage: <TradingViewMiniChart symbol="AAPL" height={80} />
const TradingViewMiniChart = ({ symbol, height = 80, dateRange = '1M', theme = 'dark' }) => {
  const containerRef = useRef(null);

  const config = useMemo(() => ({
    symbol: (symbol || 'AAPL').toUpperCase(),
    width: '100%',
    height: height,
    locale: 'en',
    dateRange,
    colorTheme: theme,
    isTransparent: true,
    autosize: true,
    // Optional fine-tuning colors
    trendLineColor: '#21c55d',
    underLineColor: theme === 'dark' ? 'rgba(33,197,93,0.10)' : 'rgba(33,197,93,0.15)',
    lineColor: '#21c55d',
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
    <div className="w-full overflow-hidden rounded border border-gray-700/50" style={{ height }}>
      <div ref={containerRef} className="w-full h-full" />
    </div>
  );
};

export default TradingViewMiniChart;
