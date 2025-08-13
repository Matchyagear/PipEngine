import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const WatchlistModal = ({ 
  isOpen, 
  onClose, 
  onSubmit,
  newWatchlistName,
  setNewWatchlistName,
  newWatchlistTickers,
  setNewWatchlistTickers,
  isSubmitting = false
}) => {
  const nameInputRef = useRef(null);
  const tickersInputRef = useRef(null);

  // Focus the input when modal opens
  useEffect(() => {
    if (isOpen && nameInputRef.current) {
      // Delay focus to ensure modal is fully rendered
      setTimeout(() => {
        nameInputRef.current?.focus();
      }, 100);
    }
  }, [isOpen]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit();
  };

  const handleNameChange = (e) => {
    setNewWatchlistName(e.target.value);
  };

  const handleTickersChange = (e) => {
    setNewWatchlistTickers(e.target.value);
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        onClick={handleBackdropClick}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full"
          onClick={(e) => e.stopPropagation()}
        >
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            Create Watchlist
          </h2>
          
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-gray-700 dark:text-gray-300 mb-2">
                Watchlist Name
              </label>
              <input
                ref={nameInputRef}
                type="text"
                value={newWatchlistName}
                onChange={handleNameChange}
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="My Watchlist"
                autoComplete="off"
                required
              />
            </div>

            <div className="mb-6">
              <label className="block text-gray-700 dark:text-gray-300 mb-2">
                Tickers (comma separated)
              </label>
              <textarea
                ref={tickersInputRef}
                value={newWatchlistTickers}
                onChange={handleTickersChange}
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="AAPL, MSFT, GOOGL, TSLA"
                rows="3"
                autoComplete="off"
                required
              />
            </div>

            <div className="flex space-x-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className={`flex-1 py-2 px-4 rounded-lg btn-primary text-white ${isSubmitting ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}
              >
                {isSubmitting ? 'Creating…' : 'Create Watchlist'}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="py-2 px-4 bg-gray-600 hover:bg-gray-700 text-white rounded-lg btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default WatchlistModal;