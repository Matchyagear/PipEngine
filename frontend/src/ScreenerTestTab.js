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

const ScreenerTestTab = () => {
  const [criteria, setCriteria] = useState(defaultCriteria);
  const [dragIndex, setDragIndex] = useState(null);
  const [snapshot, setSnapshot] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);
  const [showModal, setShowModal] = useState(false);

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
    // basic sorting: price asc
    return out.slice().sort((a, b) => a.currentPrice - b.currentPrice);
  }, [snapshot, criteria]);

  return (
    <div className="h-screen flex flex-col">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4 mb-4">
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
        <div className="lg:col-span-2 space-y-3 overflow-auto">
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

        <div className="space-y-4">
          <div className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Current Filter JSON</div>
            <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-auto max-h-64 bg-gray-50 dark:bg-gray-900/30 p-3 rounded">
              {JSON.stringify(query, null, 2)}
            </pre>
          </div>

          <div className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm font-semibold text-gray-900 dark:text-white">Preview ({filtered.length})</div>
              <button className="px-2 py-1 text-xs bg-gray-200 dark:bg-gray-700 rounded" onClick={loadSnapshot}>Reload Snapshot</button>
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400 max-h-72 overflow-auto">
              {filtered.slice(0, 50).map((s) => (
                <div
                  key={s.ticker}
                  className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/40"
                  onClick={() => { setSelected(s); setShowModal(true); }}
                  title="Click to open details"
                >
                  <span className="font-mono">{s.ticker}</span>
                  <span>${s.currentPrice.toFixed(2)}</span>
                  <span>RSI {Math.round(s.RSI ?? 50)}</span>
                  <span>Vol {s.averageVolume?.toLocaleString?.() || '-'}</span>
                </div>
              ))}
              {filtered.length > 50 && (
                <div className="text-center py-2 text-gray-500">Showing first 50...</div>
              )}
            </div>
          </div>
        </div>
      </div>
      <StockCardModal isOpen={showModal} onClose={() => setShowModal(false)} stock={selected} aiProvider="gemini" />
    </div>
  );
};

export default ScreenerTestTab;
