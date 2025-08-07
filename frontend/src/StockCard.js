import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Volume2,
  Target,
  Brain,
  ExternalLink,
  Info,
  Zap,
  Globe,
  Plus,
  X,
  BarChart3
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

const Tooltip = ({ children, content }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {children}
      {showTooltip && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg z-50 max-w-xs whitespace-normal">
          {content}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
        </div>
      )}
    </div>
  );
};

const StockCard = ({
  stock,
  aiProvider = 'gemini',
  onClick,
  onOpenChart
}) => {
  const [showAI, setShowAI] = useState(false);
  const [aiSummary, setAiSummary] = useState('');
  const [loadingAI, setLoadingAI] = useState(false);
  const [stockNews, setStockNews] = useState([]);
  const [loadingNews, setLoadingNews] = useState(false);

  // Watchlist dropdown state
  const [showWatchlistDropdown, setShowWatchlistDropdown] = useState(false);
  const [watchlists, setWatchlists] = useState([]);
  const [loadingWatchlists, setLoadingWatchlists] = useState(false);
  const [notification, setNotification] = useState({ show: false, message: '', type: '' });

  useEffect(() => {
    // Always load stock-specific news for every card
    if (stock.ticker) {
      fetchStockNews();
    }
  }, [stock.ticker]);

  const fetchStockNews = async () => {
    try {
      setLoadingNews(true);
      const response = await fetch(`${API_BASE_URL}/api/news/stock/${stock.ticker}?limit=3`);
      const data = await response.json();
      setStockNews(data.news || []);
    } catch (error) {
      console.error('Error fetching stock news:', error);
    } finally {
      setLoadingNews(false);
    }
  };

  const fetchAISummary = async () => {
    if (aiSummary) {
      setShowAI(!showAI);
      return;
    }

    try {
      setLoadingAI(true);
      // Try Claude first as primary AI provider
      let response = await fetch(`${API_BASE_URL}/api/stocks/${stock.ticker || stock.symbol}/claude-insight`);
      let data = await response.json();

      if (data.insight && data.insight !== 'AI summary not available' && !data.insight.includes('Claude analysis temporarily unavailable')) {
        setAiSummary(data.insight);
      } else {
        // Fallback to Gemini if Claude fails
        try {
          response = await fetch(`${API_BASE_URL}/api/stocks/${stock.ticker || stock.symbol}/gemini-insight`);
          data = await response.json();
          setAiSummary(data.insight || 'AI analysis temporarily unavailable');
        } catch (fallbackError) {
          setAiSummary('AI analysis temporarily unavailable. Please try again later.');
        }
      }

      setShowAI(true);
    } catch (error) {
      console.error('AI Summary Error:', error);
      setAiSummary('Error loading AI summary. Please try again.');
      setShowAI(true);
    } finally {
      setLoadingAI(false);
    }
  };

  const getCriteriaIcon = (criteriaName) => {
    switch (criteriaName) {
      case 'trend': return <TrendingUp className="w-4 h-4" />;
      case 'momentum': return <Activity className="w-4 h-4" />;
      case 'volume': return <Volume2 className="w-4 h-4" />;
      case 'priceAction': return <Target className="w-4 h-4" />;
      case 'oversold': return <TrendingDown className="w-4 h-4" />;
      case 'breakout': return <Zap className="w-4 h-4" />;
      default: return null;
    }
  };

  const getIndicatorTooltip = (indicator) => {
    const tooltips = {
      RSI: "Relative Strength Index (0-100): Measures if a stock is overbought (>70) or oversold (<30). Higher values suggest the stock might be due for a pullback.",
      MACD: "Moving Average Convergence Divergence: Shows the relationship between two moving averages. Positive values suggest upward momentum, negative values suggest downward momentum.",
      Volume: "Relative Volume: Compares current trading volume to average. Values >1.5x suggest high interest and potential price movement.",
      "50MA": "50-Day Moving Average: The average price over the last 50 days. When price is above this line, it suggests short-term upward trend.",
      "200MA": "200-Day Moving Average: The average price over the last 200 days. When price is above this line, it suggests long-term upward trend.",
      Stochastic: "Stochastic Oscillator (0-100): Measures momentum. Values >80 suggest overbought conditions, <20 suggest oversold conditions."
    };
    return tooltips[indicator] || "Technical indicator that helps analyze stock movement and momentum.";
  };

  const getChangeColor = (change) => {
    if (change > 0) return 'text-green-600 dark:text-green-400';
    if (change < 0) return 'text-red-600 dark:text-red-400';
    return 'text-gray-600 dark:text-gray-400';
  };

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
    setTimeout(() => {
      setNotification({ show: false, message: '', type: '' });
    }, 3000);
  };

  const handleAddToWatchlist = async (e) => {
    e.stopPropagation();
    if (!showWatchlistDropdown) {
      await fetchWatchlists();
    }
    setShowWatchlistDropdown(!showWatchlistDropdown);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showWatchlistDropdown && !event.target.closest('.watchlist-dropdown-container')) {
        setShowWatchlistDropdown(false);
      }
    };

    if (showWatchlistDropdown) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [showWatchlistDropdown]);

  // Always use the full Shadow's Picks stock card format - no compact versions
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 hover:shadow-xl transition-all stock-card cursor-pointer hover:scale-105 relative group"
      onClick={onClick}
    >
      {/* Action Buttons - Top Right Corner on Hover */}
      <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity flex space-x-2">
        {/* Add Chart Button */}
        {onOpenChart && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onOpenChart(stock);
            }}
            className="p-2 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-colors"
            title="Add Chart"
          >
            <BarChart3 className="w-4 h-4" />
          </button>
        )}

        {/* Add to Watchlist Button */}
        <div className="watchlist-dropdown-container">
          <button
            onClick={handleAddToWatchlist}
            className="p-2 bg-black text-white rounded-full shadow-lg hover:bg-gray-800 transition-colors"
            title="Add to Watchlist"
          >
            <Plus className="w-4 h-4" />
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
                        // Create new watchlist with this stock
                        // This would typically open the watchlist modal
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
            className={`absolute top-4 left-4 right-16 px-3 py-2 rounded-lg shadow-lg z-40 ${notification.type === 'success'
              ? 'bg-green-100 text-green-800 border border-green-200'
              : 'bg-red-100 text-red-800 border border-red-200'
              }`}
          >
            <p className="text-sm font-medium">{notification.message}</p>
          </motion.div>
        )}
      </AnimatePresence>
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">
            {stock.ticker}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
            {stock.companyName || stock.name}
          </p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            ${(stock.currentPrice || stock.price)?.toFixed(2)}
          </p>
          <p className={`text-sm font-medium ${getChangeColor(stock.priceChangePercent || stock.changePercent)}`}>
            {(stock.priceChangePercent || stock.changePercent) >= 0 ? '+' : ''}
            {(stock.priceChangePercent || stock.changePercent)?.toFixed(2)}%
          </p>
        </div>
      </div>

      {/* Score and Rank */}
      {stock.score !== undefined && (
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center space-x-2">
            <div className={`px-3 py-1 rounded-full text-sm font-bold ${stock.score === 4 ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' :
              stock.score === 3 ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300' :
                stock.score >= 2 ? 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300' :
                  'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
              }`}>
              {stock.score}/4
            </div>
            {stock.rank && (
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Rank #{stock.rank}
              </span>
            )}
          </div>

          {/* Bonus indicators */}
          <div className="flex space-x-1">
            {stock.passes?.oversold && (
              <div className="px-2 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300 rounded-full text-xs font-medium">
                Oversold
              </div>
            )}
            {stock.passes?.breakout && (
              <div className="px-2 py-1 bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300 rounded-full text-xs font-medium">
                Breakout
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Criteria Grid */}
      {stock.passes && (
        <div className="grid grid-cols-2 gap-3 mb-4">
          {Object.entries(stock.passes).slice(0, 4).map(([criteria, passed]) => (
            <div
              key={criteria}
              className={`p-3 rounded-lg border-2 ${passed
                ? 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-700'
                : 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-700'
                }`}
            >
              <div className="flex items-center space-x-2">
                <div className={passed ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                  {getCriteriaIcon(criteria)}
                </div>
                <span className={`text-xs font-medium capitalize ${passed ? 'text-green-800 dark:text-green-300' : 'text-red-800 dark:text-red-300'
                  }`}>
                  {criteria === 'priceAction' ? 'Price Action' : criteria}
                </span>
              </div>
              <div className={`text-xs mt-1 ${passed ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                }`}>
                {passed ? 'PASS' : 'FAIL'}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Technical Indicators with Tooltips */}
      {stock.RSI && (
        <div className="grid grid-cols-3 gap-4 mb-4 text-xs">
          <Tooltip content={getIndicatorTooltip('RSI')}>
            <div className="flex items-center space-x-1">
              <Info className="w-3 h-3 text-gray-400" />
              <span className="text-gray-500 dark:text-gray-400">RSI:</span>
              <span className={`ml-1 font-medium ${stock.RSI > 70 ? 'text-red-600' : stock.RSI < 30 ? 'text-green-600' : 'text-gray-900 dark:text-white'
                }`}>
                {stock.RSI.toFixed(1)}
              </span>
            </div>
          </Tooltip>

          <Tooltip content={getIndicatorTooltip('Volume')}>
            <div className="flex items-center space-x-1">
              <Info className="w-3 h-3 text-gray-400" />
              <span className="text-gray-500 dark:text-gray-400">Vol:</span>
              <span className="ml-1 font-medium text-gray-900 dark:text-white">
                {stock.relativeVolume?.toFixed(1)}x
              </span>
            </div>
          </Tooltip>

          <Tooltip content={getIndicatorTooltip('Stochastic')}>
            <div className="flex items-center space-x-1">
              <Info className="w-3 h-3 text-gray-400" />
              <span className="text-gray-500 dark:text-gray-400">Stoch:</span>
              <span className="ml-1 font-medium text-gray-900 dark:text-white">
                {stock.stochastic?.toFixed(1) || 'N/A'}
              </span>
            </div>
          </Tooltip>

          <Tooltip content={getIndicatorTooltip('50MA')}>
            <div className="flex items-center space-x-1">
              <Info className="w-3 h-3 text-gray-400" />
              <span className="text-gray-500 dark:text-gray-400">50MA:</span>
              <span className="ml-1 font-medium text-gray-900 dark:text-white">
                ${stock.fiftyMA?.toFixed(2)}
              </span>
            </div>
          </Tooltip>

          <Tooltip content={getIndicatorTooltip('200MA')}>
            <div className="flex items-center space-x-1">
              <Info className="w-3 h-3 text-gray-400" />
              <span className="text-gray-500 dark:text-gray-400">200MA:</span>
              <span className="ml-1 font-medium text-gray-900 dark:text-white">
                ${stock.twoHundredMA?.toFixed(2)}
              </span>
            </div>
          </Tooltip>

          <Tooltip content={getIndicatorTooltip('MACD')}>
            <div className="flex items-center space-x-1">
              <Info className="w-3 h-3 text-gray-400" />
              <span className="text-gray-500 dark:text-gray-400">MACD:</span>
              <span className={`ml-1 font-medium ${stock.MACD > 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                {stock.MACD?.toFixed(3)}
              </span>
            </div>
          </Tooltip>
        </div>
      )}

      {/* Stock News Preview - Always show */}
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2 flex items-center">
          <Globe className="w-4 h-4 mr-1" />
          Latest News
        </h4>
        {loadingNews ? (
          <div className="text-xs text-gray-500 dark:text-gray-400">Loading news...</div>
        ) : stockNews.length > 0 ? (
          <div className="space-y-2">
            {stockNews.slice(0, 2).map((article, index) => (
              <div
                key={index}
                className="p-2 bg-gray-50 dark:bg-gray-700 rounded text-xs cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                onClick={(e) => {
                  e.stopPropagation();
                  window.open(article.url, '_blank');
                }}
              >
                <p className="font-medium text-gray-900 dark:text-white line-clamp-2 mb-1">
                  {article.title}
                </p>
                <div className="flex justify-between text-gray-500 dark:text-gray-400">
                  <span className="truncate">{article.source}</span>
                  <span>Recent</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-xs text-gray-500 dark:text-gray-400">No recent news</div>
        )}
      </div>

      {/* Finviz Chart - Always show */}
      {stock.ticker && (
        <div className="mb-4 chart-container">
          <img
            src={`https://finviz.com/chart.ashx?t=${stock.ticker}&ty=c&ta=1&p=d&s=l`}
            alt={`${stock.ticker} chart`}
            className="w-full h-32 object-cover rounded-lg border"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        </div>
      )}

      {/* AI Summary Section */}
      <AnimatePresence>
        {showAI && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-700"
          >
            <div className="flex items-center space-x-2 mb-2">
              <Brain className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <span className="text-sm font-medium text-blue-800 dark:text-blue-300">
                Claude AI Analysis
              </span>
            </div>
            <p className="text-sm text-blue-700 dark:text-blue-300">
              {aiSummary}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Action Buttons */}
      <div className="flex space-x-2">
        <button
          onClick={(e) => {
            e.stopPropagation();
            fetchAISummary();
          }}
          disabled={loadingAI}
          className="flex-1 flex items-center justify-center space-x-2 py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50"
        >
          <Brain className="w-4 h-4" />
          <span className="text-sm">
            {loadingAI ? 'Loading...' : showAI ? 'Hide AI' : 'AI Insight'}
          </span>
        </button>
        <a
          href={`https://finviz.com/quote.ashx?t=${stock.ticker}`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center py-2 px-4 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
          onClick={(e) => e.stopPropagation()}
        >
          <ExternalLink className="w-4 h-4" />
        </a>
      </div>

      {/* Click to expand indicator */}
      <div className="mt-3 text-center">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Click card for detailed analysis
        </p>
      </div>
    </motion.div>
  );
};

export default StockCard;
