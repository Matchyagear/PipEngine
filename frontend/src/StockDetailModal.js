import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Volume2, 
  Target,
  Brain,
  ExternalLink,
  Clock,
  BarChart3,
  Zap,
  Globe,
  Calendar,
  DollarSign
} from 'lucide-react';
import { StockNews } from './NewsComponents';

const StockDetailModal = ({ stock, isOpen, onClose, aiProvider, API_BASE_URL }) => {
  const [stockNews, setStockNews] = useState([]);
  const [loadingNews, setLoadingNews] = useState(false);
  const [aiSummary, setAiSummary] = useState('');
  const [loadingAI, setLoadingAI] = useState(false);

  useEffect(() => {
    if (isOpen && stock) {
      fetchStockNews();
      fetchAISummary();
    }
  }, [isOpen, stock]);

  const fetchStockNews = async () => {
    if (!stock) return;
    
    try {
      setLoadingNews(true);
      const response = await fetch(`${API_BASE_URL}/api/news/stock/${stock.ticker}`);
      const data = await response.json();
      setStockNews(data.news || []);
    } catch (error) {
      console.error('Error fetching stock news:', error);
    } finally {
      setLoadingNews(false);
    }
  };

  const fetchAISummary = async () => {
    if (!stock || stock.aiSummary || stock.openaiSummary) {
      setAiSummary(stock.aiSummary || stock.openaiSummary || '');
      return;
    }

    try {
      setLoadingAI(true);
      const response = await fetch(`${API_BASE_URL}/api/stocks/${stock.ticker}?ai_provider=${aiProvider}`);
      const data = await response.json();
      setAiSummary(data.aiSummary || data.openaiSummary || 'AI summary not available');
    } catch (error) {
      setAiSummary('Error loading AI summary');
    } finally {
      setLoadingAI(false);
    }
  };

  const getCriteriaIcon = (criteriaName) => {
    switch (criteriaName) {
      case 'trend': return <TrendingUp className="w-5 h-5" />;
      case 'momentum': return <Activity className="w-5 h-5" />;
      case 'volume': return <Volume2 className="w-5 h-5" />;
      case 'priceAction': return <Target className="w-5 h-5" />;
      case 'oversold': return <TrendingDown className="w-5 h-5" />;
      case 'breakout': return <Zap className="w-5 h-5" />;
      default: return null;
    }
  };

  const getCriteriaDescription = (criteriaName) => {
    switch (criteriaName) {
      case 'trend': return '50-day MA > 200-day MA and price above both';
      case 'momentum': return 'RSI > 50, MACD positive, Stochastic > 20';
      case 'volume': return 'Average volume > 1M, Relative volume > 1.5x';
      case 'priceAction': return 'Price within Bollinger Bands, above 50-day MA';
      case 'oversold': return 'RSI < 30 and Stochastic < 20 (potential reversal)';
      case 'breakout': return 'Price above upper Bollinger Band with high volume';
      default: return '';
    }
  };

  if (!isOpen || !stock) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="bg-white dark:bg-gray-800 rounded-2xl max-w-6xl w-full max-h-[90vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6 rounded-t-2xl">
            <div className="flex justify-between items-start">
              <div className="flex items-center space-x-4">
                <div>
                  <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
                    {stock.ticker}
                  </h2>
                  <p className="text-lg text-gray-600 dark:text-gray-400">
                    {stock.companyName}
                  </p>
                </div>
                
                <div className="text-right">
                  <p className="text-3xl font-bold text-gray-900 dark:text-white">
                    ${stock.currentPrice.toFixed(2)}
                  </p>
                  <p className={`text-lg font-medium ${
                    stock.priceChangePercent >= 0 
                      ? 'text-green-600 dark:text-green-400' 
                      : 'text-red-600 dark:text-red-400'
                  }`}>
                    {stock.priceChangePercent >= 0 ? '+' : ''}
                    {stock.priceChangePercent.toFixed(2)}% 
                    (${stock.priceChange.toFixed(2)})
                  </p>
                </div>
              </div>
              
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Score and Rank */}
            <div className="flex items-center space-x-4 mt-4">
              <div className={`px-4 py-2 rounded-full text-lg font-bold ${
                stock.score === 4 ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' :
                stock.score === 3 ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300' :
                stock.score >= 2 ? 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300' :
                'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
              }`}>
                Score: {stock.score}/4
              </div>
              <div className="text-lg text-gray-600 dark:text-gray-400">
                Rank #{stock.rank}
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column - Analysis */}
            <div className="lg:col-span-2 space-y-6">
              {/* Criteria Analysis */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Trading Criteria Analysis
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(stock.passes).map(([criteria, passed]) => (
                    <div
                      key={criteria}
                      className={`p-4 rounded-lg border-2 ${
                        passed 
                          ? 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-700' 
                          : 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-700'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className={passed ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                          {getCriteriaIcon(criteria)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <span className={`font-semibold capitalize ${
                              passed ? 'text-green-800 dark:text-green-300' : 'text-red-800 dark:text-red-300'
                            }`}>
                              {criteria === 'priceAction' ? 'Price Action' : criteria}
                            </span>
                            <span className={`text-sm font-medium ${
                              passed ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                            }`}>
                              {passed ? 'PASS' : 'FAIL'}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                            {getCriteriaDescription(criteria)}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Technical Indicators */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Technical Indicators
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                    <div className="text-sm text-gray-500 dark:text-gray-400">RSI (14)</div>
                    <div className={`text-2xl font-bold ${
                      stock.RSI > 70 ? 'text-red-600' : stock.RSI < 30 ? 'text-green-600' : 'text-gray-900 dark:text-white'
                    }`}>
                      {stock.RSI.toFixed(1)}
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                    <div className="text-sm text-gray-500 dark:text-gray-400">MACD</div>
                    <div className={`text-2xl font-bold ${
                      stock.MACD > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {stock.MACD.toFixed(3)}
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                    <div className="text-sm text-gray-500 dark:text-gray-400">Rel Volume</div>
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {stock.relativeVolume.toFixed(1)}x
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                    <div className="text-sm text-gray-500 dark:text-gray-400">50-day MA</div>
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      ${stock.fiftyMA.toFixed(2)}
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                    <div className="text-sm text-gray-500 dark:text-gray-400">200-day MA</div>
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      ${stock.twoHundredMA.toFixed(2)}
                    </div>
                  </div>
                  
                  {stock.stochastic && (
                    <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                      <div className="text-sm text-gray-500 dark:text-gray-400">Stochastic</div>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {stock.stochastic.toFixed(1)}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* AI Analysis */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                  <Brain className="w-5 h-5 mr-2" />
                  AI Analysis ({aiProvider === 'openai' ? 'OpenAI' : 'Gemini'})
                </h3>
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-700">
                  {loadingAI ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                      Loading AI analysis...
                    </div>
                  ) : (
                    <p className="text-blue-700 dark:text-blue-300">
                      {aiSummary}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Right Column - Chart and News */}
            <div className="space-y-6">
              {/* Finviz Chart */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Price Chart
                </h3>
                <div className="rounded-lg overflow-hidden">
                  <img 
                    src={`https://finviz.com/chart.ashx?t=${stock.ticker}&ty=c&ta=1&p=d&s=l`}
                    alt={`${stock.ticker} chart`}
                    className="w-full h-64 object-cover"
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                </div>
                <div className="mt-2">
                  <a
                    href={`https://finviz.com/quote.ashx?t=${stock.ticker}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-blue-600 hover:text-blue-700 dark:text-blue-400 text-sm"
                  >
                    <span>View on Finviz</span>
                    <ExternalLink className="w-3 h-3 ml-1" />
                  </a>
                </div>
              </div>

              {/* Stock News */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                  <Globe className="w-5 h-5 mr-2" />
                  Recent News
                </h3>
                <div className="max-h-96 overflow-y-auto">
                  {loadingNews ? (
                    <div className="space-y-3">
                      {[...Array(3)].map((_, i) => (
                        <div key={i} className="animate-pulse">
                          <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded mb-2"></div>
                          <div className="h-3 bg-gray-200 dark:bg-gray-600 rounded w-3/4"></div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <StockNews news={stockNews} ticker={stock.ticker} />
                  )}
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default StockDetailModal;