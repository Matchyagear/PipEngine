import React, { useEffect, useMemo, useRef } from 'react';

// Compact TradingView Advanced Chart (candles)
// Usage: <TradingViewCandleMini symbol="AAPL" height={140} interval="D" />
const TradingViewCandleMini = ({ symbol, height = 140, interval = 'D', theme = 'dark' }) => {
  const containerRef = useRef(null);

  const config = useMemo(() => ({
    autosize: true,
    symbol: (symbol || 'AAPL').toUpperCase(),
    interval,
    timezone: 'America/New_York',
    theme,
    style: '1', // candles
    locale: 'en',
    hide_top_toolbar: true,
    hide_legend: true,
    allow_symbol_change: false,
    calendar: false,
    withdateranges: false,
    support_host: 'https://www.tradingview.com',
    backgroundColor: 'rgba(0,0,0,0)'
  }), [symbol, interval, theme]);

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.innerHTML = '';

    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.async = true;
    script.innerHTML = JSON.stringify(config);

    const wrapper = document.createElement('div');
    wrapper.style.width = '100%';
    wrapper.style.height = `${height}px`;

    containerRef.current.appendChild(script);
    containerRef.current.appendChild(wrapper);

    return () => {
      if (containerRef.current) containerRef.current.innerHTML = '';
    };
  }, [config, height]);

  return (
    <div className="w-full overflow-hidden rounded" style={{ height }}>
      <div ref={containerRef} className="w-full h-full" />
    </div>
  );
};

export default TradingViewCandleMini;
