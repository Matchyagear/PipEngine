import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Upload, 
  PieChart, 
  TrendingUp, 
  TrendingDown, 
  BarChart3,
  DollarSign,
  Percent,
  Clock,
  Edit2,
  Trash2,
  Download,
  AlertCircle,
  CheckCircle,
  ExternalLink
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import StockCard from './StockCard';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

const Portfolio = () => {
  const [portfolios, setPortfolios] = useState([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState(null);
  const [showAddManualModal, setShowAddManualModal] = useState(false);
  const [showWebullImportModal, setShowWebullImportModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [webullCredentials, setWebullCredentials] = useState({
    username: '',
    password: '',
    accountId: ''
  });

  // Manual stock addition form
  const [manualStock, setManualStock] = useState({
    symbol: '',
    quantity: '',
    avgCost: '',
    purchaseDate: new Date().toISOString().split('T')[0]
  });

  // Sample portfolio data (will be replaced with real data)
  const [samplePortfolio] = useState({
    id: 'demo_portfolio',
    name: 'Demo Portfolio',
    totalValue: 125000,
    dayChange: 2500,
    dayChangePercent: 2.04,
    positions: [
      {
        symbol: 'AAPL',
        companyName: 'Apple Inc.',
        quantity: 100,
        avgCost: 150.00,
        currentPrice: 175.50,
        marketValue: 17550,
        unrealizedPnL: 2550,
        unrealizedPnLPercent: 17.0,
        purchaseDate: '2024-01-15'
      },
      {
        symbol: 'MSFT',
        companyName: 'Microsoft Corporation',
        quantity: 50,
        avgCost: 300.00,
        currentPrice: 330.25,
        marketValue: 16512.50,
        unrealizedPnL: 1512.50,
        unrealizedPnLPercent: 10.08,
        purchaseDate: '2024-02-01'
      },
      {
        symbol: 'GOOGL',
        companyName: 'Alphabet Inc.',
        quantity: 25,
        avgCost: 120.00,
        currentPrice: 135.75,
        marketValue: 3393.75,
        unrealizedPnL: 393.75,
        unrealizedPnLPercent: 13.12,
        purchaseDate: '2024-01-20'
      }
    ]
  });

  useEffect(() => {
    // Initialize with demo portfolio
    setPortfolios([samplePortfolio]);
    setSelectedPortfolio(samplePortfolio);
  }, [samplePortfolio]);

  const handleAddManualStock = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Fetch current stock price (you'd replace this with actual API call)
      const mockCurrentPrice = Math.random() * 200 + 50; // Mock price for demo
      
      const newPosition = {
        symbol: manualStock.symbol.toUpperCase(),
        companyName: `${manualStock.symbol.toUpperCase()} Company`, // Mock company name
        quantity: parseFloat(manualStock.quantity),
        avgCost: parseFloat(manualStock.avgCost),
        currentPrice: mockCurrentPrice,
        marketValue: parseFloat(manualStock.quantity) * mockCurrentPrice,
        unrealizedPnL: (mockCurrentPrice - parseFloat(manualStock.avgCost)) * parseFloat(manualStock.quantity),
        unrealizedPnLPercent: ((mockCurrentPrice - parseFloat(manualStock.avgCost)) / parseFloat(manualStock.avgCost)) * 100,
        purchaseDate: manualStock.purchaseDate
      };

      // Update selected portfolio
      const updatedPortfolio = {
        ...selectedPortfolio,
        positions: [...selectedPortfolio.positions, newPosition]
      };

      // Recalculate portfolio totals
      const totalMarketValue = updatedPortfolio.positions.reduce((sum, pos) => sum + pos.marketValue, 0);
      const totalUnrealizedPnL = updatedPortfolio.positions.reduce((sum, pos) => sum + pos.unrealizedPnL, 0);
      
      updatedPortfolio.totalValue = totalMarketValue;
      updatedPortfolio.dayChange = totalUnrealizedPnL;
      updatedPortfolio.dayChangePercent = totalMarketValue > 0 ? (totalUnrealizedPnL / (totalMarketValue - totalUnrealizedPnL)) * 100 : 0;

      setSelectedPortfolio(updatedPortfolio);
      setPortfolios(portfolios.map(p => p.id === updatedPortfolio.id ? updatedPortfolio : p));

      // Reset form
      setManualStock({
        symbol: '',
        quantity: '',
        avgCost: '',
        purchaseDate: new Date().toISOString().split('T')[0]
      });
      setShowAddManualModal(false);
    } catch (error) {
      console.error('Error adding manual stock:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleWebullImport = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // This will be replaced with actual Webull API integration
      const response = await fetch(`${API_BASE_URL}/api/portfolio/webull-import`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(webullCredentials),
      });

      if (response.ok) {
        const importedPortfolio = await response.json();
        setPortfolios([...portfolios, importedPortfolio]);
        setSelectedPortfolio(importedPortfolio);
        setShowWebullImportModal(false);
        setWebullCredentials({ username: '', password: '', accountId: '' });
      } else {
        throw new Error('Import failed - API keys may be missing or invalid');
      }
    } catch (error) {
      console.error('Webull import error:', error);
      alert('Webull import is not yet configured. Please provide API credentials to enable this feature.');
    } finally {
      setLoading(false);
    }
  };

  const removePosition = (symbol) => {
    const updatedPortfolio = {
      ...selectedPortfolio,
      positions: selectedPortfolio.positions.filter(pos => pos.symbol !== symbol)
    };

    // Recalculate totals
    const totalMarketValue = updatedPortfolio.positions.reduce((sum, pos) => sum + pos.marketValue, 0);
    const totalUnrealizedPnL = updatedPortfolio.positions.reduce((sum, pos) => sum + pos.unrealizedPnL, 0);
    
    updatedPortfolio.totalValue = totalMarketValue;
    updatedPortfolio.dayChange = totalUnrealizedPnL;
    updatedPortfolio.dayChangePercent = totalMarketValue > 0 ? (totalUnrealizedPnL / (totalMarketValue - totalUnrealizedPnL)) * 100 : 0;

    setSelectedPortfolio(updatedPortfolio);
    setPortfolios(portfolios.map(p => p.id === updatedPortfolio.id ? updatedPortfolio : p));
  };

  const getChangeColor = (change) => {
    if (change > 0) return 'text-green-600 dark:text-green-400';
    if (change < 0) return 'text-red-600 dark:text-red-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Portfolio Management
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Track and manage your investment portfolios
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowAddManualModal(true)}
            className="flex items-center space-x-2 py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg btn-primary"
          >
            <Plus className="w-4 h-4" />
            <span>Add Stock</span>
          </button>
          <button
            onClick={() => setShowWebullImportModal(true)}
            className="flex items-center space-x-2 py-2 px-4 bg-green-600 hover:bg-green-700 text-white rounded-lg btn-primary"
          >
            <Upload className="w-4 h-4" />
            <span>Import from Webull</span>
          </button>
        </div>
      </div>

      {/* Portfolio Overview */}
      {selectedPortfolio && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {selectedPortfolio.name}
            </h2>
            <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
              <Clock className="w-4 h-4" />
              <span>Updated just now</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-900/20">
              <div className="flex items-center space-x-2 mb-2">
                <DollarSign className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-medium text-blue-800 dark:text-blue-300">Total Value</span>
              </div>
              <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                {formatCurrency(selectedPortfolio.totalValue)}
              </div>
            </div>

            <div className="p-4 rounded-lg bg-green-50 dark:bg-green-900/20">
              <div className="flex items-center space-x-2 mb-2">
                <TrendingUp className="w-5 h-5 text-green-600" />
                <span className="text-sm font-medium text-green-800 dark:text-green-300">Day Change</span>
              </div>
              <div className="text-2xl font-bold text-green-900 dark:text-green-100">
                {formatCurrency(selectedPortfolio.dayChange)}
              </div>
            </div>

            <div className="p-4 rounded-lg bg-purple-50 dark:bg-purple-900/20">
              <div className="flex items-center space-x-2 mb-2">
                <Percent className="w-5 h-5 text-purple-600" />
                <span className="text-sm font-medium text-purple-800 dark:text-purple-300">Day Change %</span>
              </div>
              <div className="text-2xl font-bold text-purple-900 dark:text-purple-100">
                {selectedPortfolio.dayChangePercent >= 0 ? '+' : ''}{selectedPortfolio.dayChangePercent.toFixed(2)}%
              </div>
            </div>

            <div className="p-4 rounded-lg bg-orange-50 dark:bg-orange-900/20">
              <div className="flex items-center space-x-2 mb-2">
                <BarChart3 className="w-5 h-5 text-orange-600" />
                <span className="text-sm font-medium text-orange-800 dark:text-orange-300">Positions</span>
              </div>
              <div className="text-2xl font-bold text-orange-900 dark:text-orange-100">
                {selectedPortfolio.positions.length}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Positions List */}
      {selectedPortfolio && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Portfolio Positions
            </h3>
            <button className="flex items-center space-x-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200">
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-2 text-sm font-medium text-gray-600 dark:text-gray-400">Symbol</th>
                  <th className="text-left py-3 px-2 text-sm font-medium text-gray-600 dark:text-gray-400">Quantity</th>
                  <th className="text-left py-3 px-2 text-sm font-medium text-gray-600 dark:text-gray-400">Avg Cost</th>
                  <th className="text-left py-3 px-2 text-sm font-medium text-gray-600 dark:text-gray-400">Current Price</th>
                  <th className="text-left py-3 px-2 text-sm font-medium text-gray-600 dark:text-gray-400">Market Value</th>
                  <th className="text-left py-3 px-2 text-sm font-medium text-gray-600 dark:text-gray-400">Unrealized P&L</th>
                  <th className="text-left py-3 px-2 text-sm font-medium text-gray-600 dark:text-gray-400">Actions</th>
                </tr>
              </thead>
              <tbody>
                {selectedPortfolio.positions.map((position) => (
                  <motion.tr
                    key={position.symbol}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                  >
                    <td className="py-3 px-2">
                      <div>
                        <div className="font-semibold text-gray-900 dark:text-white">
                          {position.symbol}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400 truncate">
                          {position.companyName}
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-2 text-gray-900 dark:text-white">
                      {position.quantity.toLocaleString()}
                    </td>
                    <td className="py-3 px-2 text-gray-900 dark:text-white">
                      {formatCurrency(position.avgCost)}
                    </td>
                    <td className="py-3 px-2 text-gray-900 dark:text-white">
                      {formatCurrency(position.currentPrice)}
                    </td>
                    <td className="py-3 px-2 text-gray-900 dark:text-white">
                      {formatCurrency(position.marketValue)}
                    </td>
                    <td className="py-3 px-2">
                      <div className={`font-medium ${getChangeColor(position.unrealizedPnL)}`}>
                        {formatCurrency(position.unrealizedPnL)}
                      </div>
                      <div className={`text-sm ${getChangeColor(position.unrealizedPnL)}`}>
                        ({position.unrealizedPnLPercent >= 0 ? '+' : ''}{position.unrealizedPnLPercent.toFixed(2)}%)
                      </div>
                    </td>
                    <td className="py-3 px-2">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => removePosition(position.symbol)}
                          className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-200"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                        <a
                          href={`https://finviz.com/quote.ashx?t=${position.symbol}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Manual Stock Addition Modal */}
      <AnimatePresence>
        {showAddManualModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
            onClick={() => setShowAddManualModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                Add Manual Stock Position
              </h2>

              <form onSubmit={handleAddManualStock}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-gray-700 dark:text-gray-300 mb-2">
                      Stock Symbol
                    </label>
                    <input
                      type="text"
                      value={manualStock.symbol}
                      onChange={(e) => setManualStock({...manualStock, symbol: e.target.value})}
                      className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="AAPL"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-gray-700 dark:text-gray-300 mb-2">
                        Quantity
                      </label>
                      <input
                        type="number"
                        value={manualStock.quantity}
                        onChange={(e) => setManualStock({...manualStock, quantity: e.target.value})}
                        className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="100"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-gray-700 dark:text-gray-300 mb-2">
                        Average Cost
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        value={manualStock.avgCost}
                        onChange={(e) => setManualStock({...manualStock, avgCost: e.target.value})}
                        className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="150.00"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-gray-700 dark:text-gray-300 mb-2">
                      Purchase Date
                    </label>
                    <input
                      type="date"
                      value={manualStock.purchaseDate}
                      onChange={(e) => setManualStock({...manualStock, purchaseDate: e.target.value})}
                      className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                </div>

                <div className="flex space-x-2 mt-6">
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 py-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg btn-primary"
                  >
                    {loading ? 'Adding...' : 'Add Position'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAddManualModal(false)}
                    className="py-2 px-4 bg-gray-600 hover:bg-gray-700 text-white rounded-lg btn-secondary"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Webull Import Modal */}
      <AnimatePresence>
        {showWebullImportModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
            onClick={() => setShowWebullImportModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                Import from Webull
              </h2>

              <div className="mb-4 p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="w-5 h-5 text-orange-600" />
                  <span className="text-sm font-medium text-orange-800 dark:text-orange-200">
                    API Configuration Required
                  </span>
                </div>
                <p className="text-sm text-orange-700 dark:text-orange-300 mt-2">
                  Webull API credentials need to be configured on the server before this feature can be used.
                </p>
              </div>

              <form onSubmit={handleWebullImport}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-gray-700 dark:text-gray-300 mb-2">
                      Account ID
                    </label>
                    <input
                      type="text"
                      value={webullCredentials.accountId}
                      onChange={(e) => setWebullCredentials({...webullCredentials, accountId: e.target.value})}
                      className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Your Webull Account ID"
                      required
                    />
                  </div>
                </div>

                <div className="flex space-x-2 mt-6">
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 py-2 px-4 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded-lg btn-primary"
                  >
                    {loading ? 'Importing...' : 'Import Portfolio'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowWebullImportModal(false)}
                    className="py-2 px-4 bg-gray-600 hover:bg-gray-700 text-white rounded-lg btn-secondary"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Portfolio;