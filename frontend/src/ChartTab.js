import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, Settings, RefreshCw } from 'lucide-react';

const ChartTab = ({ initialSymbol = 'AAPL' }) => {
    // Load saved state from localStorage or use defaults
    const getSavedState = () => {
        try {
            const saved = localStorage.getItem('chartTabState');
            if (saved) {
                const parsed = JSON.parse(saved);
                return {
                    symbol: parsed.symbol || initialSymbol,
                    theme: parsed.theme || 'dark',
                    timeframe: parsed.timeframe || '1D'
                };
            }
        } catch (error) {
            console.warn('Failed to load chart state:', error);
        }
        return {
            symbol: initialSymbol,
            theme: 'dark',
            timeframe: '1D'
        };
    };

    const savedState = getSavedState();
    const [selectedSymbol, setSelectedSymbol] = useState(savedState.symbol);
    const [chartTheme, setChartTheme] = useState(savedState.theme);
    const [timeframe, setTimeframe] = useState(savedState.timeframe);
    const [isLoading, setIsLoading] = useState(false);

    // Popular symbols for quick selection
    const popularSymbols = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
        'SPY', 'QQQ', 'IWM', 'VTI', 'BTCUSD', 'ETHUSD'
    ];

    // Timeframe options
    const timeframes = [
        { value: '1', label: '1m' },
        { value: '5', label: '5m' },
        { value: '15', label: '15m' },
        { value: '30', label: '30m' },
        { value: '60', label: '1h' },
        { value: '240', label: '4h' },
        { value: '1D', label: '1D' },
        { value: '1W', label: '1W' },
        { value: '1M', label: '1M' }
    ];

    // TradingView widget configuration
    const getWidgetConfig = () => ({
        width: '100%',
        height: '100%',
        symbol: selectedSymbol,
        interval: timeframe,
        timezone: 'America/New_York',
        theme: chartTheme,
        style: '1',
        locale: 'en',
        toolbar_bg: chartTheme === 'dark' ? '#1e1e1e' : '#ffffff',
        enable_publishing: false,
        allow_symbol_change: true,
        container_id: 'tradingview_chart',
        autosize: true,
        studies_overrides: {},
        overrides: {
            'mainSeriesProperties.candleStyle.upColor': '#26a69a',
            'mainSeriesProperties.candleStyle.downColor': '#ef5350',
            'mainSeriesProperties.candleStyle.wickUpColor': '#26a69a',
            'mainSeriesProperties.candleStyle.wickDownColor': '#ef5350'
        }
    });

    // Save state to localStorage whenever it changes
    const saveState = (newState) => {
        try {
            const currentState = {
                symbol: selectedSymbol,
                theme: chartTheme,
                timeframe: timeframe,
                ...newState
            };
            localStorage.setItem('chartTabState', JSON.stringify(currentState));
        } catch (error) {
            console.warn('Failed to save chart state:', error);
        }
    };

    // Update symbol when prop changes
    useEffect(() => {
        setSelectedSymbol(initialSymbol);
        saveState({ symbol: initialSymbol });
    }, [initialSymbol]);

    useEffect(() => {
        // Load TradingView widget script
        const script = document.createElement('script');
        script.src = 'https://s3.tradingview.com/tv.js';
        script.async = true;
        script.onload = () => {
            if (window.TradingView) {
                // Clear existing widget
                const container = document.getElementById('tradingview_chart');
                if (container) {
                    container.innerHTML = '';
                }

                // Create new widget
                new window.TradingView.widget(getWidgetConfig());
            }
        };
        document.head.appendChild(script);

        return () => {
            // Cleanup
            const existingScript = document.querySelector('script[src="https://s3.tradingview.com/tv.js"]');
            if (existingScript) {
                existingScript.remove();
            }
        };
    }, [selectedSymbol, chartTheme, timeframe]);

    const handleSymbolChange = (symbol) => {
        setIsLoading(true);
        setSelectedSymbol(symbol);
        saveState({ symbol });
        // Reload the widget with new symbol
        setTimeout(() => {
            if (window.TradingView) {
                const container = document.getElementById('tradingview_chart');
                if (container) {
                    container.innerHTML = '';
                }
                new window.TradingView.widget(getWidgetConfig());
            }
            setIsLoading(false);
        }, 100);
    };

    const handleThemeChange = () => {
        const newTheme = chartTheme === 'dark' ? 'light' : 'dark';
        setChartTheme(newTheme);
        saveState({ theme: newTheme });
    };

    const handleTimeframeChange = (newTimeframe) => {
        setTimeframe(newTimeframe);
        saveState({ timeframe: newTimeframe });
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="h-screen flex flex-col justify-center items-center p-4"
        >
            {/* Auto-Fit Chart Container */}
            <div className="w-full max-w-6xl panel overflow-hidden">
                {/* TradingView Widget Container */}
                <div
                    id="tradingview_chart"
                    className="w-full bg-white dark:bg-gray-900"
                    style={{ height: 'calc(100vh - 4rem)', maxHeight: '600px' }}
                >
                    {isLoading && (
                        <div className="flex items-center justify-center h-full">
                            <div className="text-center">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                                <p className="text-gray-600 dark:text-gray-400">Loading TradingView Chart...</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
};

export default ChartTab;
