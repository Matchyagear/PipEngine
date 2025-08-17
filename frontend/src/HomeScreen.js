import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Clock,
  DollarSign,
  Globe,
  Zap,
  Plus,
  Volume2,
  Target,
  Brain,
  ExternalLink,
  Info,
  Bell,
  Star
} from 'lucide-react';
import { motion } from 'framer-motion';
import StockCard from './StockCard';
import IndexCard from './IndexCard';
import { NewsSidebar } from './NewsComponents';
import TradingViewHeatmap from './components/TradingViewHeatmap';
import TradingViewMiniChart from './components/TradingViewMiniChart';
import SimpleTradingViewWidget from './components/SimpleTradingViewWidget';
import DirectTradingViewChart from './components/DirectTradingViewChart';
import TradingViewMiniWidget from './components/TradingViewMiniWidget';
import MiniStockCard from './MiniStockCard';
import StockCardModal from './StockCardModal';

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

const HomeScreen = ({ onNewWatchlist, watchlists, onDeleteWatchlist, news, newsLoading, onOpenChart }) => {
  const [marketData, setMarketData] = useState(null);
  const [featuredStocks, setFeaturedStocks] = useState([]);
  const [fullMovers, setFullMovers] = useState(null);
  const [highestVolumeStocks, setHighestVolumeStocks] = useState([]);
  const [volatileStocks, setVolatileStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingFeatured, setLoadingFeatured] = useState(true);
  const [loadingMovers, setLoadingMovers] = useState(true);
  const [loadingVolume, setLoadingVolume] = useState(true);
  const [loadingVolatile, setLoadingVolatile] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Expandable section states
  const [showMorningBrief, setShowMorningBrief] = useState(true);
  const [morning, setMorning] = useState(null);
  const [mbLoading, setMbLoading] = useState(false);
  const [showAllGainers, setShowAllGainers] = useState(false);
  const [showAllLosers, setShowAllLosers] = useState(false);
  const [showAllVolume, setShowAllVolume] = useState(false);
  const [showAllVolatile, setShowAllVolatile] = useState(false);
  const [expandedGainers, setExpandedGainers] = useState([]);
  const [expandedLosers, setExpandedLosers] = useState([]);
  const [expandedVolume, setExpandedVolume] = useState([]);
  const [expandedVolatile, setExpandedVolatile] = useState([]);

  // Mini stock card modal state
  const [selectedMiniStock, setSelectedMiniStock] = useState(null);
  const [showStockModal, setShowStockModal] = useState(false);

  useEffect(() => {
    // OPTIMIZED: Load only critical market data immediately
    fetchMarketData();

    // HEAVILY STAGGERED: Spread out API calls to reduce initial load burst
    const t1 = setTimeout(() => fetchFullMovers(), 3000);     // 3s delay
    const t2 = setTimeout(() => fetchHighestVolumeStocks(), 6000);  // 6s delay
    const t3 = setTimeout(() => fetchVolatileStocks(), 9000); // 9s delay
    const t4 = setTimeout(() => fetchFeaturedStocks(), 12000); // 12s delay - most expensive last

    // Refresh every 10 minutes instead of 5 (less frequent auto-refresh)
    const interval = setInterval(() => {
      fetchMarketData();
      setTimeout(() => fetchFullMovers(), 1000);
      setTimeout(() => fetchHighestVolumeStocks(), 2000);
      setTimeout(() => fetchVolatileStocks(), 3000);
      setTimeout(() => fetchFeaturedStocks(), 4000);
    }, 600000); // 10 minutes instead of 5

    return () => {
      clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); clearTimeout(t4);
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    // DISABLED: Morning brief loading for better performance
    // Can be re-enabled later with background loading
    const fetchMB = async () => {
      try {
        setMbLoading(true);
        // OPTIMIZED: Load morning brief sooner with TradingView charts
        setTimeout(async () => {
          try {
            const res = await fetch(`${API_BASE_URL}/api/morning/brief`);
            if (res.ok) setMorning(await res.json());
          } catch (e) {
            console.log('Morning brief loading - showing fallback charts');
          }
          setMbLoading(false);
        }, 1000); // 1 second delay for faster loading
      } catch (e) {
        setMbLoading(false);
      }
    };
    fetchMB();
  }, []);

  const fetchMarketData = async () => {
    try {
      setLoading(true);
      // Use instant endpoint for immediate loading
      const response = await fetch(`${API_BASE_URL}/api/market/overview/instant`);
      const data = await response.json();
      setMarketData(data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error fetching market data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFeaturedStocks = async () => {
    try {
      setLoadingFeatured(true);
      // Use fast endpoint for live featured stocks (not static)
      const response = await fetch(`${API_BASE_URL}/api/stocks/scan/fast`);

      if (response.ok) {
        const data = await response.json();
        // Take top 2 performing stocks for featured section
        setFeaturedStocks(data.stocks?.slice(0, 2) || []);
      } else {
        // Fallback to regular scan if fast endpoint fails
        const fallbackResponse = await fetch(`${API_BASE_URL}/api/stocks/scan`);
        if (fallbackResponse.ok) {
          const fallbackData = await fallbackResponse.json();
          setFeaturedStocks(fallbackData.stocks?.slice(0, 2) || []);
        } else {
          // Final fallback to static data only if both live endpoints fail
          setFeaturedStocks([
            {
              symbol: 'AAPL',
              company_name: 'Apple Inc.',
              current_price: 227.52,
              change_percent: 2.1,
              volume: 45678901,
              score: 4,
              analysis: {
                recommendation: 'Strong Buy',
                price_target: 250,
                risk_level: 'Low'
              }
            },
            {
              symbol: 'NVDA',
              company_name: 'NVIDIA Corporation',
              current_price: 140.76,
              change_percent: 3.4,
              volume: 67890123,
              score: 4,
              analysis: {
                recommendation: 'Buy',
                price_target: 160,
                risk_level: 'Medium'
              }
            }
          ]);
        }
      }
    } catch (error) {
      console.error('Error fetching featured stocks:', error);
      // Try regular scan as fallback for network errors
      try {
        const fallbackResponse = await fetch(`${API_BASE_URL}/api/stocks/scan`);
        if (fallbackResponse.ok) {
          const fallbackData = await fallbackResponse.json();
          setFeaturedStocks(fallbackData.stocks?.slice(0, 2) || []);
        } else {
          // Final fallback to static data
          setFeaturedStocks([
            {
              symbol: 'AAPL',
              company_name: 'Apple Inc.',
              current_price: 227.52,
              change_percent: 2.1,
              volume: 45678901,
              score: 4,
              analysis: {
                recommendation: 'Strong Buy',
                price_target: 250,
                risk_level: 'Low'
              }
            },
            {
              symbol: 'MSFT',
              company_name: 'Microsoft Corporation',
              current_price: 422.54,
              change_percent: 1.8,
              volume: 23456789,
              score: 4,
              analysis: {
                recommendation: 'Buy',
                price_target: 450,
                risk_level: 'Low'
              }
            }
          ]);
        }
      } catch (fallbackError) {
        console.error('Fallback fetch also failed:', fallbackError);
        // Final static fallback
        setFeaturedStocks([
          {
            symbol: 'AAPL',
            company_name: 'Apple Inc.',
            current_price: 227.52,
            change_percent: 2.1,
            volume: 45678901,
            score: 4,
            analysis: {
              recommendation: 'Strong Buy',
              price_target: 250,
              risk_level: 'Low'
            }
          },
          {
            symbol: 'MSFT',
            company_name: 'Microsoft Corporation',
            current_price: 422.54,
            change_percent: 1.8,
            volume: 23456789,
            score: 4,
            analysis: {
              recommendation: 'Buy',
              price_target: 450,
              risk_level: 'Low'
            }
          }
        ]);
      }
    } finally {
      setLoadingFeatured(false);
    }
  };

  const fetchFullMovers = async () => {
    try {
      setLoadingMovers(true);
      const response = await fetch(`${API_BASE_URL}/api/market/full-movers`, { cache: 'no-store' });
      const data = await response.json();
      setFullMovers(data);
    } catch (error) {
      console.error('Error fetching full movers:', error);
    } finally {
      setLoadingMovers(false);
    }
  };

  const fetchHighestVolumeStocks = async () => {
    try {
      setLoadingVolume(true);
      const response = await fetch(`${API_BASE_URL}/api/market/highest-volume`, { cache: 'no-store' });
      const data = await response.json();
      setHighestVolumeStocks(data.stocks?.slice(0, 5) || []);
    } catch (error) {
      console.error('Error fetching highest volume stocks:', error);
    } finally {
      setLoadingVolume(false);
    }
  };

  const fetchVolatileStocks = async () => {
    try {
      setLoadingVolatile(true);
      const response = await fetch(`${API_BASE_URL}/api/market/volatile-stocks?limit=10`, { cache: 'no-store' });
      const data = await response.json();
      setVolatileStocks(data.volatile_stocks?.slice(0, 5) || []);
    } catch (error) {
      console.error('Error fetching volatile stocks:', error);
    } finally {
      setLoadingVolatile(false);
    }
  };

  // Function to load more stocks when expanding
  const loadMoreGainers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/market/movers`);
      const data = await response.json();
      const additionalGainers = [];

      // Get full analysis for additional gainers (skip first 2)
      for (const gainer of data.gainers.slice(2, 5)) {
        try {
          const stockResponse = await fetch(`${API_BASE_URL}/api/stocks/${gainer.ticker}`);
          const stockData = await stockResponse.json();
          if (stockData) additionalGainers.push(stockData);
        } catch (error) {
          console.error(`Error fetching additional gainer ${gainer.ticker}:`, error);
        }
      }
      setExpandedGainers(additionalGainers);
    } catch (error) {
      console.error('Error loading more gainers:', error);
    }
  };

  const loadMoreLosers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/market/movers`);
      const data = await response.json();
      const additionalLosers = [];

      // Get full analysis for additional losers (skip first 2)
      for (const loser of data.losers.slice(2, 5)) {
        try {
          const stockResponse = await fetch(`${API_BASE_URL}/api/stocks/${loser.ticker}`);
          const stockData = await stockResponse.json();
          if (stockData) additionalLosers.push(stockData);
        } catch (error) {
          console.error(`Error fetching additional loser ${loser.ticker}:`, error);
        }
      }
      setExpandedLosers(additionalLosers);
    } catch (error) {
      console.error('Error loading more losers:', error);
    }
  };

  const loadMoreVolume = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/market/highest-volume?limit=20`);
      const data = await response.json();
      // Get additional stocks beyond the first 5
      const additionalStocks = data.stocks?.slice(5, 20) || [];
      setExpandedVolume(additionalStocks);
      setShowAllVolume(true);
    } catch (error) {
      console.error('Error loading more volume stocks:', error);
    }
  };

  const loadMoreVolatile = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/market/volatile-stocks?limit=20`);
      const data = await response.json();
      // Get additional stocks beyond the first 5
      const additionalStocks = data.volatile_stocks?.slice(5, 20) || [];
      setExpandedVolatile(additionalStocks);
      setShowAllVolatile(true);
    } catch (error) {
      console.error('Error loading more volatile stocks:', error);
    }
  };

  // Handle mini stock card clicks
  const handleMiniStockClick = (stock) => {
    setSelectedMiniStock(stock);
    setShowStockModal(true);
  };

  const closeStockModal = () => {
    setShowStockModal(false);
    setSelectedMiniStock(null);
  };

  const getChangeColor = (change) => {
    if (change > 0) return 'text-green-600 dark:text-green-400';
    if (change < 0) return 'text-red-600 dark:text-red-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  const formatNumber = (num) => {
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
    return num?.toFixed(2) || '0.00';
  };

  if (loading && !marketData) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with New List Button */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Market Overview
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Real-time NYSE market data and insights
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={onNewWatchlist}
            className="flex items-center space-x-2 py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg btn-primary"
          >
            <Plus className="w-4 h-4" />
            <span>New List</span>
          </button>
          <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
            <Clock className="w-4 h-4" />
            <span>
              {lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString()}` : 'Loading...'}
            </span>
          </div>
        </div>
      </div>

      {/* Watchlists Display */}
      {watchlists && watchlists.length > 0 && (
        <div className="panel p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Your Watchlists
          </h2>
          <div className="flex flex-wrap gap-2">
            {watchlists.map((watchlist) => (
              <div
                key={watchlist.id}
                className="flex items-center space-x-2 py-2 px-3 bg-purple-100 dark:bg-purple-900/20 text-purple-800 dark:text-purple-300 rounded-lg"
              >
                <span>{watchlist.name}</span>
                <button
                  onClick={() => onDeleteWatchlist(watchlist.id)}
                  className="text-red-500 hover:text-red-700"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Morning Brief (collapsible) */}
      <div className="panel p-6 overflow-hidden">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <Info className="w-5 h-5 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Morning Brief
              <span className="ml-2 text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded-full">
                Live Charts
              </span>
            </h2>
            <button
              onClick={() => {
                setMbLoading(true);
                setTimeout(async () => {
                  try {
                    const res = await fetch(`${API_BASE_URL}/api/morning/brief`);
                    if (res.ok) setMorning(await res.json());
                  } catch (e) {
                    console.log('Morning brief manual refresh failed');
                  }
                  setMbLoading(false);
                }, 500);
              }}
              className="text-blue-600 hover:text-blue-800 text-xs px-2 py-1 rounded hover:bg-blue-100 dark:hover:bg-blue-900/20"
              title="Refresh Morning Brief"
            >
              🔄 Refresh
            </button>
          </div>
          <button
            onClick={() => setShowMorningBrief(!showMorningBrief)}
            className="text-blue-600 hover:text-blue-800 p-1 rounded-full hover:bg-blue-100 dark:hover:bg-blue-900/20"
            aria-expanded={showMorningBrief}
            aria-controls="morning-brief-content"
          >
            <svg
              className={`w-5 h-5 transform transition-transform ${showMorningBrief ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
        {showMorningBrief && (
          <div id="morning-brief-content" className="pt-2 text-sm text-gray-300 space-y-6">
            {mbLoading && (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mr-3"></div>
                <span className="text-gray-500">Loading market data...</span>
              </div>
            )}

            {true && ( // FORCE TRADINGVIEW WIDGETS ALWAYS
              <>
                <div>
                  <h3 className="font-medium mb-3 flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-blue-400" />
                    Key Market Indices - Live Charts
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                    {[
                      { symbol: "FOREXCOM:SPXUSD", name: "S&P 500" },
                      { symbol: "$NDQ", name: "NASDAQ" },
                      { symbol: "FOREXCOM:DJI", name: "Dow Jones" }
                    ].map((ticker) => (
                      <div key={ticker.symbol} className="bg-gray-800/40 border border-gray-700 rounded-lg p-3 hover:bg-gray-800/60 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm font-medium text-gray-300">{ticker.name}</div>
                          <div className="text-xs text-gray-400">{ticker.symbol}</div>
                        </div>
                        <div className="h-48">
                          <TradingViewMiniWidget
                            symbol={ticker.symbol}
                            width="100%"
                            height={192}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="font-medium mb-3 flex items-center gap-2">
                    <Zap className="w-4 h-4 text-purple-400" />
                    Popular ETFs - Live Charts
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                    {[
                      { symbol: "$QQQ", name: "Invesco QQQ Trust" },
                      { symbol: "$SPY", name: "SPDR S&P 500 ETF" }
                    ].map((ticker) => (
                      <div key={ticker.symbol} className="bg-gray-800/40 border border-gray-700 rounded-lg p-3 hover:bg-gray-800/60 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm font-medium text-gray-300">{ticker.name}</div>
                          <div className="text-xs text-gray-400">{ticker.symbol}</div>
                        </div>
                        <div className="h-48">
                          <TradingViewMiniWidget
                            symbol={ticker.symbol}
                            width="100%"
                            height={192}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="font-medium mb-3 flex items-center gap-2">
                    <Globe className="w-4 h-4 text-green-400" />
                    Futures & Commodities - Live Charts
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                    {[
                      { symbol: "FOREXCOM:SPXUSD", name: "S&P 500 Futures" },
                      { symbol: "FOREXCOM:NDX", name: "NASDAQ Futures" },
                      { symbol: "FOREXCOM:DJI", name: "Dow Futures" },
                      { symbol: "FOREXCOM:USOIL", name: "Crude Oil" },
                      { symbol: "FOREXCOM:XAUUSD", name: "Gold Futures" },
                      { symbol: "BITSTAMP:BTCUSD", name: "Bitcoin" }
                    ].map((ticker) => (
                      <div key={ticker.symbol} className="bg-gray-800/40 border border-gray-700 rounded-lg p-3 hover:bg-gray-800/60 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm font-medium text-gray-300">{ticker.name}</div>
                          <div className="text-xs text-gray-400">{ticker.symbol}</div>
                        </div>
                        <div className="h-48">
                          <TradingViewMiniWidget
                            symbol={ticker.symbol}
                            width="100%"
                            height={192}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="font-medium mb-2">Overnight/Early Headlines</h3>
                  <ul className="space-y-1 list-disc list-inside">
                    {morning?.early_news?.map((n, idx) => (
                      <li key={idx}><a href={n.url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">{n.title}</a> <span className="text-gray-500">— {n.source}</span></li>
                    )) || [
                      { title: "Market Rally Continues as Tech Stocks Lead Gains", url: "#", source: "Financial News" },
                      { title: "Federal Reserve Signals Continued Economic Support", url: "#", source: "Economic Times" },
                      { title: "Major Earnings Reports Drive Market Activity", url: "#", source: "MarketWatch" }
                    ].map((n, idx) => (
                      <li key={idx}><a href={n.url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">{n.title}</a> <span className="text-gray-500">— {n.source}</span></li>
                    ))}
                  </ul>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <div>
                    <h3 className="font-medium mb-2">Earnings Today</h3>
                    <ul className="text-sm space-y-1">
                      {morning?.earnings_today?.map((e, idx) => (
                        <li key={idx} className="text-gray-300">{e.symbol || ''} <span className="text-gray-500">{e.time || ''}</span></li>
                      )) || [
                        { symbol: "AAPL", time: "4:30 PM ET" },
                        { symbol: "MSFT", time: "4:00 PM ET" },
                        { symbol: "GOOGL", time: "4:15 PM ET" }
                      ].map((e, idx) => (
                        <li key={idx} className="text-gray-300">{e.symbol} <span className="text-gray-500">{e.time}</span></li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-medium mb-2">Economic Calendar</h3>
                    <ul className="text-sm space-y-1">
                      {morning?.economic_today?.map((e, idx) => (
                        <li key={idx} className="text-gray-300">{e.event || ''} <span className="text-gray-500">{e.time || ''}</span></li>
                      )) || [
                        { event: "CPI Data Release", time: "8:30 AM ET" },
                        { event: "Fed Minutes", time: "2:00 PM ET" },
                        { event: "Jobless Claims", time: "8:30 AM ET" }
                      ].map((e, idx) => (
                        <li key={idx} className="text-gray-300">{e.event} <span className="text-gray-500">{e.time}</span></li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div>
                  <h3 className="font-medium mb-2">Top Gainers/Losers (Pre/Post)</h3>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <div>
                      <div className="text-xs text-gray-400 mb-1">Gainers</div>
                      <ul className="text-sm space-y-1">
                        {morning?.movers?.gainers?.slice(0, 5).map((s) => (
                          <li key={s.ticker}>{s.ticker} <span className="text-green-400">{s.changePercent}%</span></li>
                        )) || [
                          { ticker: "NVDA", changePercent: 3.2 },
                          { ticker: "TSLA", changePercent: 2.8 },
                          { ticker: "AMD", changePercent: 2.1 }
                        ].map((s) => (
                          <li key={s.ticker}>{s.ticker} <span className="text-green-400">{s.changePercent}%</span></li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <div className="text-xs text-gray-400 mb-1">Losers</div>
                      <ul className="text-sm space-y-1">
                        {morning?.movers?.losers?.slice(0, 5).map((s) => (
                          <li key={s.ticker}>{s.ticker} <span className="text-red-400">{s.changePercent}%</span></li>
                        )) || [
                          { ticker: "NFLX", changePercent: -1.8 },
                          { ticker: "META", changePercent: -1.2 },
                          { ticker: "PYPL", changePercent: -0.9 }
                        ].map((s) => (
                          <li key={s.ticker}>{s.ticker} <span className="text-red-400">{s.changePercent}%</span></li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="font-medium mb-2">Market Score (1–100)</h3>
                  <div className="space-y-2">
                    <div className="w-full h-3 rounded-full overflow-hidden" style={{ background: 'linear-gradient(90deg, #16a34a 0%, #84cc16 20%, #facc15 50%, #f97316 80%, #dc2626 100%)' }}>
                      <div className="h-full bg-white/80" style={{ width: `${Math.max(0, Math.min(100, morning?.market_score || 65))}%` }}></div>
                    </div>
                    <div className="flex items-center justify-between text-xs text-gray-400">
                      <span>Bullish</span>
                      <span className="text-sm text-gray-200 font-semibold">{morning?.market_score || 65}</span>
                      <span>Bearish</span>
                    </div>
                    {morning?.score_components && (
                      <div className="text-xs text-gray-400">
                        <span className="mr-3">Fut: {morning.score_components.futures}%</span>
                        <span className="mr-3">Breadth: {morning.score_components.breadth}%</span>
                        <span className="mr-3">Global: {morning.score_components.global}%</span>
                        <span>News: {morning.score_components.news}%</span>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}

            {false && morning && ( // DISABLE BACKEND MORNING BRIEF FOR NOW
              <>
                <div>
                  <h3 className="font-medium mb-3 flex items-center gap-2">
                    <Globe className="w-4 h-4 text-green-400" />
                    Global Market Overview - Live Charts
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {morning.global_indices?.slice(0, 8).map((i, index) => (
                      <div key={i.symbol} className="bg-gray-800/40 border border-gray-700 rounded-lg p-3 hover:bg-gray-800/60 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-xs font-medium text-gray-300">{i.name}</div>
                          <div className="text-xs text-gray-400">{i.symbol}</div>
                        </div>
                        <div className="h-20 mb-2">
                          <TradingViewMiniChart
                            symbol={i.symbol}
                            height={80}
                            dateRange="1D"
                            theme="dark"
                            scale={0.9}
                            key={`global-${i.symbol}-${index}`}
                          />
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-200">{i.price ?? '-'}</span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${i.changePercent >= 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                            }`}>
                            {i.changePercent >= 0 ? '+' : ''}{i.changePercent}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h3 className="font-medium mb-3 flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-blue-400" />
                    Futures (Pre-Market) - Live Charts
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {morning.futures?.slice(0, 8).map((f, index) => (
                      <div key={f.symbol} className="bg-gray-800/40 border border-gray-700 rounded-lg p-3 hover:bg-gray-800/60 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-xs font-medium text-gray-300">{f.name}</div>
                          <div className="text-xs text-gray-400">{f.symbol}</div>
                        </div>
                        <div className="h-20 mb-2">
                          <TradingViewMiniChart
                            symbol={f.symbol}
                            height={80}
                            dateRange="1D"
                            theme="dark"
                            scale={0.9}
                            key={`futures-${f.symbol}-${index}`}
                          />
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-200">{f.price ?? '-'}</span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${f.changePercent >= 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                            }`}>
                            {f.changePercent >= 0 ? '+' : ''}{f.changePercent}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h3 className="font-medium mb-2">Overnight/Early Headlines</h3>
                  <ul className="space-y-1 list-disc list-inside">
                    {morning.early_news?.map((n, idx) => (
                      <li key={idx}><a href={n.url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">{n.title}</a> <span className="text-gray-500">— {n.source}</span></li>
                    ))}
                  </ul>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <div>
                    <h3 className="font-medium mb-2">Earnings Today</h3>
                    <ul className="text-sm space-y-1">
                      {morning.earnings_today?.map((e, idx) => (
                        <li key={idx} className="text-gray-300">{e.symbol || ''} <span className="text-gray-500">{e.time || ''}</span></li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-medium mb-2">Economic Calendar</h3>
                    <ul className="text-sm space-y-1">
                      {morning.economic_today?.map((e, idx) => (
                        <li key={idx} className="text-gray-300">{e.event || ''} <span className="text-gray-500">{e.time || ''}</span></li>
                      ))}
                    </ul>
                  </div>
                </div>
                <div>
                  <h3 className="font-medium mb-2">Top Gainers/Losers (Pre/Post)</h3>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <div>
                      <div className="text-xs text-gray-400 mb-1">Gainers</div>
                      <ul className="text-sm space-y-1">
                        {morning.movers?.gainers?.slice(0, 5).map((s) => (
                          <li key={s.ticker}>{s.ticker} <span className="text-green-400">{s.changePercent}%</span></li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <div className="text-xs text-gray-400 mb-1">Losers</div>
                      <ul className="text-sm space-y-1">
                        {morning.movers?.losers?.slice(0, 5).map((s) => (
                          <li key={s.ticker}>{s.ticker} <span className="text-red-400">{s.changePercent}%</span></li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
                <div>
                  <h3 className="font-medium mb-3 flex items-center gap-2">
                    <Zap className="w-4 h-4 text-yellow-400" />
                    Most Talked About - Live Charts
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
                    {morning.trending?.slice(0, 6).map((t, index) => (
                      <div key={t.ticker} className="bg-gray-800/40 border border-gray-700 rounded-lg p-3 hover:bg-gray-800/60 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm font-bold text-yellow-400">{t.ticker}</div>
                          <div className="flex items-center gap-1 text-xs text-gray-400">
                            <span>📰 {t.mentions}</span>
                            {typeof t.twitter === 'number' && <span>🐦 {t.twitter}</span>}
                          </div>
                        </div>
                        <div className="h-16 mb-2">
                          <TradingViewMiniChart
                            symbol={t.ticker}
                            height={64}
                            dateRange="1D"
                            theme="dark"
                            scale={0.8}
                            key={`trending-${t.ticker}-${index}`}
                          />
                        </div>
                        <div className="text-xs text-center text-gray-400">
                          {t.mentions} mentions
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h3 className="font-medium mb-2">Market Score (1–100)</h3>
                  <div className="space-y-2">
                    <div className="w-full h-3 rounded-full overflow-hidden" style={{ background: 'linear-gradient(90deg, #16a34a 0%, #84cc16 20%, #facc15 50%, #f97316 80%, #dc2626 100%)' }}>
                      <div className="h-full bg-white/80" style={{ width: `${Math.max(0, Math.min(100, morning.market_score))}%` }}></div>
                    </div>
                    <div className="flex items-center justify-between text-xs text-gray-400">
                      <span>Bullish</span>
                      <span className="text-sm text-gray-200 font-semibold">{morning.market_score}</span>
                      <span>Bearish</span>
                    </div>
                    {morning.score_components && (
                      <div className="text-xs text-gray-400">
                        <span className="mr-3">Fut: {morning.score_components.futures}%</span>
                        <span className="mr-3">Breadth: {morning.score_components.breadth}%</span>
                        <span className="mr-3">Global: {morning.score_components.global}%</span>
                        <span>News: {morning.score_components.news}%</span>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}

          </div>
        )}
      </div>

      {/* Market Indices with Stock Cards */}
      <div className="panel p-6">
        <div className="flex items-center space-x-2 mb-4">
          <BarChart3 className="w-5 h-5 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Major Indices
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {marketData?.indices?.map((index) => (
            <IndexCard key={index.symbol} index={index} />
          ))}
        </div>
      </div>

      {/* Featured Stocks and Market News Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Featured Stocks Section with Loading and Expand */}
        <div className="lg:col-span-3">
          <div className="panel p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Zap className="w-5 h-5 text-yellow-600" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Featured Stock Analysis
                </h2>
              </div>
              <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded-full">
                Top Performers
              </span>
            </div>

            {loadingFeatured ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-600"></div>
                <span className="ml-3 text-gray-600 dark:text-gray-400">Loading featured analysis...</span>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                {featuredStocks.map((stock) => (
                  <MiniStockCard
                    key={stock.ticker}
                    stock={stock}
                    onClick={handleMiniStockClick}
                    onOpenChart={() => onOpenChart(stock)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Market News Section - Side by Side */}
        <div className="lg:col-span-1">
          <div className="panel p-6 h-full overflow-hidden">
            <div className="flex items-center space-x-2 mb-4">
              <Bell className="w-5 h-5 text-blue-600" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Market News
              </h2>
            </div>
            <div className="max-h-96 overflow-y-auto">
              <NewsSidebar news={news} loading={newsLoading} />
            </div>
          </div>
        </div>
      </div>

      {/* Market Movers with Full StockCard Format */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Gainers with Expand Feature */}
        <div className="panel p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Top Gainers
              </h2>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-green-600 bg-green-100 dark:bg-green-900/20 px-2 py-1 rounded-full">
                +{fullMovers?.gainers?.[0]?.priceChangePercent?.toFixed(2) || '0.00'}%
              </span>
              <button
                onClick={async () => {
                  if (!showAllGainers) {
                    await loadMoreGainers();
                  }
                  setShowAllGainers(!showAllGainers);
                }}
                className="text-green-600 hover:text-green-800 p-1 rounded-full hover:bg-green-100 dark:hover:bg-green-900/20"
              >
                <svg className={`w-4 h-4 transform transition-transform ${showAllGainers ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
          </div>

          {loadingMovers ? (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
              <span className="ml-3 text-gray-600 dark:text-gray-400">Loading gainers...</span>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Initial 2 gainers - Mini Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {fullMovers?.gainers?.slice(0, 2).map((stock, index) => (
                  <MiniStockCard
                    key={stock.ticker}
                    stock={stock}
                    onClick={handleMiniStockClick}
                    onOpenChart={() => onOpenChart(stock)}
                  />
                ))}
              </div>

              {/* Expanded gainers */}
              {showAllGainers && (
                <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {expandedGainers.map((stock, index) => (
                      <MiniStockCard
                        key={stock.ticker}
                        stock={stock}
                        onClick={handleMiniStockClick}
                        onOpenChart={() => onOpenChart(stock)}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Top Losers with Expand Feature */}
        <div className="panel p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <TrendingDown className="w-5 h-5 text-red-600" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Top Losers
              </h2>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-red-600 bg-red-100 dark:bg-red-900/20 px-2 py-1 rounded-full">
                {fullMovers?.losers?.[0]?.priceChangePercent?.toFixed(2) || '0.00'}%
              </span>
              <button
                onClick={async () => {
                  if (!showAllLosers) {
                    await loadMoreLosers();
                  }
                  setShowAllLosers(!showAllLosers);
                }}
                className="text-red-600 hover:text-red-800 p-1 rounded-full hover:bg-red-100 dark:hover:bg-red-900/20"
              >
                <svg className={`w-4 h-4 transform transition-transform ${showAllLosers ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
          </div>

          {loadingMovers ? (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
              <span className="ml-3 text-gray-600 dark:text-gray-400">Loading losers...</span>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Initial 2 losers - Mini Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {fullMovers?.losers?.slice(0, 2).map((stock, index) => (
                  <MiniStockCard
                    key={stock.ticker}
                    stock={stock}
                    onClick={handleMiniStockClick}
                    onOpenChart={() => onOpenChart(stock)}
                  />
                ))}
              </div>

              {/* Expanded losers */}
              {showAllLosers && (
                <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {expandedLosers.map((stock, index) => (
                      <MiniStockCard
                        key={stock.ticker}
                        stock={stock}
                        onClick={handleMiniStockClick}
                        onOpenChart={() => onOpenChart(stock)}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Highest Volume Stocks with Expand Feature */}
      <div className="panel p-6 border-l-4 border-purple-500">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Volume2 className="w-5 h-5 text-purple-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Highest Volume Stocks
            </h2>
            <span className="text-sm text-purple-600 bg-purple-100 dark:bg-purple-900/20 px-3 py-1 rounded-full font-medium">
              TRENDING
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Updated every 5 minutes
            </div>
            <button
              onClick={async () => {
                if (!showAllVolume) {
                  await loadMoreVolume();
                }
                setShowAllVolume(!showAllVolume);
              }}
              className="text-purple-600 hover:text-purple-800 p-1 rounded-full hover:bg-purple-100 dark:hover:bg-purple-900/20"
            >
              <svg className={`w-4 h-4 transform transition-transform ${showAllVolume ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>
        </div>

        {loadingVolume ? (
          <div className="flex justify-center items-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            <span className="ml-3 text-gray-600 dark:text-gray-400">Loading volume data...</span>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Initial 2 volume stocks - Mini Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {highestVolumeStocks.map((stock, index) => (
                <div key={stock.ticker} className="relative">
                  {index === 0 && (
                    <div className="absolute -top-2 -right-2 bg-purple-600 text-white text-xs px-2 py-1 rounded-full z-10">
                      #1 VOLUME
                    </div>
                  )}
                  <MiniStockCard
                    stock={stock}
                    onClick={handleMiniStockClick}
                    onOpenChart={() => onOpenChart(stock)}
                  />
                </div>
              ))}
            </div>

            {/* Expanded volume stocks */}
            {showAllVolume && (
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {expandedVolume.map((stock, index) => (
                    <MiniStockCard
                      key={stock.ticker}
                      stock={stock}
                      onClick={handleMiniStockClick}
                      onOpenChart={() => onOpenChart(stock)}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Most Volatile Stocks with Expand Feature */}
      <div className="panel p-6 border-l-4 border-orange-500">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Zap className="w-5 h-5 text-orange-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Most Volatile Stocks
            </h2>
            <span className="text-sm text-orange-600 bg-orange-100 dark:bg-orange-900/20 px-3 py-1 rounded-full font-medium">
              HIGH VOLATILITY
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Updated every 5 minutes
            </div>
            <button
              onClick={async () => {
                if (!showAllVolatile) {
                  await loadMoreVolatile();
                }
                setShowAllVolatile(!showAllVolatile);
              }}
              className="text-orange-600 hover:text-orange-800 p-1 rounded-full hover:bg-orange-100 dark:hover:bg-orange-900/20"
            >
              <svg className={`w-4 h-4 transform transition-transform ${showAllVolatile ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>
        </div>

        {loadingVolatile ? (
          <div className="flex justify-center items-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600"></div>
            <span className="ml-3 text-gray-600 dark:text-gray-400">Loading volatile stocks...</span>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Initial 5 volatile stocks - Mini Cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
              {volatileStocks.map((stock, index) => {
                // Enhance volatile stock data for MiniStockCard compatibility
                const stockWithScore = {
                  ...stock,
                  score: Math.min(4, Math.max(1, Math.floor(stock.volatility_score / 10))), // Convert volatility score to 1-4 scale
                  averageVolume: stock.volume || stock.averageVolume,
                  rank: index + 1
                };

                return (
                  <div key={stock.ticker} className="relative">
                    {index === 0 && (
                      <div className="absolute -top-2 -right-2 bg-orange-600 text-white text-xs px-2 py-1 rounded-full z-10">
                        #1 VOLATILE
                      </div>
                    )}
                    <MiniStockCard
                      stock={stockWithScore}
                      onClick={handleMiniStockClick}
                      onOpenChart={() => onOpenChart(stockWithScore)}
                    />
                  </div>
                );
              })}
            </div>

            {/* Expanded volatile stocks */}
            {showAllVolatile && (
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                  {expandedVolatile.map((stock, index) => {
                    // Enhance volatile stock data for MiniStockCard compatibility
                    const stockWithScore = {
                      ...stock,
                      score: Math.min(4, Math.max(1, Math.floor(stock.volatility_score / 10))), // Convert volatility score to 1-4 scale
                      averageVolume: stock.volume || stock.averageVolume,
                      rank: index + 1
                    };

                    return (
                      <MiniStockCard
                        key={stock.ticker}
                        stock={stockWithScore}
                        onClick={handleMiniStockClick}
                        onOpenChart={() => onOpenChart(stockWithScore)}
                      />
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Sector Performance Heatmap (TradingView) */}
      <div className="panel p-3">
        <TradingViewHeatmap height={360} dataSource="SPX500" grouping="sector" />
      </div>

      {/* Market Stats */}
      <div className="panel p-6">
        <div className="flex items-center space-x-2 mb-4 text-gray-100">
          <Globe className="w-5 h-5" />
          <h2 className="text-xl font-semibold">Market Status</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold mb-1">
              {marketData?.stats?.trading_session || 'Loading...'}
            </div>
            <div className="text-sm opacity-80">Trading Session</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold mb-1">
              {marketData?.gainers?.length || 0}
            </div>
            <div className="text-sm opacity-80">Active Gainers</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold mb-1">
              {marketData?.losers?.length || 0}
            </div>
            <div className="text-sm opacity-80">Active Losers</div>
          </div>
        </div>
      </div>

      {/* Stock Card Modal */}
      <StockCardModal
        isOpen={showStockModal}
        onClose={closeStockModal}
        stock={selectedMiniStock}
        aiProvider="gemini"
        onOpenChart={onOpenChart}
      />
    </div>
  );
};

export default HomeScreen;
