import React, { useState, useEffect, useCallback, useRef } from 'react';
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
import AuthPage from "./components/AuthPage";
import ShadowbotPage from "./ShadowbotPage";
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
  const [refreshInterval, setRefreshInterval] = useState(600); // 10 minutes instead of 5
  const [aiProvider, setAiProvider] = useState('gemini');

  // WebSocket connection for real-time updates
  const [websocket, setWebsocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [watchlists, setWatchlists] = useState([]);
  const [currentWatchlist, setCurrentWatchlist] = useState(null);
  const [watchlistsBackendAvailable, setWatchlistsBackendAvailable] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [showWatchlistModal, setShowWatchlistModal] = useState(false);
  const [newWatchlistName, setNewWatchlistName] = useState('');
  const [newWatchlistTickers, setNewWatchlistTickers] = useState('');
  const [alerts, setAlerts] = useState([]);
  const [showMobileView, setShowMobileView] = useState(false);
  const [showAIChat, setShowAIChat] = useState(false);
  const [authToken, setAuthToken] = useState(() => localStorage.getItem('authToken') || '');
  const [authUser, setAuthUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('authUser')) || null; } catch { return null; }
  });
  const [chartSymbol, setChartSymbol] = useState('AAPL');
  const [showLogoMenu, setShowLogoMenu] = useState(false);
  const logoMenuRef = useRef(null);


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


  // Auto-refresh effect - use fast endpoint for auto-refresh too
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchStocks(true); // Use fast endpoint for auto-refresh
      }, refreshInterval * 1000);

      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  // ULTRA-OPTIMIZED: Maximum performance loading strategy
  useEffect(() => {
    console.log('🚀 PERFORMANCE: Starting optimized loading sequence...');

    // INSTANT: Load only critical data immediately
    loadUserPreferences();
    fetchWatchlists();

    // Show progress to user
    console.log('⚡ PERFORMANCE: Core data loaded, continuing background...');

    // BACKGROUND: Load everything else with significant delays
    setTimeout(() => {
      console.log('📊 PERFORMANCE: Loading alerts...');
      fetchAlerts();
    }, 2000);

    setTimeout(() => {
      console.log('📰 PERFORMANCE: Loading news...');
      fetchNews();
    }, 4000);

    // Check if mobile
    const checkMobile = () => {
      setShowMobileView(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // WebSocket connection effect
  useEffect(() => {
    console.log('📡 WEBSOCKET: Initializing real-time connection...');

    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(`${API_BASE_URL.replace('https://', 'wss://').replace('http://', 'ws://')}/ws`);

        ws.onopen = () => {
          console.log('📡 WEBSOCKET: Connected successfully');
          setIsConnected(true);
          setWebsocket(ws);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('📡 WEBSOCKET: Received update:', data.type);

            // Handle real-time updates
            if (data.type === 'stock_update') {
              setStocks(data.data.stocks || []);
              console.log('📊 WEBSOCKET: Stock data updated in real-time');
            } else if (data.type === 'market_update') {
              // Update market data if needed
              console.log('📈 WEBSOCKET: Market data updated in real-time');
            }
          } catch (error) {
            console.log('📡 WEBSOCKET: Error parsing message:', error);
          }
        };

        ws.onclose = () => {
          console.log('📡 WEBSOCKET: Connection closed');
          setIsConnected(false);
          setWebsocket(null);
          // Don't auto-reconnect for now to prevent spam
        };

        ws.onerror = (error) => {
          console.log('📡 WEBSOCKET: Connection error:', error);
          setIsConnected(false);
          // Don't auto-reconnect for now to prevent spam
        };

      } catch (error) {
        console.log('📡 WEBSOCKET: Failed to create connection:', error);
      }
    };

    // Connect after initial load
    setTimeout(connectWebSocket, 3000);

    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, []);

  // Apply dark mode
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Close logo dropdown when clicking outside
  useEffect(() => {
    const handleDocumentClick = (event) => {
      if (logoMenuRef.current && !logoMenuRef.current.contains(event.target)) {
        setShowLogoMenu(false);
      }
    };
    document.addEventListener('mousedown', handleDocumentClick);
    return () => document.removeEventListener('mousedown', handleDocumentClick);
  }, []);

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

  const authHeaders = () => (authToken ? { Authorization: `Bearer ${authToken}` } : {});

  const handleAuthSuccess = (data, { remember } = { remember: true }) => {
    if (data?.token) {
      setAuthToken(data.token);
      if (remember) localStorage.setItem('authToken', data.token);
    }
    if (data?.user) {
      setAuthUser(data.user);
      if (remember) localStorage.setItem('authUser', JSON.stringify(data.user));
    }
  };

  // Local watchlist helpers (fallback when backend is disabled)
  const generateLocalId = () => {
    try { return crypto.randomUUID(); } catch { return `wl_${Date.now()}_${Math.floor(Math.random() * 1e6)}`; }
  };
  const loadLocalWatchlists = () => {
    try {
      const raw = localStorage.getItem('watchlists');
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch { return []; }
  };
  const saveLocalWatchlists = (lists) => {
    try { localStorage.setItem('watchlists', JSON.stringify(lists)); } catch { }
  };
  const createLocalWatchlist = (name, tickers) => {
    const wl = {
      id: generateLocalId(),
      name,
      tickers,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      source: 'local'
    };
    const next = [wl, ...watchlists];
    setWatchlists(next);
    saveLocalWatchlists(next);
    return wl;
  };
  const deleteLocalWatchlist = (watchlistId) => {
    const next = watchlists.filter(w => w.id !== watchlistId);
    setWatchlists(next);
    saveLocalWatchlists(next);
  };
  const updateLocalWatchlist = (watchlistId, name, tickers) => {
    const next = watchlists.map(w => w.id === watchlistId ? { ...w, name, tickers, updated_at: new Date().toISOString(), source: 'local' } : w);
    setWatchlists(next);
    saveLocalWatchlists(next);
    return next.find(w => w.id === watchlistId);
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

  const fetchStocks = async (useFastEndpoint = false) => {
    try {
      setLoading(true);
      let url = `${API_BASE_URL}/api/stocks/scan`;

      // Use instant endpoint for initial load (fastest possible)
      if (useFastEndpoint) {
        url = `${API_BASE_URL}/api/stocks/scan/fast`;
      } else if (currentWatchlist) {
        url = `${API_BASE_URL}/api/watchlists/${currentWatchlist.id}/scan`;
      }

      const response = await fetch(url, {
        method: currentWatchlist ? 'POST' : 'GET'
      });
      const data = await response.json();
      // On mobile, render fewer cards initially
      const all = data.stocks || [];
      const isMobile = window.innerWidth < 768;
      setStocks(isMobile ? all.slice(0, 24) : all);
    } catch (error) {
      console.error('Error fetching stocks:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchWatchlists = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/watchlists`, {
        headers: { ...authHeaders() }
      });
      if (!response.ok) {
        // Backend unavailable → fallback to local
        setWatchlistsBackendAvailable(false);
        setWatchlists(loadLocalWatchlists());
        return;
      }
      const data = await response.json();
      if (data && data.message && String(data.message).toLowerCase().includes('watchlists disabled')) {
        setWatchlistsBackendAvailable(false);
        setWatchlists(loadLocalWatchlists());
        return;
      }
      setWatchlistsBackendAvailable(true);
      setWatchlists(data.watchlists || []);
    } catch (error) {
      console.error('Error fetching watchlists:', error);
      setWatchlistsBackendAvailable(false);
      setWatchlists(loadLocalWatchlists());
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/alerts`, { headers: { ...authHeaders() } });
      const data = await response.json();
      setAlerts(data.alerts || []);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  const [isCreatingWatchlist, setIsCreatingWatchlist] = useState(false);
  const createWatchlist = async () => {
    if (!newWatchlistName || !newWatchlistTickers || isCreatingWatchlist) return;

    try {
      setIsCreatingWatchlist(true);
      const tickers = newWatchlistTickers
        .split(',')
        .map(t => t.trim().toUpperCase())
        .filter(Boolean);
      if (!watchlistsBackendAvailable) {
        createLocalWatchlist(newWatchlistName.trim(), tickers);
      } else {
        const response = await fetch(`${API_BASE_URL}/api/watchlists`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...authHeaders() },
          body: JSON.stringify({ name: newWatchlistName.trim(), tickers })
        });

        if (!response.ok) {
          // Fallback to local when backend rejects (e.g., 503)
          setWatchlistsBackendAvailable(false);
          createLocalWatchlist(newWatchlistName.trim(), tickers);
        } else {
          await fetchWatchlists();
        }
      }

      setNewWatchlistName('');
      setNewWatchlistTickers('');
      setShowWatchlistModal(false);
    } catch (error) {
      console.error('Error creating watchlist:', error);
      // Final fallback: local
      const tickers = newWatchlistTickers
        .split(',')
        .map(t => t.trim().toUpperCase())
        .filter(Boolean);
      createLocalWatchlist(newWatchlistName.trim(), tickers);
      setNewWatchlistName('');
      setNewWatchlistTickers('');
      setShowWatchlistModal(false);
    } finally {
      setIsCreatingWatchlist(false);
    }
  };

  const deleteWatchlist = async (watchlistId) => {
    try {
      if (!watchlistsBackendAvailable) {
        deleteLocalWatchlist(watchlistId);
      } else {
        const resp = await fetch(`${API_BASE_URL}/api/watchlists/${watchlistId}`, { method: 'DELETE', headers: { ...authHeaders() } });
        if (!resp.ok) {
          setWatchlistsBackendAvailable(false);
          deleteLocalWatchlist(watchlistId);
        } else {
          fetchWatchlists();
        }
      }
      if (currentWatchlist && currentWatchlist.id === watchlistId) {
        setCurrentWatchlist(null);
      }
    } catch (error) {
      console.error('Error deleting watchlist:', error);
      deleteLocalWatchlist(watchlistId);
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
    const symbol = searchTicker.trim().toUpperCase();
    if (!symbol) return;

    try {
      // Instant feedback: show a stub result while fetching full details
      setIsSearching(true);
      setSearchResult({ ticker: symbol, companyName: 'Loading…', rank: 1 });
      setShowSearchResult(true);
      setActiveTab('search');

      const response = await fetch(`${API_BASE_URL}/api/stocks/${symbol}`);
      const data = await response.json();

      if (response.ok) {
        data.rank = 1;
        setSearchResult(data);
      } else {
        alert(`Stock ${symbol} not found or error occurred`);
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
      // Use instant news endpoint for immediate loading
      const response = await fetch(`${API_BASE_URL}/api/news/general/instant`);
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

  const renderContent = () => {
    switch (activeTab) {
      case 'home':
        return (
          <HomeScreen
            onNewWatchlist={() => setShowWatchlistModal(true)}
            watchlists={watchlists}
            onDeleteWatchlist={deleteWatchlist}
            news={news}
            newsLoading={newsLoading}
            onOpenChart={openChartForStock}
          />
        );
      case 'portfolio':
        return <Portfolio />;
      case 'watchlist':
        return (
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
        );
      case 'news':
        return <NewsTab news={news} loading={newsLoading} searchQuery={newsSearchQuery} />;
      case 'chart':
        return <ChartTab initialSymbol={chartSymbol} />;
      case 'screener':
        return <ScreenerTestTab onOpenChart={openChartForStock} />;
      case 'shadows-picks':
        return (
          <div className="space-y-6">
            <div className="flex items-center space-x-2 mb-4">
              <Eye className="w-5 h-5 text-blue-600" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Shadow's Picks
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* AAPL */}
              <MiniStockCard
                stock={{
                  ticker: 'AAPL',
                  companyName: 'Apple Inc.',
                  currentPrice: 175.43,
                  priceChangePercent: 2.15,
                  score: 4,
                  passes: {
                    trend: true,
                    momentum: true,
                    volume: true,
                    priceAction: true
                  },
                  RSI: 65.2,
                  MACD: 2.34,
                  Stochastic: 78.5,
                  averageVolume: 45000000,
                  relativeVolume: 1.8,
                  fiftyDayMA: 170.25,
                  twoHundredDayMA: 165.80,
                  bollingerUpper: 180.50,
                  bollingerLower: 160.20
                }}
                onClick={(s) => { setSelectedStock(s); setShowStockDetail(true); }}
                onOpenChart={() => openChartForStock({ ticker: 'AAPL' })}
              />

              {/* CAKE */}
              <MiniStockCard
                stock={{
                  ticker: 'CAKE',
                  companyName: 'Cheesecake Factory Inc.',
                  currentPrice: 34.67,
                  priceChangePercent: -1.23,
                  score: 3,
                  passes: {
                    trend: true,
                    momentum: false,
                    volume: true,
                    priceAction: true
                  },
                  RSI: 45.8,
                  MACD: -0.12,
                  Stochastic: 35.2,
                  averageVolume: 1200000,
                  relativeVolume: 1.6,
                  fiftyDayMA: 33.45,
                  twoHundredDayMA: 32.10,
                  bollingerUpper: 36.80,
                  bollingerLower: 30.20
                }}
                onClick={(s) => { setSelectedStock(s); setShowStockDetail(true); }}
                onOpenChart={() => openChartForStock({ ticker: 'CAKE' })}
              />

              {/* NNE */}
              <MiniStockCard
                stock={{
                  ticker: 'NNE',
                  companyName: 'Nano Nuclear Energy Inc.',
                  currentPrice: 12.89,
                  priceChangePercent: 5.67,
                  score: 4,
                  passes: {
                    trend: true,
                    momentum: true,
                    volume: true,
                    priceAction: true
                  },
                  RSI: 72.1,
                  MACD: 1.85,
                  Stochastic: 82.3,
                  averageVolume: 850000,
                  relativeVolume: 2.1,
                  fiftyDayMA: 11.20,
                  twoHundredDayMA: 10.80,
                  bollingerUpper: 14.50,
                  bollingerLower: 9.80
                }}
                onClick={(s) => { setSelectedStock(s); setShowStockDetail(true); }}
                onOpenChart={() => openChartForStock({ ticker: 'NNE' })}
              />
            </div>
          </div>
        );
      default:
        return (
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
              <div className="flex flex-col justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                <div className="text-center">
                  <p className="text-lg font-semibold text-gray-700 dark:text-gray-300">Loading Lightning-Fast Market Data...</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Using optimized instant endpoints for maximum speed</p>
                  <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">Expected load time: 2-5 seconds</p>
                  {isConnected && (
                    <p className="text-xs text-green-600 dark:text-green-400 mt-2 flex items-center gap-1">
                      <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                      Real-time updates active
                    </p>
                  )}
                </div>
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
                        <p className="text-sm text-blue-600 dark:text-blue-400">{searchResult.companyName}</p>
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
                        onClick={(s) => { setSelectedStock(s); setShowStockDetail(true); }}
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
        );
    }
  };

  // Shadowbot route: show dedicated page
  const isShadowbotRoute = typeof window !== 'undefined' && window.location.pathname === '/shadowbot';
  useEffect(() => {
    if (window.location.hash === '#shadowbot') {
      // preserve original behavior for old link
      setShowAIChat(true);
    }
  }, []);

  return (
    <div className={`min-h-screen ${darkMode ? 'dark' : ''} bg-carbon-900 text-gray-100 transition-colors carbon`}>
      {/* Dedicated Auth Route */}
      {typeof window !== 'undefined' && window.location.pathname === '/auth' && (
        <AuthPage onAuth={(data, opts) => { handleAuthSuccess(data, opts); window.location.href = '/'; }} />
      )}
      {/* Enhanced Header - Made Sticky/Floating */}
      <header className="sticky top-0 z-50 header-gunmetal border-b border-carbon-700 shadow-sm backdrop-blur-sm">
        <div className="w-full px-0 py-3">
          <div className="flex flex-col lg:flex-row gap-2 lg:items-center justify-start">
            {/* Left Side - Logo and Title with dropdown */}
            <div ref={logoMenuRef} className="relative flex items-center space-x-2">
              <button
                onClick={() => setShowLogoMenu((v) => !v)}
                className="rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-haspopup="menu"
                aria-expanded={showLogoMenu}
                title="Open menu"
              >
                <Logo size="lg" showText={false} src="/pipengine_logo.png" />
              </button>
              {autoRefresh && (
                <p className="text-xs text-green-600 dark:text-green-400">
                  Auto-refreshing every {refreshInterval / 60} minutes
                </p>
              )}
              {showLogoMenu && (
                <div className="absolute left-0 top-full mt-2 w-56 bg-gray-900 border border-gray-700 rounded-lg shadow-lg z-50">
                  <div className="py-1">
                    <button
                      onClick={() => { setShowLogoMenu(false); window.location.href = '/shadowbot'; }}
                      className="w-full text-left px-3 py-2 hover:bg-gray-800"
                    >
                      Shadowbot
                    </button>
                  </div>
                </div>
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
                  {isSearching ? (
                    <RefreshCw className="w-5 h-5 animate-spin" />
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {/* Navigation Tabs in Header Center */}
            <div className="flex items-center space-x-1 bg-gray-800/30 p-1 rounded-lg border border-gray-700/60">
              <button
                onClick={() => {
                  setActiveTab('home');
                  setCurrentWatchlist(null);
                  setShowSearchResult(false);
                }}
                className={`tab-button ${activeTab === 'home' ? 'tab-button-active' : ''}`}
              >
                <Home className="w-4 h-4" />
                <span>Home</span>
              </button>



              <button
                onClick={() => {
                  setActiveTab('portfolio');
                  setCurrentWatchlist(null);
                  setShowSearchResult(false);
                }}
                className={`tab-button ${activeTab === 'portfolio' ? 'tab-button-active' : ''}`}
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
                className={`tab-button ${activeTab === 'watchlist' ? 'tab-button-active' : ''}`}
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
                className={`tab-button ${activeTab === 'news' ? 'tab-button-active' : ''}`}
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
                className={`tab-button ${activeTab === 'chart' ? 'tab-button-active' : ''}`}
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
                className={`tab-button ${activeTab === 'screener' ? 'tab-button-active' : ''}`}
              >
                <Filter className="w-4 h-4" />
                <span>Screener</span>
              </button>

              <button
                onClick={() => {
                  setActiveTab('shadows-picks');
                  setCurrentWatchlist(null);
                  setShowSearchResult(false);
                }}
                className={`tab-button ${activeTab === 'shadows-picks' ? 'tab-button-active' : ''}`}
              >
                <Eye className="w-4 h-4" />
                <span>Shadow's Picks</span>
              </button>
            </div>

            {/* Right Side - Controls */}
            <div className="flex items-center space-x-2 ml-auto pr-2">
              {/* Auth status indicator */}
              {authUser ? (
                <span className="hidden sm:inline text-xs text-green-400 mr-2">Logged in as: {authUser.email}</span>
              ) : (
                <span className="hidden sm:inline text-xs text-yellow-400 mr-2">Not logged in</span>
              )}
              {/* Auth quick actions */}
              {!authUser ? (
                <>
                  <button
                    onClick={async () => {
                      const email = prompt('Email');
                      const password = prompt('Password');
                      if (!email || !password) return;
                      try {
                        const resp = await fetch(`${API_BASE_URL}/api/auth/login`, {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ email, password })
                        });
                        const data = await resp.json();
                        if (!resp.ok) {
                          alert(data.detail || 'Login failed');
                        } else {
                          handleAuthSuccess(data);
                        }
                      } catch (e) {
                        alert('Login error');
                      }
                    }}
                    className="sleek-icon-btn"
                    title="Login"
                  >
                    <span className="text-sm">Login</span>
                  </button>
                  <button
                    onClick={async () => {
                      const email = prompt('Email');
                      const password = prompt('Password');
                      if (!email || !password) return;
                      try {
                        const resp = await fetch(`${API_BASE_URL}/api/auth/register`, {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ email, password })
                        });
                        const data = await resp.json();
                        if (!resp.ok) {
                          alert(data.detail || 'Registration failed');
                        } else {
                          handleAuthSuccess(data);
                        }
                      } catch (e) {
                        alert('Registration error');
                      }
                    }}
                    className="sleek-icon-btn"
                    title="Register"
                  >
                    <span className="text-sm">Sign up</span>
                  </button>
                </>
              ) : (
                <>
                  <span className="text-xs text-gray-400">{authUser.email}</span>
                  <button
                    onClick={() => {
                      setAuthToken('');
                      setAuthUser(null);
                      localStorage.removeItem('authToken');
                      localStorage.removeItem('authUser');
                    }}
                    className="sleek-icon-btn"
                    title="Logout"
                  >
                    <span className="text-sm">Logout</span>
                  </button>
                </>
              )}
              {/* AI Chat Button */}
              <button
                onClick={() => setShowAIChat(!showAIChat)}
                className={`sleek-icon-btn ${showAIChat ? 'border-blue-500 text-blue-300' : ''}`}
                title="AI Chat"
              >
                <Brain className="w-5 h-5" />
              </button>

              {/* Mobile/Desktop Toggle */}
              <button
                onClick={() => setShowMobileView(!showMobileView)}
                className="sleek-icon-btn"
              >
                {showMobileView ? <Monitor className="w-5 h-5" /> : <Smartphone className="w-5 h-5" />}
              </button>

              {/* Dark Mode Toggle */}
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="sleek-icon-btn"
              >
                {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>

              {/* Settings */}
              <button
                onClick={() => setShowSettings(true)}
                className="sleek-icon-btn"
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
                className="sleek-icon-btn disabled:opacity-50"
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
        {!isShadowbotRoute && activeTab === 'news' && (
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
        {!isShadowbotRoute && activeTab !== 'news' && activeTab !== 'home' && activeTab !== 'portfolio' && (
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
            {!isShadowbotRoute ? renderContent() : <ShadowbotPage />}
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
        isSubmitting={isCreatingWatchlist}
      />

      {/* Stock Detail Modal */}
      <StockDetailModal
        stock={selectedStock}
        isOpen={showStockDetail}
        onClose={() => setShowStockDetail(false)}
        aiProvider={aiProvider}
        API_BASE_URL={API_BASE_URL}
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
