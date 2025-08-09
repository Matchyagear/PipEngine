import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

const ScreenerTab = () => {
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Create the TradingView widget container
        const container = document.getElementById('tradingview_screener');
        if (!container) return;

        // Clear any existing content
        container.innerHTML = '';

        // Create the widget script
        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-screener.js';
        script.async = true;
        script.innerHTML = JSON.stringify({
            "width": "100%",
            "height": "100%",
            "defaultColumn": "overview",
            "defaultScreen": "most_capitalized",
            "market": "US",
            "showToolbar": true,
            "colorTheme": "dark",
            "locale": "en",
            "isTransparent": false
        });

        // Add the script to the container
        container.appendChild(script);

        // Set loading to false after a short delay to allow widget to initialize
        const timer = setTimeout(() => {
            setIsLoading(false);
        }, 2000);

        return () => {
            clearTimeout(timer);
        };
    }, []);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="h-screen flex flex-col overflow-hidden"
        >
            {/* Screener Header */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4 mb-4">
                <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                        </svg>
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                            Stock Screener
                        </h1>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                            Advanced stock screening powered by TradingView
                        </p>
                    </div>
                </div>
            </div>

            {/* TradingView Screener Widget */}
            <div className="flex-1 bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden relative">
                {isLoading && (
                    <div className="absolute inset-0 flex items-center justify-center bg-white dark:bg-gray-800 z-10">
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                            <p className="text-gray-600 dark:text-gray-400">Loading TradingView Screener...</p>
                        </div>
                    </div>
                )}

                <div
                    id="tradingview_screener"
                    className="w-full h-full"
                    style={{ minHeight: 'calc(100vh - 200px)' }}
                />
            </div>
        </motion.div>
    );
};

export default ScreenerTab;
