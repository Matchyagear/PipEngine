import React from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  ExternalLink
} from 'lucide-react';
import TradingViewSymbolOverview from './components/TradingViewSymbolOverview';

const IndexCard = ({ index, onClick }) => {
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

  const getDisplayAndTvSymbols = (rawSymbol) => {
    const s = (rawSymbol || '').toUpperCase();
    switch (s) {
      case '^GSPC':
        return { display: 'SPX', tv: 'SP:SPX' };
      case '^DJI':
        return { display: 'DJI', tv: 'DJ:DJI' };
      case '^IXIC':
        return { display: 'NDQ', tv: 'NASDAQ:IXIC' };
      case '^RUT':
        return { display: 'BTCUSD', tv: 'BTCUSD' };
      case '^VIX':
        return { display: 'ETHUSD', tv: 'ETHUSD' };
      default:
        return { display: s.replace('^', ''), tv: s.replace('^', '') };
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="panel card-panel p-6 hover:shadow-xl transition-all stock-card cursor-pointer hover:scale-105"
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">
            {getDisplayAndTvSymbols(index.symbol).display}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
            {index.name}
          </p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {formatNumber(index.price)}
          </p>
          <p className={`text-sm font-medium ${getChangeColor(index.change)}`}>
            {index.change >= 0 ? '+' : ''}{index.change?.toFixed(2)}
            ({index.changePercent >= 0 ? '+' : ''}{index.changePercent?.toFixed(2)}%)
          </p>
        </div>
      </div>

      {/* Index Type Badge */}
      <div className="flex justify-between items-center mb-4">
        <div className="px-3 py-1 rounded-full text-sm font-bold bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">
          INDEX
        </div>
        <div className="flex items-center space-x-1">
          {index.change >= 0 ? (
            <TrendingUp className="w-4 h-4 text-green-600" />
          ) : (
            <TrendingDown className="w-4 h-4 text-red-600" />
          )}
        </div>
      </div>

      {/* Index Stats */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="p-3 rounded-lg border-2 bg-gray-50 border-gray-200 dark:bg-gray-700 dark:border-gray-600">
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-blue-600" />
            <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Current Price</span>
          </div>
          <div className="text-sm font-bold text-gray-900 dark:text-white mt-1">
            {formatNumber(index.price)}
          </div>
        </div>

        <div className="p-3 rounded-lg border-2 bg-gray-50 border-gray-200 dark:bg-gray-700 dark:border-gray-600">
          <div className="flex items-center space-x-2">
            {index.change >= 0 ? (
              <TrendingUp className="w-4 h-4 text-green-600" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-600" />
            )}
            <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Day Change</span>
          </div>
          <div className={`text-sm font-bold mt-1 ${getChangeColor(index.change)}`}>
            {index.changePercent >= 0 ? '+' : ''}{index.changePercent?.toFixed(2)}%
          </div>
        </div>
      </div>

      {/* Index Chart - TradingView Symbol Overview */}
      <div className="mb-4">
        <TradingViewSymbolOverview symbol={getDisplayAndTvSymbols(index.symbol).tv} height={80} />
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-2">
        <a
          href={`https://www.tradingview.com/symbols/${getDisplayAndTvSymbols(index.symbol).display}`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 flex items-center justify-center space-x-2 py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          onClick={(e) => e.stopPropagation()}
        >
          <ExternalLink className="w-4 h-4" />
          <span className="text-sm">View on TradingView</span>
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

export default IndexCard;
