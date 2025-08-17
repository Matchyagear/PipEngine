import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, X, BarChart3 } from 'lucide-react';
// Using a lightweight inline SVG sparkline for perfect fit
import Sparkline from './components/Sparkline';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

const MiniStockCard = ({ stock, onClick, onOpenChart }) => {
  // Watchlist dropdown state
  const [showWatchlistDropdown, setShowWatchlistDropdown] = useState(false);
  const [watchlists, setWatchlists] = useState([]);
  const [loadingWatchlists, setLoadingWatchlists] = useState(false);
  const [notification, setNotification] = useState({ show: false, message: '', type: '' });

  // Watchlist functions
  const fetchWatchlists = async () => {
    if (watchlists.length > 0) return; // Only fetch once

    setLoadingWatchlists(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/watchlists`);
      if (response.ok) {
        const data = await response.json();
        setWatchlists(data.watchlists || []);
      }
    } catch (error) {
      console.error('Error fetching watchlists:', error);
    } finally {
      setLoadingWatchlists(false);
    }
  };

  const isStockInWatchlist = (watchlist) => {
    if (!watchlist.tickers) return false;

    let tickers;
    if (Array.isArray(watchlist.tickers)) {
      tickers = watchlist.tickers;
    } else {
      tickers = watchlist.tickers.split(',').map(t => t.trim());
    }

    return tickers.some(ticker => {
      const cleanTicker = ticker.includes(':') ? ticker.split(':')[1] : ticker;
      return cleanTicker.toUpperCase() === stock.ticker.toUpperCase();
    });
  };

  const handleWatchlistToggle = async (watchlist, isChecked) => {
    try {
      let updatedTickers;

      if (isChecked) {
        // Add stock to watchlist
        if (!watchlist.tickers || (Array.isArray(watchlist.tickers) && watchlist.tickers.length === 0)) {
          updatedTickers = [stock.ticker];
        } else if (Array.isArray(watchlist.tickers)) {
          updatedTickers = [...watchlist.tickers, stock.ticker];
        } else {
          updatedTickers = watchlist.tickers + ',' + stock.ticker;
        }
      } else {
        // Remove stock from watchlist
        if (Array.isArray(watchlist.tickers)) {
          updatedTickers = watchlist.tickers.filter(ticker => {
            const cleanTicker = ticker.includes(':') ? ticker.split(':')[1] : ticker;
            return cleanTicker.toUpperCase() !== stock.ticker.toUpperCase();
          });
        } else {
          const tickers = watchlist.tickers.split(',').map(t => t.trim());
          updatedTickers = tickers.filter(ticker => {
            const cleanTicker = ticker.includes(':') ? ticker.split(':')[1] : ticker;
            return cleanTicker.toUpperCase() !== stock.ticker.toUpperCase();
          }).join(',');
        }
      }

      const response = await fetch(`${API_BASE_URL}/api/watchlists/${watchlist.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: watchlist.name,
          tickers: updatedTickers
        })
      });

      if (response.ok) {
        const updatedWatchlist = await response.json();
        setWatchlists(prev => prev.map(w => w.id === watchlist.id ? updatedWatchlist : w));

        showNotification(
          isChecked ? `Added to ${watchlist.name}` : `Removed from ${watchlist.name}`,
          'success'
        );
      } else {
        showNotification('Failed to update watchlist', 'error');
      }
    } catch (error) {
      console.error('Error updating watchlist:', error);
      showNotification('Error updating watchlist', 'error');
    }
  };

  const showNotification = (message, type) => {
    setNotification({ show: true, message, type });
    setTimeout(() => setNotification({ show: false, message: '', type: '' }), 3000);
  };

  const handleAddToWatchlist = async (e) => {
    e.stopPropagation();
    if (watchlists.length === 0) {
      await fetchWatchlists();
    }
    setShowWatchlistDropdown(!showWatchlistDropdown);
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showWatchlistDropdown && !event.target.closest('.watchlist-dropdown-container')) {
        setShowWatchlistDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showWatchlistDropdown]);

  const score = typeof stock.score === 'number' ? stock.score : 0;
  const ringClass = score === 4 ? 'ring-green-500' : score === 3 ? 'ring-yellow-400' : score === 2 ? 'ring-orange-500' : score === 1 ? 'ring-red-600' : 'ring-red-900';
  const shiny = (score === 4 && (stock.setupFit || 0) >= 80);

  return (
    <div className={shiny ? 'p-[2px] rounded-xl bg-gradient-to-r from-emerald-400 via-green-300 to-cyan-400 shadow-[0_0_14px_rgba(34,197,94,0.45)]' : `rounded-xl ring-2 ${ringClass}`}>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="panel card-panel p-3 hover:shadow-lg transition-all cursor-pointer hover:scale-105 relative group"
        onClick={() => onClick && onClick(stock)}
      >
        {/* Action Buttons - Top Right Corner on Hover */}
        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex space-x-1">
          {/* Add Chart Button */}
          {onOpenChart && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onOpenChart(stock);
              }}
              className="p-1.5 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-colors"
              title="Add Chart"
            >
              <BarChart3 className="w-3 h-3" />
            </button>
          )}

          {/* Add to Watchlist Button */}
          <div className="watchlist-dropdown-container">
            <button
              onClick={handleAddToWatchlist}
              className="p-1.5 bg-black text-white rounded-full shadow-lg hover:bg-gray-800 transition-colors"
              title="Add to Watchlist"
            >
              <Plus className="w-3 h-3" />
            </button>

            {/* Watchlist Dropdown */}
            {showWatchlistDropdown && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute top-full right-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 z-50"
              >
                <div className="p-4">
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                    Add {stock.ticker} to Watchlists
                  </h4>

                  {loadingWatchlists ? (
                    <div className="flex items-center justify-center py-4">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
                      <span className="ml-2 text-sm text-gray-600">Loading...</span>
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {watchlists.map((watchlist) => {
                        const isChecked = isStockInWatchlist(watchlist);
                        return (
                          <label
                            key={watchlist.id}
                            className="flex items-center space-x-2 p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                          >
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={(e) => handleWatchlistToggle(watchlist, e.target.checked)}
                              className="rounded border-gray-300 text-black focus:ring-black"
                            />
                            <span className="text-sm text-gray-900 dark:text-white">
                              {watchlist.name}
                            </span>
                          </label>
                        );
                      })}

                      {watchlists.length === 0 && (
                        <p className="text-sm text-gray-500 text-center py-4">
                          No watchlists found
                        </p>
                      )}

                      {/* Create New Watchlist Option */}
                      <hr className="my-2 border-gray-200 dark:border-gray-700" />
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          console.log('Create new watchlist with', stock.ticker);
                          setShowWatchlistDropdown(false);
                        }}
                        className="w-full text-left p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded flex items-center space-x-2"
                      >
                        <Plus className="w-4 h-4" />
                        <span className="text-sm">Create New Watchlist</span>
                      </button>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </div>
        </div>

        {/* Notification Toast */}
        <AnimatePresence>
          {notification.show && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={`absolute top-2 left-2 right-10 px-2 py-1 rounded shadow-lg z-40 text-xs ${notification.type === 'success'
                ? 'bg-green-100 text-green-800 border border-green-200'
                : 'bg-red-100 text-red-800 border border-red-200'
                }`}
            >
              <p className="font-medium">{notification.message}</p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Header with Ticker and Score */}
        <div className="flex justify-between items-start mb-2">
          <div>
            <h3 className="text-sm font-bold text-gray-900 dark:text-white">
              {stock.ticker}
            </h3>
          </div>
          <div className={`px-2 py-1 rounded-full text-xs font-bold ${stock.score === 4 ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' :
            stock.score === 3 ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300' :
              stock.score >= 2 ? 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300' :
                'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
            }`}>
            {stock.score}/4
          </div>
        </div>

        {/* Individual Criteria Display */}
        {stock.passes && (
          <div className="grid grid-cols-2 gap-1 mb-2">
            {Object.entries(stock.passes).filter(([key]) => ['trend', 'momentum', 'volume', 'priceAction'].includes(key)).map(([key, value]) => (
              <div key={key} className={`px-1 py-0.5 rounded text-xs font-medium text-center ${
                value 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' 
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
              }`}>
                {key.charAt(0).toUpperCase() + key.slice(1)}
              </div>
            ))}
          </div>
        )}

        {/* Price and Change */}
        <div className="mb-2">
          <p className="text-lg font-bold text-gray-900 dark:text-white">
            ${stock.currentPrice ? stock.currentPrice.toFixed(2) : 'N/A'}
          </p>
          <p className={`text-xs font-medium ${(stock.priceChangePercent || 0) >= 0
            ? 'text-green-600 dark:text-green-400'
            : 'text-red-600 dark:text-red-400'
            }`}>
            {(stock.priceChangePercent || 0) >= 0 ? '+' : ''}
            {stock.priceChangePercent ? stock.priceChangePercent.toFixed(2) : '0.00'}%
          </p>
        </div>

        {/* Sparkline */}
      <div className="mt-2">
        <Sparkline data={(stock.intraday || stock.spark || stock.history || []).slice(-40)} width={200} height={14} stroke={stock.priceChangePercent >= 0 ? '#22c55e' : '#ef4444'} strokeWidth={1.75} />
      </div>

        {/* Click indicator */}
        <div className="mt-2 text-center">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Click for details
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default MiniStockCard;
