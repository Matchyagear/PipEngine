import React from 'react';
import { motion } from 'framer-motion';
import { Clock, ExternalLink, Globe } from 'lucide-react';

// News Sidebar Component
export const NewsSidebar = ({ news, loading }) => {
  const formatTimeAgo = (dateString) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now - date;
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffMins = Math.floor(diffMs / (1000 * 60));

      if (diffHours > 24) {
        return `${Math.floor(diffHours / 24)}d ago`;
      } else if (diffHours > 0) {
        return `${diffHours}h ago`;
      } else if (diffMins > 0) {
        return `${diffMins}m ago`;
      } else {
        return 'Just now';
      }
    } catch {
      return 'Recently';
    }
  };

  if (loading) {
    return (
      <div className="w-80 panel p-4 border-l border-carbon-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">📰 Market News</h3>
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded mb-2"></div>
              <div className="h-3 bg-gray-200 dark:bg-gray-600 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="w-80 panel p-4 max-h-screen overflow-y-auto border-l border-carbon-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
        <Globe className="w-5 h-5 mr-2" />
        Market News
      </h3>

      <div className="space-y-3">
        {news.slice(0, 12).map((article, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="p-3 bg-carbon-700 rounded-lg hover:bg-carbon-600 transition-colors cursor-pointer"
            onClick={() => window.open(article.url, '_blank')}
          >
            <h4 className="text-sm font-medium text-gray-900 dark:text-white line-clamp-2 mb-2">
              {article.title}
            </h4>

            <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
              <span className="truncate mr-2">{article.source}</span>
              <div className="flex items-center">
                <Clock className="w-3 h-3 mr-1" />
                <span>{formatTimeAgo(article.published_at)}</span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
          Click any article to read more
        </p>
      </div>
    </div>
  );
};

// News Tab Component
export const NewsTab = ({ news, loading, searchQuery }) => {
  const formatTimeAgo = (dateString) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now - date;
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffMins = Math.floor(diffMs / (1000 * 60));

      if (diffHours > 24) {
        return `${Math.floor(diffHours / 24)} days ago`;
      } else if (diffHours > 0) {
        return `${diffHours} hours ago`;
      } else if (diffMins > 0) {
        return `${diffMins} minutes ago`;
      } else {
        return 'Just now';
      }
    } catch {
      return 'Recently';
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center">
          <div className="h-8 bg-gray-200 dark:bg-gray-600 rounded w-48 animate-pulse"></div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(9)].map((_, i) => (
            <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-6 animate-pulse">
              <div className="h-6 bg-gray-200 dark:bg-gray-600 rounded mb-4"></div>
              <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded mb-2"></div>
              <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded w-2/3 mb-4"></div>
              <div className="h-3 bg-gray-200 dark:bg-gray-600 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          {searchQuery ? `News Results for "${searchQuery}"` : 'Financial News'}
        </h2>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          {news.length} articles found
        </div>
      </div>

      {/* News Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {news.map((article, index) => (
          <motion.article
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="panel p-6 cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => window.open(article.url, '_blank')}
          >
            {/* Article Image */}
            {article.image_url && (
              <div className="mb-4">
                <img
                  src={article.image_url}
                  alt={article.title}
                  className="w-full h-48 object-cover rounded-lg"
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
              </div>
            )}

            {/* Article Content */}
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white line-clamp-2">
                {article.title}
              </h3>

              <p className="text-gray-600 dark:text-gray-300 text-sm line-clamp-3">
                {article.description}
              </p>

              {/* Article Meta */}
              <div className="flex items-center justify-between pt-3 border-t border-gray-200 dark:border-gray-600">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-medium text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/30 px-2 py-1 rounded">
                    {article.source}
                  </span>
                </div>

                <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
                  <Clock className="w-3 h-3 mr-1" />
                  <span>{formatTimeAgo(article.published_at)}</span>
                </div>
              </div>

              {/* Read More Link */}
              <div className="flex items-center text-blue-600 dark:text-blue-400 text-sm font-medium">
                <span>Read full article</span>
                <ExternalLink className="w-3 h-3 ml-1" />
              </div>
            </div>
          </motion.article>
        ))}
      </div>

      {/* Empty State */}
      {news.length === 0 && !loading && (
        <div className="text-center py-12">
          <Globe className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No news found
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            {searchQuery ? 'Try a different search term' : 'No news articles available at the moment'}
          </p>
        </div>
      )}
    </div>
  );
};

// Stock News Component (for individual stock cards)
export const StockNews = ({ news, ticker }) => {
  const formatTimeAgo = (dateString) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffHours = Math.floor((now - date) / (1000 * 60 * 60));
      return diffHours > 24 ? `${Math.floor(diffHours / 24)}d ago` : `${diffHours}h ago`;
    } catch {
      return 'Recent';
    }
  };

  if (!news || news.length === 0) {
    return (
      <div className="text-center text-gray-500 dark:text-gray-400 text-sm">
        No recent news for {ticker}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
        Recent News
      </h4>

      {news.slice(0, 3).map((article, index) => (
        <div
          key={index}
          className="p-2 bg-gray-50 dark:bg-gray-700 rounded cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
          onClick={() => window.open(article.url, '_blank')}
        >
          <p className="text-xs font-medium text-gray-900 dark:text-white line-clamp-2 mb-1">
            {article.title}
          </p>
          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <span className="truncate">{article.source}</span>
            <span>{formatTimeAgo(article.published_at)}</span>
          </div>
        </div>
      ))}
    </div>
  );
};
