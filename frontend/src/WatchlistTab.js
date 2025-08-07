import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Star,
  Plus,
  Edit,
  Trash2,
  Grid,
  List,
  ChevronDown,
  Settings,
  Upload
} from 'lucide-react';
import StockCard from './StockCard';
import MiniStockCard from './MiniStockCard';
import StockCardModal from './StockCardModal';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

const WatchlistTab = ({
  watchlists,
  setWatchlists,
  onNewWatchlist,
  onDeleteWatchlist,
  fetchStocks,
  aiProvider,
  onOpenChart
}) => {
  const [selectedWatchlist, setSelectedWatchlist] = useState(null);
  const [viewMode, setViewMode] = useState('mini'); // 'mini' or 'full'
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [watchlistStocks, setWatchlistStocks] = useState([]);
  const [loading, setLoading] = useState(false);

  // Mini stock card modal state
  const [selectedMiniStock, setSelectedMiniStock] = useState(null);
  const [showStockModal, setShowStockModal] = useState(false);

  // Context menu state
  const [contextMenu, setContextMenu] = useState({ show: false, x: 0, y: 0, watchlist: null });
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingWatchlist, setEditingWatchlist] = useState(null);
  const [editName, setEditName] = useState('');
  const [editTickers, setEditTickers] = useState('');

  // Create default watchlist if none exists
  useEffect(() => {
    const createDefaultWatchlist = async () => {
      if (watchlists.length === 0) {
        try {
          console.log('Creating default watchlist...');
          const response = await fetch(`${API_BASE_URL}/api/watchlists`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              name: 'My Watchlist',
              tickers: 'AAPL, MSFT, GOOGL, TSLA' // Add some default tickers
            })
          });

          if (response.ok) {
            const newWatchlist = await response.json();
            console.log('Default watchlist created:', newWatchlist);
            setWatchlists([newWatchlist]);
            setSelectedWatchlist(newWatchlist);
          } else {
            console.error('Failed to create default watchlist:', response.status);
          }
        } catch (error) {
          console.error('Error creating default watchlist:', error);
        }
      } else {
        // Set the first watchlist as selected by default
        console.log('Using existing watchlist:', watchlists[0]);
        setSelectedWatchlist(watchlists[0]);
      }
    };

    createDefaultWatchlist();
  }, [watchlists, setWatchlists]);

  // Fetch stocks for selected watchlist
  useEffect(() => {
    if (selectedWatchlist && selectedWatchlist.tickers) {
      fetchWatchlistStocks();
    } else {
      setWatchlistStocks([]);
    }
  }, [selectedWatchlist]);

  const fetchWatchlistStocks = async () => {
    if (!selectedWatchlist) {
      console.log('No watchlist selected');
      setWatchlistStocks([]);
      return;
    }

    console.log('Selected watchlist:', selectedWatchlist);
    console.log('Watchlist tickers:', selectedWatchlist.tickers);

    // Handle both string and array formats for tickers
    if (!selectedWatchlist.tickers ||
      (typeof selectedWatchlist.tickers === 'string' && selectedWatchlist.tickers.trim() === '') ||
      (Array.isArray(selectedWatchlist.tickers) && selectedWatchlist.tickers.length === 0)) {
      console.log('Watchlist has no tickers');
      setWatchlistStocks([]);
      return;
    }

    setLoading(true);
    try {
      // Handle both string and array formats, and clean exchange prefixes
      let tickersRaw;
      if (Array.isArray(selectedWatchlist.tickers)) {
        tickersRaw = selectedWatchlist.tickers;
      } else if (typeof selectedWatchlist.tickers === 'string') {
        tickersRaw = selectedWatchlist.tickers.split(',');
      } else {
        console.error('Invalid tickers format:', selectedWatchlist.tickers);
        setWatchlistStocks([]);
        setLoading(false);
        return;
      }

      const tickers = tickersRaw
        .map(t => {
          // Remove exchange prefixes like "NASDAQ:", "NYSE:", etc.
          const cleaned = t.toString().trim().toUpperCase();
          if (cleaned.includes(':')) {
            return cleaned.split(':')[1];
          }
          return cleaned;
        })
        .filter(t => t && t.length > 0);

      console.log('Processing tickers:', tickers);

      if (tickers.length === 0) {
        console.log('No valid tickers found');
        setWatchlistStocks([]);
        setLoading(false);
        return;
      }

      const stockPromises = tickers.map(async (ticker) => {
        try {
          console.log(`Fetching data for ${ticker}...`);
          const response = await fetch(`${API_BASE_URL}/api/stocks/${ticker}`);

          if (!response.ok) {
            console.error(`Failed to fetch ${ticker}: ${response.status}`);
            return null;
          }

          const stockData = await response.json();
          console.log(`Successfully fetched ${ticker}:`, stockData.ticker);
          return stockData;
        } catch (error) {
          console.error(`Error fetching ${ticker}:`, error);
          return null;
        }
      });

      const stocks = await Promise.all(stockPromises);
      const validStocks = stocks.filter(stock => stock !== null);
      console.log('Valid stocks found:', validStocks.length);
      console.log('Stock tickers:', validStocks.map(s => s.ticker));

      setWatchlistStocks(validStocks);
    } catch (error) {
      console.error('Error fetching watchlist stocks:', error);
      setWatchlistStocks([]);
    } finally {
      setLoading(false);
    }
  };

  const handleMiniStockClick = (stock) => {
    setSelectedMiniStock(stock);
    setShowStockModal(true);
  };

  const closeStockModal = () => {
    setShowStockModal(false);
    setSelectedMiniStock(null);
  };

  const handleWatchlistSelect = (watchlist) => {
    setSelectedWatchlist(watchlist);
    setDropdownOpen(false);
  };

  // Context menu handlers
  const handleRightClick = (e, watchlist) => {
    e.preventDefault();
    setContextMenu({
      show: true,
      x: e.pageX,
      y: e.pageY,
      watchlist
    });
  };

  const closeContextMenu = () => {
    setContextMenu({ show: false, x: 0, y: 0, watchlist: null });
  };

  const handleEdit = (watchlist) => {
    setEditingWatchlist(watchlist);
    setEditName(watchlist.name);
    setEditTickers(watchlist.tickers || '');
    setShowEditModal(true);
    closeContextMenu();
  };

  const handleDelete = async (watchlist) => {
    if (window.confirm(`Are you sure you want to delete "${watchlist.name}"?`)) {
      try {
        await onDeleteWatchlist(watchlist.id);
        // If we deleted the selected watchlist, select another one
        if (selectedWatchlist?.id === watchlist.id) {
          const remaining = watchlists.filter(w => w.id !== watchlist.id);
          setSelectedWatchlist(remaining.length > 0 ? remaining[0] : null);
        }
      } catch (error) {
        console.error('Error deleting watchlist:', error);
      }
    }
    closeContextMenu();
  };

  const saveEditedWatchlist = async () => {
    if (!editingWatchlist) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/watchlists/${editingWatchlist.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: editName,
          tickers: editTickers
        })
      });

      if (response.ok) {
        const updatedWatchlist = await response.json();
        const updatedWatchlists = watchlists.map(w =>
          w.id === editingWatchlist.id ? updatedWatchlist : w
        );
        setWatchlists(updatedWatchlists);

        // Update selected watchlist if it's the one being edited
        if (selectedWatchlist?.id === editingWatchlist.id) {
          setSelectedWatchlist(updatedWatchlist);
        }

        setShowEditModal(false);
        setEditingWatchlist(null);
      }
    } catch (error) {
      console.error('Error updating watchlist:', error);
    }
  };

  // File import handler
  const handleFileImport = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target.result;
      const tickers = content
        .split(/[\n,\s]+/)
        .map(ticker => ticker.trim().toUpperCase())
        .filter(ticker => ticker.length > 0)
        .join(', ');

      // Open new watchlist modal with imported tickers
      onNewWatchlist(tickers);
    };
    reader.readAsText(file);
  };

  // Close context menu when clicking outside
  React.useEffect(() => {
    const handleClickOutside = () => closeContextMenu();
    if (contextMenu.show) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [contextMenu.show]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header with Dropdown and Controls */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Watchlist Dropdown */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Star className="w-6 h-6 text-yellow-600" />
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Watchlists
              </h1>
            </div>

            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center space-x-2 py-2 px-4 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                <span className="text-gray-900 dark:text-white font-medium">
                  {selectedWatchlist ? selectedWatchlist.name : 'Select Watchlist'}
                </span>
                <ChevronDown className="w-4 h-4 text-gray-500" />
              </button>

              {dropdownOpen && (
                <div className="absolute top-full left-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 z-10">
                  <div className="p-2">
                    {watchlists.map((watchlist) => (
                      <button
                        key={watchlist.id}
                        onClick={() => handleWatchlistSelect(watchlist)}
                        onContextMenu={(e) => handleRightClick(e, watchlist)}
                        className="w-full text-left px-3 py-2 text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors relative group"
                      >
                        {watchlist.name}
                        {selectedWatchlist?.id === watchlist.id && (
                          <Star className="w-4 h-4 inline ml-2 text-yellow-500" />
                        )}
                        <span className="opacity-0 group-hover:opacity-100 text-xs text-gray-500 dark:text-gray-400 float-right">
                          Right-click for options
                        </span>
                      </button>
                    ))}
                    <hr className="my-2 border-gray-200 dark:border-gray-700" />
                    <button
                      onClick={() => {
                        onNewWatchlist();
                        setDropdownOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors flex items-center space-x-2"
                    >
                      <Plus className="w-4 h-4" />
                      <span>Create New Watchlist</span>
                    </button>
                    <label className="w-full text-left px-3 py-2 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors flex items-center space-x-2 cursor-pointer">
                      <input
                        type="file"
                        accept=".txt,.csv"
                        onChange={handleFileImport}
                        className="hidden"
                      />
                      <Upload className="w-4 h-4" />
                      <span>Import from .txt/.csv</span>
                    </label>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">View:</span>
            <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setViewMode('mini')}
                className={`p-2 rounded transition-colors ${viewMode === 'mini'
                    ? 'bg-white dark:bg-gray-600 shadow-sm'
                    : 'hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                title="Mini Cards"
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('full')}
                className={`p-2 rounded transition-colors ${viewMode === 'full'
                    ? 'bg-white dark:bg-gray-600 shadow-sm'
                    : 'hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                title="Full Cards"
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Watchlist Content */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600 dark:text-gray-400">Loading stocks...</span>
          </div>
        ) : watchlistStocks.length === 0 ? (
          <div className="text-center py-16">
            <Star className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Your watchlist is empty
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Add some stocks to "{selectedWatchlist?.name}" to get started
            </p>
            <button
              onClick={onNewWatchlist}
              className="inline-flex items-center space-x-2 py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Add Stocks</span>
            </button>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {selectedWatchlist?.name} ({watchlistStocks.length} stocks)
              </h2>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => fetchWatchlistStocks()}
                  className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                  title="Refresh"
                >
                  <Settings className="w-4 h-4" />
                </button>
                <button
                  onClick={onNewWatchlist}
                  className="flex items-center space-x-2 py-2 px-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  <span>Add Stock</span>
                </button>
              </div>
            </div>

            {/* Stock Cards */}
            {viewMode === 'mini' ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                {watchlistStocks.map((stock) => (
                  <MiniStockCard
                    key={stock.ticker}
                    stock={stock}
                    onClick={handleMiniStockClick}
                    onOpenChart={() => onOpenChart(stock)}
                  />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {watchlistStocks.map((stock) => (
                  <StockCard
                    key={stock.ticker}
                    stock={stock}
                    aiProvider={aiProvider}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Context Menu */}
      {contextMenu.show && (
        <div
          className="fixed bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 py-2 z-50"
          style={{ left: contextMenu.x, top: contextMenu.y }}
        >
          <button
            onClick={() => handleEdit(contextMenu.watchlist)}
            className="w-full text-left px-4 py-2 text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
          >
            <Edit className="w-4 h-4" />
            <span>Edit Watchlist</span>
          </button>
          <button
            onClick={() => handleDelete(contextMenu.watchlist)}
            className="w-full text-left px-4 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center space-x-2"
          >
            <Trash2 className="w-4 h-4" />
            <span>Delete Watchlist</span>
          </button>
        </div>
      )}

      {/* Edit Watchlist Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-96 max-w-90vw">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Edit Watchlist
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Watchlist Name
                </label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Enter watchlist name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Stock Tickers (comma separated)
                </label>
                <textarea
                  value={editTickers}
                  onChange={(e) => setEditTickers(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white h-24"
                  placeholder="AAPL, MSFT, GOOGL, ..."
                />
              </div>
            </div>

            <div className="flex space-x-3 mt-6">
              <button
                onClick={saveEditedWatchlist}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors"
                disabled={!editName.trim()}
              >
                Save Changes
              </button>
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setEditingWatchlist(null);
                }}
                className="flex-1 bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500 text-gray-900 dark:text-white py-2 px-4 rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Stock Card Modal */}
      <StockCardModal
        isOpen={showStockModal}
        onClose={closeStockModal}
        stock={selectedMiniStock}
        aiProvider={aiProvider}
      />
    </div>
  );
};

export default WatchlistTab;
