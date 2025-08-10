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
    // Load only lightweight overview first for fast first paint
    fetchMarketData();

    // Stagger heavier requests to reduce initial load burst
    const t1 = setTimeout(() => fetchFullMovers(), 2500);
    const t2 = setTimeout(() => fetchHighestVolumeStocks(), 4000);
    const t3 = setTimeout(() => fetchVolatileStocks(), 5500);
    const t4 = setTimeout(() => fetchFeaturedStocks(), 7000);

    // Refresh every 5 minutes (stagger inside the tick as well)
    const interval = setInterval(() => {
      fetchMarketData();
      setTimeout(() => fetchFullMovers(), 500);
      setTimeout(() => fetchHighestVolumeStocks(), 1000);
      setTimeout(() => fetchVolatileStocks(), 1500);
      setTimeout(() => fetchFeaturedStocks(), 2000);
    }, 300000); // 5 minutes

    return () => {
      clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); clearTimeout(t4);
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    const fetchMB = async () => {
      try {
        setMbLoading(true);
        const res = await fetch(`${API_BASE_URL}/api/morning/brief`);
        if (res.ok) setMorning(await res.json());
      } catch (e) {
      } finally { setMbLoading(false); }
    };
    fetchMB();
  }, []);

  const fetchMarketData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/market/overview`);
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
      const response = await fetch(`${API_BASE_URL}/api/stocks/scan`);
      const data = await response.json();
      // Reduced to top 2 performing stocks for featured section
      setFeaturedStocks(data.stocks?.slice(0, 2) || []);
    } catch (error) {
      console.error('Error fetching featured stocks:', error);
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
            </h2>
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
          <div id="morning-brief-content" className="pt-2 text-sm text-gray-300 space-y-4">
            {mbLoading && <div className="text-gray-500">Loading...</div>}
            {morning && (
              <>
                <div>
                  <h3 className="font-medium mb-2">Global Market Overview</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
                    {morning.global_indices?.map((i) => (
                      <div key={i.symbol} className="bg-gray-800/40 border border-gray-700 rounded-md px-3 py-2">
                        <div className="text-xs text-gray-400">{i.name}</div>
                        <div className="text-sm">{i.price ?? '-'} <span className={i.changePercent>=0? 'text-green-400':'text-red-400'}>({i.changePercent}%)</span></div>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h3 className="font-medium mb-2">Futures (Pre-Market)</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
                    {morning.futures?.map((f) => (
                      <div key={f.symbol} className="bg-gray-800/40 border border-gray-700 rounded-md px-3 py-2">
                        <div className="text-xs text-gray-400">{f.name}</div>
                        <div className="text-sm">{f.price ?? '-'} <span className={f.changePercent>=0? 'text-green-400':'text-red-400'}>({f.changePercent}%)</span></div>
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
                      {morning.earnings_today?.map((e, idx)=> (
                        <li key={idx} className="text-gray-300">{e.symbol || ''} <span className="text-gray-500">{e.time || ''}</span></li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-medium mb-2">Economic Calendar</h3>
                    <ul className="text-sm space-y-1">
                      {morning.economic_today?.map((e, idx)=> (
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
                        {morning.movers?.gainers?.slice(0,5).map((s)=> (
                          <li key={s.ticker}>{s.ticker} <span className="text-green-400">{s.changePercent}%</span></li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <div className="text-xs text-gray-400 mb-1">Losers</div>
                      <ul className="text-sm space-y-1">
                        {morning.movers?.losers?.slice(0,5).map((s)=> (
                          <li key={s.ticker}>{s.ticker} <span className="text-red-400">{s.changePercent}%</span></li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
                <div>
                  <h3 className="font-medium mb-2">Most Talked About (From Headlines)</h3>
                  <div className="flex flex-wrap gap-2">
                    {morning.trending?.map((t)=> (
                      <span key={t.ticker} className="px-2 py-1 text-xs rounded-md border border-gray-700">{t.ticker} · {t.mentions}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <h3 className="font-medium mb-2">Market Score (1–100)</h3>
                  <div className="flex items-center gap-3">
                    <div className="text-2xl font-semibold">{morning.market_score}</div>
                    <div className="text-xs text-gray-400">Bearish > 50 · Bullish < 50</div>
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
