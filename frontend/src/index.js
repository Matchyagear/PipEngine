import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

// =============================================================================
// SERVICE WORKER REGISTRATION FOR PERFORMANCE & OFFLINE SUPPORT
// =============================================================================

// Register service worker for PWA functionality
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('🎯 SERVICE WORKER: Registered successfully');
        console.log('⚡ PERFORMANCE: Offline caching enabled');

        // Listen for updates
        registration.addEventListener('updatefound', () => {
          console.log('🔄 SERVICE WORKER: Update found, installing...');
        });
      })
      .catch((error) => {
        console.log('❌ SERVICE WORKER: Registration failed:', error);
      });
  });
}

// Performance monitoring
const startTime = performance.now();
window.addEventListener('load', () => {
  const loadTime = performance.now() - startTime;
  console.log(`⚡ PERFORMANCE: Page loaded in ${loadTime.toFixed(2)}ms`);

  // Track navigation timing
  if (performance.navigation) {
    const timing = performance.timing;
    const domContentLoaded = timing.domContentLoadedEventEnd - timing.navigationStart;
    const fullLoad = timing.loadEventEnd - timing.navigationStart;

    console.log(`📊 PERFORMANCE: DOM ready in ${domContentLoaded}ms`);
    console.log(`📊 PERFORMANCE: Full load in ${fullLoad}ms`);
  }
});

// Global error handler for external scripts (like TradingView)
window.addEventListener('error', (event) => {
  // Suppress script errors from external sources
  if (event.message === 'Script error.' ||
    (event.filename && (
      event.filename.includes('tradingview.com') ||
      event.filename.includes('s3.tradingview.com') ||
      event.filename === ''
    ))) {
    console.log('📊 TRADINGVIEW: External script error suppressed for better UX');
    event.preventDefault();
    return false;
  }

  // Let other errors through for debugging
  return true;
});

// Additional error suppression for unhandled promise rejections from external scripts
window.addEventListener('unhandledrejection', (event) => {
  if (event.reason && typeof event.reason === 'string' &&
    event.reason.includes('tradingview')) {
    console.log('📊 TRADINGVIEW: Promise rejection suppressed for external script');
    event.preventDefault();
    return false;
  }
});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
