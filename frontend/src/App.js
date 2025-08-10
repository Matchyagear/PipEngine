import React, { useState, useEffect, useCallback } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Volume2,
  Target,
  RefreshCw,
  Filter,
  BarChart3,
  ExternalLink,
  Brain,
  Star,
  Eye,
  Moon,
  Sun,
  Settings,
  Plus,
  Edit,
  Trash2,
  Download,
  Bell,
  PlayCircle,
  PauseCircle,
  Smartphone,
  Monitor,
  Zap,
  TrendingUpIcon,
  AlertTriangle,
  X,
  Home,
  Globe,
  PieChart
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { NewsSidebar, NewsTab, StockNews } from './NewsComponents';
import StockDetailModal from './StockDetailModal';
import HomeScreen from './HomeScreen';
import WatchlistModal from './WatchlistModal';
import StockCard from './StockCard';
import MiniStockCard from './MiniStockCard';
import StockCardModal from './StockCardModal';
import Portfolio from './Portfolio';
import AIChat from './AIChat';
import WatchlistTab from './WatchlistTab';
import ChartTab from './ChartTab';
import ScreenerTestTab from "./ScreenerTestTab";
import Logo from "./components/Logo";
import "./App.css";
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  // Core state
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('home');
  const [sortBy, setSortBy] = useState('score');
  const [filterBy, setFilterBy] = useState('all');
  const [isRefreshing, setIsRefreshing] = useState(false);

  // New feature states
  const [darkMode, setDarkMode] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(300);
  const [aiProvider, setAiProvider] = useState('gemini');
  const [watchlists, setWatchlists] = useState([]);
  const [currentWatchlist, setCurrentWatchlist] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showWatchlistModal, setShowWatchlistModal] = useState(false);
  const [newWatchlistName, setNewWatchlistName] = useState('');
  const [newWatchlistTickers, setNewWatchlistTickers] = useState('');
  const [alerts, setAlerts] = useState([]);
  const [showMobileView, setShowMobileView] = useState(false);
  const [showAIChat, setShowAIChat] = useState(false);
  const [chartSymbol, setChartSymbol] = useState('AAPL');

  // Search functionality
  const [searchTicker, setSearchTicker] = useState('');
  const [searchResult, setSearchResult] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchResult, setShowSearchResult] = useState(false);

  // News functionality
  const [news, setNews] = useState([]);
  const [newsLoading, setNewsLoading] = useState(false);
  const [newsSearchQuery, setNewsSearchQuery] = useState('');
  const [isSearchingNews, setIsSearchingNews] = useState(false);
  const [selectedStock, setSelectedStock] = useState(null);
  const [showStockDetail, setShowStockDetail] = useState(false);
  const [showShadowModal, setShowShadowModal] = useState(false);
  const [selectedShadowStock, setSelectedShadowStock] = useState(null);

  // Auto-refresh effect
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchStocks();
      }, refreshInterval * 1000);

      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  // Load user preferences on mount
  useEffect(() => {
    loadUserPreferences();
    fetchWatchlists();
    fetchAlerts();
    fetchNews(); // Load general news on startup

    // Check if mobile
    const checkMobile = () => {
      setShowMobileView(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Apply dark mode
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const loadUserPreferences = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/preferences`);
      const prefs = await response.json();
      setDarkMode(prefs.dark_mode);
      setAutoRefresh(prefs.auto_refresh);
      setRefreshInterval(prefs.refresh_interval);
      setAiProvider(prefs.ai_provider);
    } catch (error) {
      console.error('Error loading preferences:', error);
    }
  };

  const saveUserPreferences = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/preferences`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'default',
          dark_mode: darkMode,
          auto_refresh: autoRefresh,
          refresh_interval: refreshInterval,
          ai_provider: aiProvider,
          notifications_enabled: true
        })
      });
    } catch (error) {
      console.error('Error saving preferences:', error);
    }
  };

  const fetchStocks = async () => {
    try {
      setLoading(true);
      let url = `${API_BASE_URL}/api/stocks/scan`;

      if (currentWatchlist) {
        url = `${API_BASE_URL}/api/watchlists/${currentWatchlist.id}/scan`;
      }

      const response = await fetch(url);
      const data = await response.json();
      setStocks(data.stocks || []);
    } catch (error) {
      console.error('Error fetching stocks:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchWatchlists = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/watchlists`);
      const data = await response.json();
      setWatchlists(data.watchlists || []);
    } catch (error) {
      console.error('Error fetching watchlists:', error);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/alerts`);
      const data = await response.json();
      setAlerts(data.alerts || []);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  const createWatchlist = async () => {
    if (!newWatchlistName || !newWatchlistTickers) return;

    try {
      const tickers = newWatchlistTickers.split(',').map(t => t.trim().toUpperCase());
      const response = await fetch(`${API_BASE_URL}/api/watchlists`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newWatchlistName,
          tickers: tickers
        })
      });

      if (response.ok) {
        setNewWatchlistName('');
        setNewWatchlistTickers('');
        setShowWatchlistModal(false);
        fetchWatchlists();
      }
    } catch (error) {
      console.error('Error creating watchlist:', error);
    }
  };

  const deleteWatchlist = async (watchlistId) => {
    try {
      await fetch(`${API_BASE_URL}/api/watchlists/${watchlistId}`, {
        method: 'DELETE'
      });
      fetchWatchlists();
      if (currentWatchlist && currentWatchlist.id === watchlistId) {
        setCurrentWatchlist(null);
      }
    } catch (error) {
      console.error('Error deleting watchlist:', error);
    }
  };

  const exportData = async (format = 'json') => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/export/stocks?format=${format}`);
      const data = await response.json();

      if (format === 'csv') {
        const blob = new Blob([data.data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = data.filename;
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `shadowbeta_analysis_${Date.now()}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  };

  const refreshStocks = async () => {
    setIsRefreshing(true);
    await fetchStocks();
    setIsRefreshing(false);
  };

  const searchStock = async () => {
    if (!searchTicker.trim()) return;

    try {
      setIsSearching(true);
      const response = await fetch(`${API_BASE_URL}/api/stocks/${searchTicker.toUpperCase()}`);
      const data = await response.json();

      if (response.ok) {
        // Add rank as 1 for search results
        data.rank = 1;
        setSearchResult(data);
        setShowSearchResult(true);
        setActiveTab('search');
      } else {
        alert(`Stock ${searchTicker.toUpperCase()} not found or error occurred`);
      }
    } catch (error) {
      console.error('Error searching stock:', error);
      alert('Error searching for stock. Please try again.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter') {
      searchStock();
    }
  };

  const fetchNews = async () => {
    try {
      setNewsLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/news/general?limit=20`);
      const data = await response.json();
      setNews(data.news || []);
    } catch (error) {
      console.error('Error fetching news:', error);
    } finally {
      setNewsLoading(false);
    }
  };

  const searchNews = async () => {
    if (!newsSearchQuery.trim()) return;

    try {
      setIsSearchingNews(true);
      const response = await fetch(`${API_BASE_URL}/api/news/search?q=${encodeURIComponent(newsSearchQuery)}&limit=30`);
      const data = await response.json();
      setNews(data.news || []);
      setActiveTab('news');
    } catch (error) {
      console.error('Error searching news:', error);
    } finally {
      setIsSearchingNews(false);
    }
  };

  const handleNewsSearchKeyPress = (e) => {
    if (e.key === 'Enter') {
      searchNews();
    }
  };

  const openStockDetail = (stock) => {
    setSelectedStock(stock);
    setShowStockDetail(true);
  };

  const openChartForStock = (stock) => {
    setChartSymbol(stock.ticker || stock.symbol);
    setActiveTab('chart');
  };

  const getFilteredAndSortedStocks = () => {
    // If showing search result, return only the search result
    if (showSearchResult && searchResult) {
      return [searchResult];
    }

    let filtered = stocks;

    // Apply filters
    if (filterBy === '4out4') {
      filtered = stocks.filter(stock => stock.score === 4);
    } else if (filterBy === '3plus') {
      filtered = stocks.filter(stock => stock.score >= 3);
    } else if (filterBy === 'oversold') {
      filtered = stocks.filter(stock => stock.passes?.oversold);
    } else if (filterBy === 'breakout') {
      filtered = stocks.filter(stock => stock.passes?.breakout);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'score':
          return b.score - a.score;
        case 'ticker':
          return a.ticker.localeCompare(b.ticker);
        case 'volume':
          return b.averageVolume - a.averageVolume;
        case 'change':
          return b.priceChangePercent - a.priceChangePercent;
        case 'rsi':
          return a.RSI - b.RSI; // Lower RSI first (more oversold)
        default:
          return b.score - a.score;
      }
    });

    return filtered;
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

  const SettingsModal = () => (
    <AnimatePresence>
      {showSettings && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setShowSettings(false)}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full max-h-90vh overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Settings</h2>

            {/* Dark Mode Toggle */}
            <div className="flex items-center justify-between mb-4">
              <label className="text-gray-700 dark:text-gray-300">Dark Mode</label>
              <button
                onClick={() => setDarkMode(!darkMode)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${darkMode ? 'bg-blue-600' : 'bg-gray-300'
                  }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${darkMode ? 'translate-x-6' : 'translate-x-1'
                    }`}
                />
              </button>
            </div>

            {/* Auto Refresh Toggle */}
            <div className="flex items-center justify-between mb-4">
              <label className="text-gray-700 dark:text-gray-300">Auto Refresh</label>
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${autoRefresh ? 'bg-blue-600' : 'bg-gray-300'
                  }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${autoRefresh ? 'translate-x-6' : 'translate-x-1'
                    }`}
                />
              </button>
            </div>

            {/* Refresh Interval */}
            <div className="mb-4">
              <label className="block text-gray-700 dark:text-gray-300 mb-2">
                Refresh Interval (seconds)
              </label>
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value={60}>1 minute</option>
                <option value={300}>5 minutes</option>
                <option value={900}>15 minutes</option>
                <option value={1800}>30 minutes</option>
              </select>
            </div>

            {/* AI Provider */}
            <div className="mb-6">
              <label className="block text-gray-700 dark:text-gray-300 mb-2">
                AI Provider
              </label>
              <select
                value={aiProvider}
                onChange={(e) => setAiProvider(e.target.value)}
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="gemini">Google Gemini</option>
                <option value="openai">OpenAI GPT</option>
              </select>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-2">
              <button
                onClick={() => {
                  saveUserPreferences();
                  setShowSettings(false);
                }}
                className="flex-1 py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg btn-primary"
              >
                Save Settings
              </button>
              <button
                onClick={() => setShowSettings(false)}
                className="py-2 px-4 bg-gray-600 hover:bg-gray-700 text-white rounded-lg btn-secondary"
              >
                Cancel
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );



  const filteredStocks = getFilteredAndSortedStocks();

  return (
    <div className={`min-h-screen ${darkMode ? 'dark' : ''} bg-carbon-900 text-gray-100 transition-colors carbon`}>
      {/* Enhanced Header - Made Sticky/Floating */}
      <header className="sticky top-0 z-50 bg-carbon-800/90 border-b border-carbon-700 shadow-sm backdrop-blur-sm">
        <div className="w-full px-0 py-3">
          <div className="flex flex-col lg:flex-row gap-2 lg:items-center justify-start">
            {/* Left Side - Logo and Title */}
            <div className="flex items-center space-x-2">
              <Logo size="lg" showText={false} src="/pipengine_logo.png" />
              {autoRefresh && (
                <p className="text-xs text-green-600 dark:text-green-400">
                  Auto-refreshing every {refreshInterval / 60} minutes
                </p>
              )}
            </div>

            {/* Center - Global Search */}
            <div className="max-w-md ml-0">
              <div className="relative">
                <input
                  type="text"
                  value={searchTicker}
                  onChange={(e) => setSearchTicker(e.target.value.toUpperCase())}
                  onKeyPress={handleSearchKeyPress}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-2 pr-10 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Search any stock ticker (e.g., AAPL, TSLA)"
                />
                <button
                  onClick={searchStock}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Navigation Tabs in Header Center */}
            <div className="flex items-center space-x-1 bg-gray-100 dark:bg-gray-700 p-1 rounded-lg">
              <button
                onClick={() => {
                  setActiveTab('home');
                  setCurrentWatchlist(null);
                  setShowSearchResult(false);
                }}
                className={`flex items-center justify-center space-x-2 py-2 px-3 rounded-md transition-colors text-sm ${activeTab === 'home'
                  ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
              >
                <Home className="w-4 h-4" />
                <span>Home</span>
              </button>

              <button
                onClick={() => {
                  setActiveTab('shadow');
                  setCurrentWatchlist(null);
                  setShowSearchResult(false);
                  fetchStocks();
                }}
                className={`flex items-center justify-center space-x-2 py-2 px-3 rounded-md transition-colors text-sm ${activeTab === 'shadow' && !currentWatchlist && !showSearchResult
                  ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
              >
                <Eye className="w-4 h-4" />
                <span>Shadow's Picks</span>
              </button>

              <button
                onClick={() => {
                  setActiveTab('portfolio');
                  setCurrentWatchlist(null);
                  setShowSearchResult(false);
                }}
                className={`flex items-center justify-center space-x-2 py-2 px-3 rounded-md transition-colors text-sm ${activeTab === 'portfolio'
                  ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
              >
                <PieChart className="w-4 h-4" />
                <span>Portfolio</span>
              </button>

              <button
                onClick={() => {
                  setActiveTab('watchlist');
                  setCurrentWatchlist(null);
                  setShowSearchResult(false);
                }}
                className={`flex items-center justify-center space-x-2 py-2 px-3 rounded-md transition-colors text-sm ${activeTab === 'watchlist'
                  ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
              >
                <Star className="w-4 h-4" />
                <span>Watchlist</span>
              </button>

              <button
                onClick={() => {
                  setActiveTab('news');
                  setCurrentWatchlist(null);
                  setShowSearchResult(false);
                  fetchNews();
                }}
                className={`flex items-center justify-center space-x-2 py-2 px-3 rounded-md transition-colors text-sm ${activeTab === 'news'
                  ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
              >
                <Bell className="w-4 h-4" />
                <span>News</span>
              </button>

              <button
                onClick={() => {
                  setActiveTab('chart');
                  setCurrentWatchlist(null);
                  setShowSearchResult(false);
                }}
                className={`flex items-center justify-center space-x-2 py-2 px-3 rounded-md transition-colors text-sm ${activeTab === 'chart'
                  ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
              >
                <BarChart3 className="w-4 h-4" />
                <span>Chart</span>
              </button>

              <button
                onClick={() => {
                  setActiveTab("screener");
                  setCurrentWatchlist(null);
                  setShowSearchResult(false);
                }}
                className={`flex items-center justify-center space-x-2 py-2 px-3 rounded-md transition-colors text-sm ${activeTab === "screener"
                  ? "bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                  }`}
              >
                <Filter className="w-4 h-4" />
                <span>Screener</span>
              </button>
            </div>

            {/* Right Side - Controls */}
            <div className="flex items-center space-x-2 ml-auto pr-2">
              {/* AI Chat Button */}
              <button
                onClick={() => setShowAIChat(!showAIChat)}
                className={`p-2 transition-colors rounded-lg ${showAIChat
                  ? "text-blue-700 bg-blue-200 dark:text-blue-300 dark:bg-blue-700"
                  : "text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 bg-blue-100 dark:bg-blue-900/20 hover:bg-blue-200 dark:hover:bg-blue-800/30"
                  }`}
                title="AI Chat"
              >
                <Brain className="w-5 h-5" />
              </button>

              {/* Mobile/Desktop Toggle */}
              <button
                onClick={() => setShowMobileView(!showMobileView)}
                className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
              >
                {showMobileView ? <Monitor className="w-5 h-5" /> : <Smartphone className="w-5 h-5" />}
              </button>

              {/* Dark Mode Toggle */}
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
              >
                {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>

              {/* Settings */}
              <button
                onClick={() => setShowSettings(true)}
                className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
              >
                <Settings className="w-5 h-5" />
              </button>

              {/* Export */}
              <button
                onClick={() => exportData("json")}
                className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
              >
                <Download className="w-5 h-5" />
              </button>

              {/* Refresh */}
              <button
                onClick={refreshStocks}
                disabled={isRefreshing}
                className="p-2 text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 disabled:opacity-50"
              >
                <RefreshCw className={`w-5 h-5 ${isRefreshing ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">

        {/* News Search Box (only show on news tab) */}
        {activeTab === 'news' && (
          <div className="flex items-center justify-center mb-6">
            <div className="flex items-center space-x-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2">
              <input
                type="text"
                value={newsSearchQuery}
                onChange={(e) => setNewsSearchQuery(e.target.value)}
                onKeyPress={handleNewsSearchKeyPress}
                placeholder="Search news (e.g., Bitcoin, Tesla)"
                className="bg-transparent outline-none text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 text-sm"
                style={{ width: '200px' }}
              />
              <button
                onClick={searchNews}
                disabled={isSearchingNews || !newsSearchQuery.trim()}
                className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 disabled:opacity-50"
              >
                {isSearchingNews ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Watchlist Tabs (only show on stocks tab) */}
        {activeTab !== 'news' && activeTab !== 'home' && activeTab !== 'portfolio' && (
          <div className="flex items-center space-x-2">
            {watchlists.map((watchlist) => (
              <button
                key={watchlist.id}
                onClick={() => {
                  setCurrentWatchlist(watchlist);
                  setActiveTab('watchlist');
                  setShowSearchResult(false);
                  fetchStocks();
                }}
                className={`flex items-center space-x-2 py-2 px-3 rounded-lg transition-colors ${currentWatchlist?.id === watchlist.id
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                  }`}
              >
                <Star className="w-4 h-4" />
                <span>{watchlist.name}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteWatchlist(watchlist.id);
                  }}
                  className="text-red-400 hover:text-red-600"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </button>
            ))}

            <button
              onClick={() => setShowWatchlistModal(true)}
              className="flex items-center space-x-2 py-2 px-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg btn-primary"
            >
              <Plus className="w-4 h-4" />
              <span>New List</span>
            </button>
          </div>
        )}

        <div className="flex gap-6">
          {/* Main Content Area */}
          <div className="flex-1">
            {/* Content Based on Active Tab */}
            {activeTab === 'home' ? (
              <HomeScreen
                onNewWatchlist={() => setShowWatchlistModal(true)}
                watchlists={watchlists}
                onDeleteWatchlist={deleteWatchlist}
                news={news}
                newsLoading={newsLoading}
                onOpenChart={openChartForStock}
              />
            ) : activeTab === 'portfolio' ? (
              <Portfolio />
            ) : activeTab === 'watchlist' ? (
              <WatchlistTab
                watchlists={watchlists}
                setWatchlists={setWatchlists}
                onNewWatchlist={(importedTickers = '') => {
                  if (importedTickers) {
                    setNewWatchlistTickers(importedTickers);
                    setNewWatchlistName('Imported Watchlist');
                  }
                  setShowWatchlistModal(true);
                }}
                onDeleteWatchlist={deleteWatchlist}
                fetchStocks={fetchStocks}
                aiProvider={aiProvider}
                onOpenChart={openChartForStock}
              />
            ) : activeTab === 'news' ? (
              <NewsTab
                news={news}
                loading={newsLoading}
                searchQuery={newsSearchQuery}
              />
            ) : activeTab === 'chart' ? (
              <ChartTab initialSymbol={chartSymbol} />
            ) : activeTab === "screener" ? (
              <ScreenerTestTab onOpenChart={openChartForStock} />
            ) : (
              <>
                {/* Enhanced Controls */}
                <div className="flex flex-wrap gap-4 mb-6">
                  <div className="flex items-center space-x-2">
                    <Filter className="w-4 h-4 text-gray-500" />
                    <select
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value)}
                      className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    >
                      <option value="score">Sort by Score</option>
                      <option value="ticker">Sort by Ticker</option>
                      <option value="volume">Sort by Volume</option>
                      <option value="change">Sort by Change</option>
                      <option value="rsi">Sort by RSI</option>
                    </select>
                  </div>

                  <div className="flex items-center space-x-2">
                    <BarChart3 className="w-4 h-4 text-gray-500" />
                    <select
                      value={filterBy}
                      onChange={(e) => setFilterBy(e.target.value)}
                      className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    >
                      <option value="all">All Stocks</option>
                      <option value="4out4">4/4 Only</option>
                      <option value="3plus">3+ Score</option>
                      <option value="oversold">Oversold</option>
                      <option value="breakout">Breakout</option>
                    </select>
                  </div>

                  {/* Auto-refresh indicator */}
                  <div className="flex items-center space-x-2">
                    {autoRefresh ? (
                      <PlayCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <PauseCircle className="w-4 h-4 text-red-500" />
                    )}
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      Auto-refresh: {autoRefresh ? 'ON' : 'OFF'}
                    </span>
                  </div>
                </div>

                {/* Stock Grid */}
                {loading ? (
                  <div className="flex justify-center items-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                  </div>
                ) : (
                  <>
                    {/* Search Result Header */}
                    {showSearchResult && searchResult && (
                      <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-700">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-300">
                              Search Result for "{searchResult.ticker}"
                            </h3>
                            <p className="text-sm text-blue-600 dark:text-blue-400">
                              {searchResult.companyName}
                            </p>
                          </div>
                          <button
                            onClick={() => {
                              setShowSearchResult(false);
                              setSearchResult(null);
                              setSearchTicker('');
                              setActiveTab('shadow');
                            }}
                            className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200"
                          >
                            <X className="w-5 h-5" />
                          </button>
                        </div>
                      </div>
                    )}

                    <div className={showMobileView ? 'space-y-4' : 'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4'}>
                      {filteredStocks.length > 0 ? (
                        filteredStocks.map((stock) => (
                          <MiniStockCard
                            key={stock.ticker}
                            stock={stock}
                            onClick={(s) => { setSelectedShadowStock(s); setShowShadowModal(true); }}
                            onOpenChart={() => openChartForStock(stock)}
                          />
                        ))
                      ) : (
                        <div className="col-span-full text-center py-12">
                          <p className="text-gray-500 dark:text-gray-400 text-lg">
                            {showSearchResult ? 'Stock not found or error occurred.' : 'No stocks match your current filters.'}
                          </p>
                        </div>
                      )}
                    </div>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      <SettingsModal />
      <WatchlistModal
        isOpen={showWatchlistModal}
        onClose={() => setShowWatchlistModal(false)}
        onSubmit={createWatchlist}
        newWatchlistName={newWatchlistName}
        setNewWatchlistName={setNewWatchlistName}
        newWatchlistTickers={newWatchlistTickers}
        setNewWatchlistTickers={setNewWatchlistTickers}
      />

      {/* Stock Detail Modal */}
      <StockDetailModal
        stock={selectedStock}
        isOpen={showStockDetail}
        onClose={() => setShowStockDetail(false)}
        aiProvider={aiProvider}
        API_BASE_URL={API_BASE_URL}
      />

      {/* Shadow's Picks Stock Card Modal (universal StockCard) */}
      <StockCardModal
        isOpen={showShadowModal}
        onClose={() => { setShowShadowModal(false); setSelectedShadowStock(null); }}
        stock={selectedShadowStock}
        aiProvider={aiProvider}
        onOpenChart={openChartForStock}
      />

      {/* AI Chat Component - Controlled by Header Button */}
      <AIChat isOpen={showAIChat} setIsOpen={setShowAIChat} />

      {/* Fixed Export Menu - Smaller and Semi-transparent */}
      <div className="fixed bottom-6 right-6 z-40">
        <div className="flex flex-col space-y-3">
          <button
            onClick={() => exportData('csv')}
            className="flex items-center space-x-1 py-1.5 px-2 bg-green-600 hover:bg-green-700 text-white rounded-md shadow-lg btn-success transition-all opacity-60 hover:opacity-80 text-xs"
            title="Export CSV"
          >
            <Download className="w-3 h-3" />
            <span className="text-xs font-medium">CSV</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
