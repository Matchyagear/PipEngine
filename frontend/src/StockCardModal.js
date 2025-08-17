import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import StockCard from './StockCard';

const StockCardModal = ({ isOpen, onClose, stock, aiProvider = 'gemini', onOpenChart }) => {
  console.log('StockCardModal render:', { isOpen, stock: stock?.ticker });
  if (!isOpen || !stock) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black bg-opacity-50"
          onClick={onClose}
        />

        {/* Modal Content */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8, y: 50 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.8, y: 50 }}
          className="relative bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto"
        >
          {/* Close Button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-10 p-2 text-gray-300 hover:text-white bg-carbon-800 rounded-full shadow-lg hover:shadow-xl transition-all"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Full Stock Card */}
          <div className="p-4">
            <StockCard
              stock={stock}
              aiProvider={aiProvider}
              onOpenChart={onOpenChart}
            />
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default StockCardModal;
