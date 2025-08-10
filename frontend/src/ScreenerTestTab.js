import React, { useCallback, useEffect, useMemo, useState } from 'react';
import StockCardModal from './StockCardModal';

// Lightweight, no-API custom screener UI with basic drag-and-drop to order criteria.
// This only manages UI state; no backend calls are made.

const defaultCriteria = [
  { id: 'price', label: 'Price ($)', type: 'range', value: [5, 200], min: 0, max: 1000, step: 1 },
  { id: 'volume', label: 'Avg Volume (min)', type: 'number', value: 500000, min: 0, step: 1000 },
  { id: 'marketCap', label: 'Market Cap (min, $B)', type: 'number', value: 2, min: 0, step: 0.1 },
  { id: 'sector', label: 'Sector', type: 'multiselect', value: [], options: ['Technology', 'Healthcare', 'Financial Services', 'Energy', 'Industrials', 'Consumer Discretionary', 'Consumer Staples', 'Utilities', 'Materials', 'Real Estate', 'Communication Services'] },
  { id: 'rsi', label: 'RSI', type: 'range', value: [20, 80], min: 0, max: 100, step: 1 },
  { id: 'smaCross', label: '50MA > 200MA', type: 'boolean', value: false },
];

const CriterionRow = ({ item, index, onDragStart, onDragOver, onDrop, onChange }) => {
  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, index)}
      onDragOver={(e) => onDragOver(e, index)}
      onDrop={(e) => onDrop(e, index)}
      className="flex flex-col gap-2 p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
    >
      <div className="flex items-center justify-between">
        <div className="font-medium text-gray-900 dark:text-white">{item.label}</div>
        <span className="cursor-grab text-gray-400" title="Drag to reorder">⋮⋮</span>
      </div>

      {item.type === 'range' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 items-center">
          <div className="flex items-center gap-2">
            <input
              type="number"
              className="w-full border rounded px-2 py-1 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white"
              value={item.value[0]}
              min={item.min}
              max={item.max}
              step={item.step}
              onChange={(e) => onChange(item.id, [Number(e.target.value), item.value[1]])}
            />
            <span className="text-gray-500">to</span>
            <input
              type="number"
              className="w-full border rounded px-2 py-1 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white"
              value={item.value[1]}
              min={item.min}
              max={item.max}
              step={item.step}
              onChange={(e) => onChange(item.id, [item.value[0], Number(e.target.value)])}
            />
          </div>
          <input
            type="range"
            min={item.min}
            max={item.max}
            step={item.step}
            value={item.value[0]}
            onChange={(e) => onChange(item.id, [Number(e.target.value), item.value[1]])}
          />
          <input
            type="range"
            min={item.min}
            max={item.max}
            step={item.step}
            value={item.value[1]}
            onChange={(e) => onChange(item.id, [item.value[0], Number(e.target.value)])}
          />
        </div>
      )}

      {item.type === 'number' && (
        <input
          type="number"
          className="w-48 border rounded px-2 py-1 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white"
          value={item.value}
          min={item.min}
          step={item.step}
          onChange={(e) => onChange(item.id, Number(e.target.value))}
        />
      )}

      {item.type === 'boolean' && (
        <label className="inline-flex items-center gap-2">
          <input
            type="checkbox"
            checked={!!item.value}
            onChange={(e) => onChange(item.id, e.target.checked)}
          />
          <span className="text-gray-700 dark:text-gray-300">Enabled</span>
        </label>
      )}

      {item.type === 'multiselect' && (
        <div className="flex flex-wrap gap-2">
          {item.options.map((opt) => {
            const active = item.value.includes(opt);
            return (
              <button
                key={opt}
                className={`px-2 py-1 rounded border text-sm ${active ? 'bg-blue-600 text-white border-blue-600' : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-600'}`}
                onClick={() => {
                  const next = active ? item.value.filter((v) => v !== opt) : [...item.value, opt];
                  onChange(item.id, next);
                }}
                type="button"
              >
                {opt}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

const ScreenerTestTab = ({ onOpenChart }) => {
  const [criteria, setCriteria] = useState(defaultCriteria);
  const [dragIndex, setDragIndex] = useState(null);
  const [snapshot, setSnapshot] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [loadingTicker, setLoadingTicker] = useState(null);
  const [showJson, setShowJson] = useState(false); // collapsed by default
  const [sortKey, setSortKey] = useState('ticker'); // ticker | price | rsi | score | setup | volume
  const [sortDir, setSortDir] = useState('asc');

  const toggleSort = (key) => {
    if (sortKey === key) {
      setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const computeSwingScore = (s) => {
    const baseScore = typeof s.score === 'number' ? s.score : 2;
    const rsi = typeof s.RSI === 'number' ? s.RSI : null;
    const macd = typeof s.MACD === 'number' ? s.MACD : null;
    const relVol = typeof s.relativeVolume === 'number' ? s.relativeVolume : null;
    const stoch = typeof s.stochastic === 'number' ? s.stochastic : null;
    const price = typeof s.currentPrice === 'number' ? s.currentPrice : null;
    const ma50 = typeof s.fiftyMA === 'number' ? s.fiftyMA : null;
    const ma200 = typeof s.twoHundredMA === 'number' ? s.twoHundredMA : null;
    const marketChg = typeof s.marketChangePercent === 'number' ? s.marketChangePercent : null;
    const sectorChg = typeof s.sectorChangePercent === 'number' ? s.sectorChangePercent : null;
    const stockChg = typeof s.priceChangePercent === 'number' ? s.priceChangePercent : null;

    const W_BASE = 38;
    const W_OVERSOLD = 10;
    const W_BREAKOUT = 8;
    const W_TREND = 16;
    const W_MACD = 8;
    const W_RSI = 14;
    const W_VOLUME = 4;
    const W_STOCH = 2;
    const W_MARKET = 6;
    const W_SECTOR = 4;
    const total = W_BASE + W_OVERSOLD + W_BREAKOUT + W_TREND + W_MACD + W_RSI + W_VOLUME + W_STOCH + W_MARKET + W_SECTOR;

    let pts = 0;
    pts += (Math.max(0, Math.min(4, baseScore)) / 4) * W_BASE;
    if (s.passes?.oversold) pts += W_OVERSOLD;
    if (s.passes?.breakout) pts += W_BREAKOUT;
    if (ma50 !== null && ma200 !== null) {
      if (ma50 > ma200) pts += W_TREND * 0.6;
      if (price !== null && price > ma50 && price > ma200) pts += W_TREND * 0.4;
    }
    if (macd !== null && macd > 0) pts += W_MACD;
    if (rsi !== null) {
      if (rsi >= 35 && rsi <= 55) pts += W_RSI;
      else if ((rsi >= 30 && rsi < 35) || (rsi > 55 && rsi <= 60)) pts += W_RSI * 0.5;
    }
    if (relVol !== null) {
      if (relVol >= 1.5) pts += W_VOLUME;
      else if (relVol >= 1.2) pts += W_VOLUME * 0.5;
    }
    if (stoch !== null && stoch >= 20 && stoch <= 80) pts += W_STOCH;
    if (marketChg !== null && stockChg !== null) {
      if ((marketChg >= 0 && stockChg >= 0) || (marketChg < 0 && stockChg < 0)) pts += W_MARKET;
    }
    if (sectorChg !== null && stockChg !== null) {
      if ((sectorChg >= 0 && stockChg >= 0) || (sectorChg < 0 && stockChg < 0)) pts += W_SECTOR;
    }
    return Math.max(1, Math.min(100, Math.round((pts / total) * 100)));
  };

  const onDragStart = useCallback((e, index) => {
    setDragIndex(index);
    e.dataTransfer.effectAllowed = 'move';
  }, []);

  const onDragOver = useCallback((e, index) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback((e, index) => {
    e.preventDefault();
    if (dragIndex === null || dragIndex === index) return;
    setCriteria((prev) => {
      const next = [...prev];
      const [moved] = next.splice(dragIndex, 1);
      next.splice(index, 0, moved);
      return next;
    });
    setDragIndex(null);
  }, [dragIndex]);

  const onChange = useCallback((id, value) => {
    setCriteria((prev) => prev.map((c) => (c.id === id ? { ...c, value } : c)));
  }, []);

  const query = useMemo(() => {
    // Produce a normalized filter spec we can later POST to backend
    return criteria.map((c) => ({ id: c.id, value: c.value }));
  }, [criteria]);

  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

  const openDetails = async (s) => {
    // If snapshot already has full fields, open immediately
    if (s && s.passes && typeof s.score === 'number') {
      setSelected(s);
      setShowModal(true);
      return;
    }
    try {
      setLoadingTicker(s.ticker);
      const res = await fetch(`${API_BASE_URL}/api/stocks/${(s.ticker || '').toUpperCase()}`);
      const full = await res.json();
      if (full && full.ticker) {
        setSelected(full);
        setShowModal(true);
      } else {
        setSelected(s);
        setShowModal(true);
      }
    } catch (e) {
      setSelected(s);
      setShowModal(true);
    }
    finally {
      setLoadingTicker(null);
    }
  };

  const loadSnapshot = async () => {
    try {
      setLoading(true);
      setError('');
      const res = await fetch(`${API_BASE_URL}/api/screener/snapshot`, { cache: 'no-store' });
      const data = await res.json();
      setSnapshot(Array.isArray(data.snapshot) ? data.snapshot : []);
    } catch (e) {
      setError('Failed to load snapshot');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSnapshot();
  }, [API_BASE_URL]);

  const filtered = useMemo(() => {
    if (!snapshot.length) return [];
    let out = snapshot;
    for (const c of criteria) {
      switch (c.id) {
        case 'price': {
          const [min, max] = c.value;
          out = out.filter((s) => s.currentPrice >= min && s.currentPrice <= max);
          break;
        }
        case 'volume': {
          out = out.filter((s) => (s.averageVolume || 0) >= c.value);
          break;
        }
        case 'marketCap': {
          // Not available in snapshot; skip for now
          break;
        }
        case 'sector': {
          if (c.value.length) out = out.filter((s) => s.sector && c.value.includes(s.sector));
          break;
        }
        case 'rsi': {
          const [min, max] = c.value;
          out = out.filter((s) => (s.RSI ?? 50) >= min && (s.RSI ?? 50) <= max);
          break;
        }
        case 'smaCross': {
          if (c.value) out = out.filter((s) => s.fiftyMA > s.twoHundredMA);
          break;
        }
        default:
          break;
      }
    }
    // sorting by selected column
    const dir = sortDir === 'asc' ? 1 : -1;
    const getNum = (v, d = 0) => (typeof v === 'number' && !Number.isNaN(v) ? v : d);
    const getStr = (v) => (v ? String(v) : '');
    const sorted = out.slice().sort((a, b) => {
      switch (sortKey) {
        case 'ticker':
          return dir * getStr(a.ticker).localeCompare(getStr(b.ticker));
        case 'price':
          return dir * (getNum(a.currentPrice) - getNum(b.currentPrice));
        case 'rsi':
          return dir * (getNum(a.RSI) - getNum(b.RSI));
        case 'score': {
          // Put undefined scores at the end for asc; start for desc
          const as = (typeof a.score === 'number') ? a.score : (sortDir === 'asc' ? -Infinity : Infinity);
          const bs = (typeof b.score === 'number') ? b.score : (sortDir === 'asc' ? -Infinity : Infinity);
          return dir * (as - bs);
        }
        case 'setup': {
          const as = computeSwingScore(a);
          const bs = computeSwingScore(b);
          return dir * (as - bs);
        }
        case 'volume':
          return dir * (getNum(a.averageVolume) - getNum(b.averageVolume));
        default:
          return 0;
      }
    });
    return sorted;
  }, [snapshot, criteria, sortKey, sortDir]);

  return (
    <div className="h-screen flex flex-col">
      <div className="panel p-4 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">Custom Screener (Test v2)</h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">Reorder criteria by dragging. Adjust values below. No API calls are made yet.</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
              onClick={() => navigator.clipboard.writeText(JSON.stringify(query))}
            >
              Copy Query JSON
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1">
        {/* Left: criteria (narrow) */}
        <div className="lg:col-span-1 space-y-2 overflow-auto">
          {loading && <div className="text-sm text-gray-500">Loading snapshot…</div>}
          {error && <div className="text-sm text-red-600">{error}</div>}
          {criteria.map((item, idx) => (
            <CriterionRow
              key={item.id}
              item={item}
              index={idx}
              onDragStart={onDragStart}
              onDragOver={onDragOver}
              onDrop={onDrop}
              onChange={onChange}
            />
          ))}
        </div>

        {/* Right: preview (wide) */}
        <div className="lg:col-span-2 space-y-4">
          {/* Collapsible JSON box (collapsed by default) */}
          <div className="panel p-0">
            <div className="flex items-center justify-between px-4 py-2">
              <div className="text-sm font-semibold text-gray-900 dark:text-white">Current Filter JSON</div>
              <button
                className="text-xs px-2 py-1 rounded bg-gray-200 dark:bg-gray-700"
                onClick={() => setShowJson(!showJson)}
              >
                {showJson ? 'Hide' : 'Show'}
              </button>
            </div>
            {showJson && (
              <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-auto max-h-64 bg-gray-50 dark:bg-gray-900/30 p-3 rounded-b-xl">
                {JSON.stringify(query, null, 2)}
              </pre>
            )}
          </div>

          <div className="panel p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-semibold text-gray-900 dark:text-white">Preview ({filtered.length})</div>
              <button className="px-2 py-1 text-xs bg-gray-200 dark:bg-gray-700 rounded" onClick={loadSnapshot}>Reload Snapshot</button>
            </div>
            {/* Sortable header */}
            <div className="grid grid-cols-6 gap-2 items-center text-xs font-semibold text-gray-300 border-b border-gray-700/60 py-1 mb-1">
              <button className="text-left" onClick={() => toggleSort('ticker')}>
                Ticker {sortKey === 'ticker' ? (sortDir === 'asc' ? '▲' : '▼') : ''}
              </button>
              <button className="text-right" onClick={() => toggleSort('price')}>
                Price {sortKey === 'price' ? (sortDir === 'asc' ? '▲' : '▼') : ''}
              </button>
              <button className="text-center" onClick={() => toggleSort('rsi')}>
                RSI {sortKey === 'rsi' ? (sortDir === 'asc' ? '▲' : '▼') : ''}
              </button>
              <button className="text-center" onClick={() => toggleSort('score')}>
                Score {sortKey === 'score' ? (sortDir === 'asc' ? '▲' : '▼') : ''}
              </button>
              <button className="text-center" onClick={() => toggleSort('setup')}>
                Setup {sortKey === 'setup' ? (sortDir === 'asc' ? '▲' : '▼') : ''}
              </button>
              <button className="text-right" onClick={() => toggleSort('volume')}>
                Volume {sortKey === 'volume' ? (sortDir === 'asc' ? '▲' : '▼') : ''}
              </button>
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400 max-h-[70vh] overflow-auto">
              {filtered.slice(0, 50).map((s) => (
                <div
                  key={s.ticker}
                  className="flex items-center gap-2 py-1 border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/40"
                  title="Click to open details"
                >
                  <button
                    className="flex-1 text-left cursor-pointer"
                    onClick={() => { if (loadingTicker !== s.ticker) openDetails(s); }}
                    disabled={loadingTicker === s.ticker}
                  >
                    <div className="grid grid-cols-6 gap-2 items-center text-sm">
                      <span className="font-mono">{s.ticker}</span>
                      <span className="text-right">${s.currentPrice.toFixed(2)}</span>
                      <span className="text-center">RSI {Math.round(s.RSI ?? 50)}</span>
                      <span className="text-center">Score {typeof s.score === 'number' ? `${s.score}/4` : '-'}</span>
                      <span className="text-center">{computeSwingScore(s)}</span>
                      <span className="text-right">Vol {s.averageVolume?.toLocaleString?.() || '-'}</span>
                    </div>
                  </button>
                  <button
                    className={`px-2 py-0.5 text-[10px] rounded ${loadingTicker === s.ticker ? 'bg-gray-400 cursor-wait' : 'bg-blue-600 hover:bg-blue-700 cursor-pointer'} text-white flex items-center gap-1`}
                    onClick={() => { if (loadingTicker !== s.ticker) openDetails(s); }}
                    disabled={loadingTicker === s.ticker}
                  >
                    {loadingTicker === s.ticker ? (
                      <span className="inline-block w-3 h-3 border-2 border-white border-b-transparent rounded-full animate-spin"></span>
                    ) : null}
                    <span>{loadingTicker === s.ticker ? 'Loading' : 'View'}</span>
                  </button>
                </div>
              ))}
              {filtered.length > 50 && (
                <div className="text-center py-2 text-gray-500">Showing first 50...</div>
              )}
            </div>
          </div>
        </div>
      </div>
      <StockCardModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        stock={selected}
        aiProvider="gemini"
        onOpenChart={(s) => onOpenChart && onOpenChart(s)}
      />
    </div>
  );
};

export default ScreenerTestTab;
