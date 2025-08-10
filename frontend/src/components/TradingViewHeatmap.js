import React, { useEffect, useMemo, useRef } from 'react';

// TradingView Stocks Heatmap widget wrapper
// Docs: https://www.tradingview.com/widget/stock-heatmap/
// Usage: <TradingViewHeatmap height={360} dataSource="SPX500" />
const TradingViewHeatmap = ({
  height = 360,
  theme = 'dark',
  exchange = 'US',
  dataSource = 'SPX500', // Alternatives: 'NASDAQ100', 'DJI', 'SPX500'
  grouping = 'sector',   // 'sector' | 'industry'
}) => {
  const containerRef = useRef(null);

  const config = useMemo(() => ({
    exchange,
    dataSource,
    grouping,
    blockColor: 'change',
    blockSize: 'market_cap_basic',
    locale: 'en',
    colorTheme: theme,
    hasTopBar: false,
    isDataSetEnabled: false,
    isZoomEnabled: true,
    hasSymbolTooltip: true,
    width: '100%',
    height,
  }), [exchange, dataSource, grouping, theme, height]);

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.innerHTML = '';

    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-stock-heatmap.js';
    script.async = true;
    script.innerHTML = JSON.stringify(config);

    containerRef.current.appendChild(script);

    return () => {
      if (containerRef.current) containerRef.current.innerHTML = '';
    };
  }, [config]);

  return (
    <div className="w-full overflow-hidden rounded" style={{ height }}>
      <div ref={containerRef} className="w-full h-full" />
    </div>
  );
};

export default TradingViewHeatmap;
