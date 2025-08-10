import React from 'react';
import { motion } from 'framer-motion';
import TradingViewMiniChart from './components/TradingViewMiniChart';

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
        return { display: 'SPY', tv: 'SPY' };
      case '^DJI':
        return { display: 'US30', tv: 'FOREXCOM:US30' };
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
      className="panel card-panel p-0 overflow-hidden hover:shadow-xl transition-all stock-card cursor-pointer hover:scale-105"
      onClick={onClick}
      style={{ height: 140 }}
    >
      <TradingViewMiniChart symbol={getDisplayAndTvSymbols(index.symbol).tv} height={140} dateRange="1D" />
    </motion.div>
  );
};

export default IndexCard;
