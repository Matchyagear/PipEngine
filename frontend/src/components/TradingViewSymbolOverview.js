import React, { useEffect, useMemo, useRef } from 'react';

// Symbol Overview widget wrapper
// Docs: https://www.tradingview.com/widget/symbol-overview/
// Usage: <TradingViewSymbolOverview symbol="AAPL" height={64} />
const TradingViewSymbolOverview = ({ symbol, height = 64, theme = 'dark', lineWidth = 2, dateRange = '3M' }) => {
  const containerRef = useRef(null);

  const config = useMemo(() => ({
    symbols: [[(symbol || 'AAPL').toUpperCase(), (symbol || 'AAPL').toUpperCase()]],
    chartOnly: true,
    width: '100%',
    height,
    locale: 'en',
    colorTheme: theme,
    isTransparent: true,
    autosize: true,
    showVolume: false,
    showMA: false,
    lineWidth,
    dateRange,
    scalePosition: 'right',
    scaleMode: 'Normal',
  }), [symbol, height, theme, lineWidth, dateRange]);

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.innerHTML = '';

    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js';
    script.async = true;
    script.innerHTML = JSON.stringify(config);
    containerRef.current.appendChild(script);

    return () => {
      if (containerRef.current) containerRef.current.innerHTML = '';
    };
  }, [config]);

  return (
    <div className="w-full overflow-hidden rounded border border-gray-700/50" style={{ height }}>
      <div ref={containerRef} className="w-full h-full" />
    </div>
  );
};

export default TradingViewSymbolOverview;
